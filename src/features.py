"""Penentuan variabel yang dipakai model.

Dua kebijakan fitur:

  application_only  Hanya variabel yang tersedia SEBELUM keputusan
                    kredit diambil. Ini model utama.

  with_pricing      Ditambah suku bunga dan angsuran. Hanya sebagai
                    pembanding -- selisih performanya mengukur
                    seberapa besar model bergantung pada keputusan
                    underwriting Lending Club.
"""
import pandas as pd

TARGET = "default_flag"

# Bukan fitur: pengenal baris dan kolom waktu.
# issue_year dipakai untuk membagi data, bukan untuk memprediksi.
NON_FEATURES = ["loan_id", "issue_year", TARGET]

CATEGORICAL = [
    "purpose",
    "home_ownership",
    "verification_status",
    "initial_list_status",
]


def prepare(df: pd.DataFrame) -> pd.DataFrame:
    """Rapikan tipe data setelah dibaca dari PostgreSQL.

    Kolom NUMERIC di PostgreSQL dikembalikan psycopg2 sebagai objek
    Decimal, bukan float. Tanpa konversi ini scikit-learn akan gagal
    dengan pesan yang membingungkan.
    """
    df = df.copy()

    for col in df.columns:
        if col in CATEGORICAL:
            df[col] = df[col].astype("string")
        elif df[col].dtype == "bool":
            df[col] = df[col].astype(int)
        elif df[col].dtype == object:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


def get_features(df: pd.DataFrame, cfg: dict, policy: str = None) -> tuple:
    """Kembalikan (daftar_numerik, daftar_kategorik) untuk satu kebijakan."""
    policy = policy or cfg["features"]["active_policy"]

    if policy not in cfg["features"]:
        raise ValueError(f"Kebijakan fitur '{policy}' tidak ada di config.yaml")

    excluded = set(cfg["features"][policy].get("exclude", []))
    excluded |= set(NON_FEATURES)

    cols = [c for c in df.columns if c not in excluded]
    categorical = [c for c in cols if c in CATEGORICAL]
    numeric = [c for c in cols if c not in CATEGORICAL]

    return numeric, categorical


def split_xy(df: pd.DataFrame, numeric: list, categorical: list) -> tuple:
    """Pisahkan matriks fitur dan vektor target."""
    return df[numeric + categorical], df[TARGET].astype(int)