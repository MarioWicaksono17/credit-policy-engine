"""Pembagian data.

Validasi utama adalah out-of-time: model dilatih pada tahun lama dan
diuji pada tahun yang lebih baru. Model kredit dipakai untuk menilai
pemohon di masa depan, jadi validasinya harus mencerminkan itu.

Pembagian acak tetap dihitung, hanya sebagai pembanding. Selisih
keduanya sendiri merupakan temuan: kalau hasil di tahun baru jauh
lebih buruk, model bergantung pada pola yang tidak bertahan lintas waktu.
"""
import pandas as pd
from sklearn.model_selection import train_test_split

TARGET = "default_flag"


def split_by_year(df: pd.DataFrame, cfg: dict) -> dict:
    """Bagi data menjadi latih, validasi, dan uji sesuai tahun di config.

    train     tahun latih        -- melatih model dan memilih fitur
    oot_val   tahun validasi     -- memilih model dan garis batas
    oot_test  tahun uji          -- menilai hasil akhir, disentuh sekali
    """
    s = cfg["split"]
    kolom = s["time_column"]

    bagian = {
        "train": df[df[kolom].isin(s["train_years"])],
        "oot_val": df[df[kolom].isin(s["validation_years"])],
        "oot_test": df[df[kolom].isin(s["test_years"])],
    }

    tahun = s["train_years"] + s["validation_years"] + s["test_years"]
    if len(tahun) != len(set(tahun)):
        raise ValueError(f"Ada tahun yang dipakai di lebih dari satu bagian: {tahun}")

    for nama, isi in bagian.items():
        if len(isi) == 0:
            raise ValueError(f"Bagian '{nama}' kosong. Periksa tahun di config.yaml.")

    return {k: v.reset_index(drop=True) for k, v in bagian.items()}


def split_random(df: pd.DataFrame, cfg: dict) -> dict:
    """Pembagian acak 80/20 dari seluruh tahun -- hanya sebagai pembanding."""
    latih, uji = train_test_split(
        df, test_size=0.2, random_state=cfg["seed"], stratify=df[TARGET]
    )
    return {"random_train": latih.reset_index(drop=True),
            "random_test": uji.reset_index(drop=True)}