"""Pembersihan data: bronze menjadi silver.

Pembagian kerja:

  Penyaringan  -- memilih pinjaman mana yang masuk -- dilakukan di
                  DATABASE dengan SQL, lewat scope_query(). Hanya sekitar
                  seperempat baris bronze yang lolos, jadi lebih efisien
                  menyaring sebelum data dikirim ke Python.

  Pembersihan  -- mengubah isi kolom -- dilakukan di PYTHON, lewat clean().

Aturan yang harus dipegang di sini:

  BOLEH    Mengubah bentuk satu baris tanpa melihat baris lain.
           Contoh: "10+ years" jadi 10, dti 999 jadi kosong.

  DILARANG Menghitung sesuatu dari sekumpulan baris, misalnya median.
           Itu harus di dalam Pipeline model, supaya hanya dihitung dari
           data latih. Kalau dilakukan di sini, informasi dari data uji
           ikut bocor ke proses pelatihan.
"""
import numpy as np
import pandas as pd
from sqlalchemy import bindparam, text

from src.config import all_features

EMP_LENGTH_MAP = {
    "< 1 year": 0.5, "1 year": 1, "2 years": 2, "3 years": 3, "4 years": 4,
    "5 years": 5, "6 years": 6, "7 years": 7, "8 years": 8, "9 years": 9,
    "10+ years": 10,
}

# Kategori tempat tinggal yang sangat jarang. Dibiarkan terpisah, kategori
# ini bisa muncul di data uji tapi tidak di data latih.
RARE_HOME_OWNERSHIP = {"ANY", "NONE", "OTHER"}

# Kolom yang di bronze disimpan sebagai TEKS, apa adanya dari CSV.
# Kolom lain disimpan sebagai angka.
BRONZE_TEXT_COLUMNS = {
    "id", "issue_d", "term", "emp_length", "home_ownership",
    "verification_status", "purpose", "earliest_cr_line", "application_type",
    "loan_status", "last_pymnt_d", "grade", "sub_grade",
}

# Kolom hasil yang disimpan di silver, beserta turunannya.
# Semuanya DILARANG menjadi fitur -- dijaga oleh src/config.py.
OUTCOME_COLUMNS = [
    "default_flag",             # target: 1 gagal bayar, 0 lunas
    "funded_amnt",
    "total_rec_prncp",
    "recoveries",
    "collection_recovery_fee",
    "total_pymnt",
    "total_rec_int",
    "ead",                      # sisa pinjaman saat gagal bayar
    "lgd",                      # porsi yang hilang dari EAD
    "net_cash",                 # untung atau rugi per pinjaman
]


# ---------------------------------------------------------------------
# Nama-nama kolom
# ---------------------------------------------------------------------
def model_features(cfg: dict) -> list:
    """Nama fitur SETELAH dibersihkan -- inilah yang dilihat model.

    Tiga kolom mentah berubah bentuk:
      fico_range_low + fico_range_high  ->  fico_score
      earliest_cr_line                  ->  credit_history_years
    Ditambah satu penanda untuk setiap kolom di missing_indicators.
    """
    hasil = []
    for c in all_features(cfg):
        if c == "fico_range_low":
            hasil.append("fico_score")
        elif c == "fico_range_high":
            continue
        elif c == "earliest_cr_line":
            hasil.append("credit_history_years")
        else:
            hasil.append(c)

    hasil += [f"{c}_missing" for c in cfg["cleaning"]["missing_indicators"]]
    return hasil


def silver_columns(cfg: dict) -> list:
    """Urutan lengkap kolom tabel silver."""
    return (["loan_id", "issue_year"]
            + model_features(cfg)
            + cfg["columns"]["benchmark"]
            + OUTCOME_COLUMNS)


def bronze_columns(cfg: dict) -> list:
    """Kolom yang dibaca dari CSV dan disimpan di bronze."""
    c = cfg["columns"]
    return ([c["id"], c["time"]] + all_features(cfg)
            + c["benchmark"] + c["outcome"] + c["filter_columns"])


