"""Pembagian data.

Validasi utama adalah out-of-time: model dilatih pada vintage lama
dan diuji pada vintage baru. Alasannya bukan formalitas -- model
kredit dipakai untuk memutuskan aplikasi di masa depan, jadi
validasinya harus mencerminkan itu.

Pembagian acak tetap dihitung sebagai pembanding. Selisih keduanya
sendiri merupakan temuan: kalau performa turun jauh saat diuji
out-of-time, artinya model bergantung pada pola yang tidak bertahan
lintas waktu.
"""
import pandas as pd
from sklearn.model_selection import train_test_split


def split_out_of_time(df: pd.DataFrame, cfg: dict) -> dict:
    """Bagi berdasarkan tahun pencairan.

    train    : vintage <= train_max_year
    oot_val  : vintage == validation_year   (untuk memilih model)
    oot_test : vintage >= test_min_year     (angka final, disentuh sekali)
    """
    s = cfg["split"]
    col = s["time_column"]

    parts = {
        "train": df[df[col] <= s["train_max_year"]],
        "oot_val": df[df[col] == s["validation_year"]],
        "oot_test": df[df[col] >= s["test_min_year"]],
    }

    total = sum(len(p) for p in parts.values())
    if total != len(df):
        raise ValueError(
            f"Pembagian tidak menutup seluruh data: {total:,} dari {len(df):,}. "
            f"Periksa apakah ada vintage di antara {s['validation_year']} "
            f"dan {s['test_min_year']}."
        )

    return {k: v.reset_index(drop=True) for k, v in parts.items()}


def split_random(df: pd.DataFrame, cfg: dict, target: str = "default_flag") -> dict:
    """Pembagian acak 80/20, hanya sebagai pembanding."""
    train, test = train_test_split(
        df,
        test_size=0.2,
        random_state=cfg["seed"],
        stratify=df[target],
    )
    return {
        "random_train": train.reset_index(drop=True),
        "random_test": test.reset_index(drop=True),
    }