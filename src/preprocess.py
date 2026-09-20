"""Pembersihan data: bronze menjadi silver.

Aturan pemisahan yang harus dipegang:

  BOLEH di sini  - hal yang tidak bergantung pada data lain.
                   Mengubah "60 months" menjadi 60, menandai nilai
                   sentinel, membuat kolom target.

  TIDAK BOLEH    - hal yang menghitung sesuatu dari sekumpulan data.
                   Imputasi median dan penskalaan HARUS berada di
                   dalam Pipeline scikit-learn, supaya nilainya
                   hanya dihitung dari data latih.

Karena penyebab kebocoran data: median dihitungdari seluruh dataset, 
sehingga informasi dari data uji ikut masuk ke proses pelatihan.
"""
import numpy as np
import pandas as pd

EMP_LENGTH_MAP = {
    "< 1 year": 0.5, "1 year": 1, "2 years": 2, "3 years": 3,
    "4 years": 4, "5 years": 5, "6 years": 6, "7 years": 7,
    "8 years": 8, "9 years": 9, "10+ years": 10,
}

# Kategori kepemilikan rumah yang sangat jarang muncul. Dibiarkan
# terpisah, kategori ini berisiko hanya muncul di data latih dan
# tidak di data uji, sehingga kolom one-hot tidak konsisten.
RARE_HOME_OWNERSHIP = {"ANY", "NONE", "OTHER"}


def parse_term(s: pd.Series) -> pd.Series:
    """' 36 months' menjadi 36."""
    return s.str.extract(r"(\d+)")[0].astype("Int64")


def parse_emp_length(s: pd.Series) -> pd.Series:
    """'10+ years' menjadi 10. Nilai kosong tetap kosong."""
    return s.map(EMP_LENGTH_MAP)


def parse_month_year(s: pd.Series) -> pd.Series:
    """'Jan-2015' menjadi tahun 2015."""
    return pd.to_datetime(s, format="%b-%Y", errors="coerce").dt.year


def apply_sentinels(df: pd.DataFrame, rules: dict) -> pd.DataFrame:
    """Ubah nilai sentinel menjadi kosong.

    Dataset memuat dti bernilai 9999 dan annual_inc bernilai 0.
    Keduanya bukan nilai sebenarnya, melainkan penanda data tidak
    tersedia. Membiarkannya akan merusak koefisien model.
    """
    df = df.copy()
    for col, rule in rules.items():
        if col not in df.columns:
            continue
        if "max_valid" in rule:
            df.loc[df[col] > rule["max_valid"], col] = np.nan
        if "min_valid" in rule:
            df.loc[df[col] < rule["min_valid"], col] = np.nan
    return df


def add_missing_indicators(df: pd.DataFrame, columns: list) -> pd.DataFrame:
    """Tandai baris yang kolomnya kosong, sebelum diisi nanti.

    Kekosongan bisa membawa informasi. mort_acc kosong di 9,5% baris,
    dan ketiadaan catatan KPR kemungkinan menandakan profil kredit
    yang lebih tipis.
    """
    df = df.copy()
    for col in columns:
        if col in df.columns:
            df[f"{col}_missing"] = df[col].isna()
    return df


def make_target(s: pd.Series, default_label: str, non_default_label: str) -> pd.Series:
    """loan_status menjadi default_flag (1 = gagal bayar)."""
    mapping = {default_label: 1, non_default_label: 0}
    return s.map(mapping).astype("Int64")


def clean(raw: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    """Jalankan seluruh pembersihan: bronze menjadi silver."""
    df = raw.copy()

    # 1. Hanya pinjaman yang sudah selesai
    valid = [cfg["data"]["default_label"], cfg["data"]["non_default_label"]]
    df = df[df["loan_status"].isin(valid)].copy()

    # 2. Kolom target
    df["default_flag"] = make_target(
        df["loan_status"],
        cfg["data"]["default_label"],
        cfg["data"]["non_default_label"],
    )

    # 3. Ubah teks menjadi angka
    df["term_months"] = parse_term(df["term"])
    df["emp_length_years"] = parse_emp_length(df["emp_length"])
    df["issue_year"] = parse_month_year(df["issue_d"])
    df["earliest_cr_year"] = parse_month_year(df["earliest_cr_line"])

    # 4. Lama riwayat kredit saat pinjaman dicairkan
    df["credit_history_years"] = df["issue_year"] - df["earliest_cr_year"]

    # 5. Nilai sentinel menjadi kosong
    df = apply_sentinels(df, cfg["features"].get("sentinels", {}))

    # 6. Penanda kekosongan, dibuat SEBELUM pengisian apa pun
    df = add_missing_indicators(df, cfg["features"].get("missing_indicators", []))

    # 7. Kategori langka digabung.
    df["home_ownership"] = df["home_ownership"].where(
        ~df["home_ownership"].isin(RARE_HOME_OWNERSHIP), "OTHER"
    )

    # 8. pub_rec_bankruptcies kosong diisi nol.
    #    Ini pengisian dengan konstanta berdasar penalaran domain --
    #    tidak adanya catatan kebangkrutan berarti nol kebangkrutan --
    #    bukan statistik yang dihitung dari data. Karena itu aman
    #    dilakukan di tahap ini.
    df["pub_rec_bankruptcies"] = df["pub_rec_bankruptcies"].fillna(0)

    # 9. Pilih kolom akhir, sesuai urutan tabel silver
    keep = [
        "loan_amnt", "term_months", "int_rate", "installment", "purpose",
        "annual_inc", "emp_length_years", "home_ownership", "verification_status",
        "dti", "credit_history_years", "open_acc", "total_acc",
        "revol_bal", "revol_util", "pub_rec", "pub_rec_bankruptcies",
        "mort_acc", "mort_acc_missing", "initial_list_status",
        "issue_year", "default_flag",
    ]
    return df[keep].reset_index(drop=True)