# ---------------------------------------------------------------------
# Penyaringan -- di database
# ---------------------------------------------------------------------
def scope_query(cfg: dict):
    """Query SQL untuk mengambil hanya pinjaman yang masuk cakupan.

    Menerapkan ketiga penyaring dari config, ditambah tahun yang dipakai.
    Nilai-nilainya dikirim sebagai parameter, bukan ditempel ke teks SQL.
    """
    f, s, d = cfg["filters"], cfg["split"], cfg["data"]
    tahun = s["train_years"] + s["validation_years"] + s["test_years"]

    syarat = [
        "application_type = :app",
        "TRIM(term) = :term",
        "CAST(RIGHT(issue_d, 4) AS INTEGER) IN :tahun",
    ]
    params = {
        "app": f["application_type"],
        "term": f"{f['term_months']} months",
        "tahun": tahun,
    }
    kunci_list = ["tahun"]

    if f.get("completed_only", True):
        syarat.append("loan_status IN :status")
        params["status"] = d["default_labels"] + d["non_default_labels"]
        kunci_list.append("status")

    sql = text("SELECT * FROM bronze_loans_raw WHERE " + " AND ".join(syarat))
    sql = sql.bindparams(*[bindparam(k, expanding=True) for k in kunci_list])
    return sql, params


# ---------------------------------------------------------------------
# Pembersihan -- di Python
# ---------------------------------------------------------------------
def _bulan_tahun(s: pd.Series) -> pd.Series:
    """'Dec-2015' menjadi tanggal."""
    return pd.to_datetime(s, format="%b-%Y", errors="coerce")


def clean(raw: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    """Ubah baris bronze yang sudah disaring menjadi baris silver."""
    df = raw.copy()
    d = cfg["data"]

    # --- 0. Pemeriksaan: penyaringan di database harus sudah berjalan
    semua_status = set(d["default_labels"]) | set(d["non_default_labels"])
    if not df["loan_status"].isin(semua_status).all():
        raise ValueError("Ada pinjaman yang belum selesai lolos penyaringan.")

    # --- 1. Pengenal dan waktu
    df["loan_id"] = df["id"].astype(str)
    tanggal = _bulan_tahun(df["issue_d"])
    df["issue_year"] = tanggal.dt.year.astype(int)

    # --- 2. Target
    df["default_flag"] = df["loan_status"].isin(d["default_labels"]).astype(int)

    # --- 3. Ubah teks menjadi angka
    df["emp_length"] = df["emp_length"].map(EMP_LENGTH_MAP)

    # --- 4. Kolom turunan
    # Lama riwayat kredit saat pengajuan, dalam tahun
    awal = _bulan_tahun(df["earliest_cr_line"])
    df["credit_history_years"] = (
        (tanggal.dt.year - awal.dt.year) * 12 + (tanggal.dt.month - awal.dt.month)
    ) / 12

    # Batas bawah dan atas FICO selalu berselisih 4 poin. Memakai keduanya
    # sebagai fitur berarti memasukkan informasi yang sama dua kali.
    df["fico_score"] = (df["fico_range_low"] + df["fico_range_high"]) / 2

    # --- 5. Kategori langka digabung
    df["home_ownership"] = df["home_ownership"].where(
        ~df["home_ownership"].isin(RARE_HOME_OWNERSHIP), "OTHER"
    )

    # --- 6. Nilai sentinel menjadi kosong
    for kolom, aturan in cfg["cleaning"]["sentinels"].items():
        if "min_valid" in aturan:
            df.loc[df[kolom] < aturan["min_valid"], kolom] = np.nan
        if "max_valid" in aturan:
            df.loc[df[kolom] > aturan["max_valid"], kolom] = np.nan

    # --- 7. Penanda kekosongan -- SETELAH sentinel, SEBELUM pengisian apa pun
    for kolom in cfg["cleaning"]["missing_indicators"]:
        df[f"{kolom}_missing"] = df[kolom].isna()

    # --- 8. Hasil: EAD, LGD, dan untung
    gagal = df["default_flag"] == 1

    # EAD: uang yang masih di tangan peminjam saat berhenti membayar.
    # Hanya bermakna untuk yang gagal bayar.
    df["ead"] = np.where(gagal, df["funded_amnt"] - df["total_rec_prncp"], np.nan)

    # LGD: dari EAD itu, berapa persen yang benar-benar hilang
    # setelah penagihan dikurangi biayanya.
    pulih = df["recoveries"] - df["collection_recovery_fee"]
    ada_ead = gagal & (df["ead"] > 0)
    df["lgd"] = np.where(ada_ead, (1 - pulih / df["ead"]).clip(0, 1), np.nan)

    # Untung atau rugi: uang yang kembali dikurangi uang yang keluar.
    # total_pymnt sudah termasuk recoveries -- terbukti dari data.
    df["net_cash"] = df["total_pymnt"] - df["collection_recovery_fee"] - df["funded_amnt"]

    return df[silver_columns(cfg)].reset_index(drop=True)