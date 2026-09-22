"""Pemilihan fitur.

Dua prinsip:

1. DAFTAR YANG DIIZINKAN, bukan daftar yang dilarang.
   Model hanya melihat kolom yang tercantum di config.yaml. Kolom lain --
   termasuk kolom hasil seperti recoveries dan lgd -- tidak akan pernah
   terlihat, walaupun ada di tabel yang sama.

2. DIPILIH HANYA DARI DATA LATIH.
   Kalau fitur dipilih dengan melihat data validasi atau uji, itu sama
   dengan mengintip soal ujian. Semua fungsi di sini hanya diberi data latih.

Urutan penyaringan dari 67 fitur:
   a. Buang yang Information Value-nya terlalu rendah
   b. Dari setiap pasangan kembar, pertahankan yang IV-nya lebih tinggi
   c. Ambil paling banyak max_features dengan IV tertinggi
   d. Setelah model dilatih, buang yang arah koefisiennya berlawanan
      dengan hubungan aslinya -- lihat sign_flips()
"""
import numpy as np
import pandas as pd

from src.preprocess import model_features

TARGET = "default_flag"
KOSONG = "KOSONG"


# ---------------------------------------------------------------------
# Tipe data dan pemisahan
# ---------------------------------------------------------------------
def prepare(df: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    """Rapikan tipe data setelah dibaca dari PostgreSQL.

    Penanda kekosongan dibaca sebagai True/False -- diubah jadi 1/0 supaya
    bisa dihitung. Kolom kategori dibiarkan sebagai teks biasa.
    """
    df = df.copy()
    for c in df.columns:
        if c.endswith("_missing"):
            df[c] = df[c].astype(int)
    for c in cfg["columns"]["categorical"]:
        df[c] = df[c].astype(object)
    return df


def split_numeric_categorical(features: list, cfg: dict) -> tuple:
    """Pisahkan daftar fitur menjadi (numerik, kategori)."""
    kategori = set(cfg["columns"]["categorical"])
    return ([f for f in features if f not in kategori],
            [f for f in features if f in kategori])


def split_xy(df: pd.DataFrame, features: list) -> tuple:
    """Ambil HANYA kolom yang ada di daftar fitur, beserta targetnya."""
    return df[features], df[TARGET].astype(int)


# ---------------------------------------------------------------------
# Information Value
# ---------------------------------------------------------------------
def information_value(x: pd.Series, y: pd.Series, bins: int = 10,
                      categorical: bool = False) -> float:
    """Seberapa kuat satu variabel memisahkan peminjam lunas dan gagal bayar.

    Caranya:
      1. Bagi peminjam ke beberapa kelompok berdasarkan nilai variabel.
         Angka dibagi jadi kelompok sama besar; kategori dipakai apa adanya.
         Nilai kosong jadi kelompok tersendiri -- kosong juga informasi.
      2. Di setiap kelompok, hitung berapa persen dari seluruh peminjam
         LUNAS yang ada di situ, dan berapa persen dari seluruh yang GAGAL.
      3. Semakin berbeda kedua persentase itu di tiap kelompok, semakin
         kuat variabelnya. IV merangkum perbedaan itu jadi satu angka.

    Patokan: <0,02 tidak berguna | 0,02-0,1 lemah | 0,1-0,3 sedang |
             >0,3 kuat | >0,5 patut dicurigai kebocoran.
    """
    y = np.asarray(y).astype(int)

    if categorical or x.nunique(dropna=True) <= bins:
        kelompok = x.astype(object).where(x.notna(), KOSONG).astype(str)
    else:
        kelompok = pd.qcut(x, q=bins, duplicates="drop").astype(str)
        kelompok = kelompok.where(x.notna(), KOSONG)

    t = pd.DataFrame({"k": kelompok.values, "y": y}).groupby("k")["y"].agg(["size", "sum"])
    gagal = t["sum"]
    lunas = t["size"] - t["sum"]

    # Tambahan 0,5 mencegah pembagian dengan nol pada kelompok yang
    # isinya hanya lunas atau hanya gagal.
    p_lunas = (lunas + 0.5) / (lunas.sum() + 0.5 * len(t))
    p_gagal = (gagal + 0.5) / (gagal.sum() + 0.5 * len(t))

    woe = np.log(p_lunas / p_gagal)
    return float(((p_lunas - p_gagal) * woe).sum())


# ---------------------------------------------------------------------
# Penyaringan
# ---------------------------------------------------------------------
def select_features(train: pd.DataFrame, cfg: dict) -> tuple:
    """Saring 67 fitur menjadi paling banyak max_features.

    Mengembalikan (daftar_terpilih, laporan). Laporan mencatat setiap
    fitur: IV-nya, dipilih atau dibuang, dan alasannya.
    """
    aturan = cfg["feature_selection"]
    semua = model_features(cfg)
    numerik, kategori = split_numeric_categorical(semua, cfg)
    y = train[TARGET]

    # --- a. Information Value setiap fitur
    lap = pd.DataFrame({
        "feature": semua,
        "iv": [information_value(train[f], y, aturan["bins"], f in kategori) for f in semua],
    }).sort_values("iv", ascending=False).reset_index(drop=True)
    lap["status"] = "dibuang"
    lap["reason"] = ""

    rendah = lap["iv"] < aturan["min_iv"]
    lap.loc[rendah, "reason"] = lap.loc[rendah, "iv"].map(
        lambda v: f"IV {v:.3f} di bawah {aturan['min_iv']} -- tidak membedakan")

    curiga = lap.loc[lap["iv"] > aturan["suspicious_iv"], "feature"].tolist()

    # --- b. Pasangan kembar, hanya untuk angka.
    # Kosong diisi median DATA LATIH, hanya untuk menghitung korelasi.
    kandidat_num = [f for f in lap.loc[~rendah, "feature"] if f in numerik]
    X = train[kandidat_num].astype(float)
    korelasi = X.fillna(X.median()).corr().abs()

    dipertahankan = []
    for f in kandidat_num:                                   # sudah urut IV tertinggi
        kembar = [(k, korelasi.loc[f, k]) for k in dipertahankan
                  if korelasi.loc[f, k] > aturan["max_correlation"]]
        if kembar:
            k, r = max(kembar, key=lambda t: t[1])
            lap.loc[lap["feature"] == f, "reason"] = (
                f"kembar dengan {k} (korelasi {r:.2f}), IV lebih rendah")
        else:
            dipertahankan.append(f)

    lolos = dipertahankan + [f for f in lap.loc[~rendah, "feature"] if f in kategori]

    # --- c. Batasi jumlahnya: ambil yang IV-nya tertinggi
    urut = lap[lap["feature"].isin(lolos)]["feature"].tolist()
    terpilih = urut[: aturan["max_features"]]
    for f in urut[aturan["max_features"]:]:
        lap.loc[lap["feature"] == f, "reason"] = (
            f"di luar {aturan['max_features']} fitur dengan IV tertinggi")

    lap.loc[lap["feature"].isin(terpilih), ["status", "reason"]] = ["dipilih", ""]
    return terpilih, lap, curiga


def sign_flips(pipe, train: pd.DataFrame, numeric: list) -> list:
    """Cari fitur yang arah koefisiennya berlawanan dengan hubungan aslinya.

    Contoh: kalau dilihat sendiri, makin tinggi DTI makin sering gagal bayar.
    Tapi di dalam model, koefisien DTI bisa saja keluar negatif -- seolah
    DTI tinggi justru aman. Ini biasanya karena ada variabel lain yang
    sangat mirip, sehingga model membagi pengaruhnya dengan cara aneh.

    Koefisien seperti itu tidak bisa dijelaskan ke komite kredit, dan
    alasan penolakannya jadi tidak masuk akal. Jadi fitur itu dibuang.
    """
    nama = list(pipe[:-1].get_feature_names_out())
    koef = pipe[-1].coef_[0]

    hasil = []
    for f in numeric:
        c = koef[nama.index(f"num__{f}")]
        d = train[[f, TARGET]].dropna()
        arah = d[f].corr(d[TARGET], method="spearman")
        if pd.notna(arah) and abs(arah) > 0.01 and np.sign(c) != np.sign(arah):
            hasil.append({"feature": f, "coef": float(c), "univariate": float(arah)})
    return hasil


def coefficient_table(pipe, iv: dict, categorical: list) -> list:
    """Koefisien model utama dalam bentuk yang bisa dibaca.

    Untuk kategori, setiap nilai punya koefisien sendiri -- misalnya
    purpose_credit_card dan purpose_small_business -- dibandingkan
    terhadap satu nilai acuan yang tidak ditampilkan.
    """
    nama = pipe[:-1].get_feature_names_out()
    koef = pipe[-1].coef_[0]
    baris = []
    for n, c in zip(nama, koef):
        jenis, _, f = n.partition("__")
        dasar = f if jenis == "num" else next(
            (k for k in categorical if f.startswith(k + "_")), f)
        baris.append({
            "feature": f,
            "type": "angka" if jenis == "num" else "kategori",
            "coef": round(float(c), 4),
            "odds_ratio": round(float(np.exp(c)), 3),
            "iv": round(iv.get(dasar, iv.get(f, float("nan"))), 4),
        })
    return sorted(baris, key=lambda b: -abs(b["coef"]))