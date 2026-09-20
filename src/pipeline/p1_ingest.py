"""Tahap 1: CSV mentah menjadi tabel bronze.

Tanpa transformasi apa pun. Tujuannya hanya memindahkan data ke
database agar tahap berikutnya tidak perlu membaca CSV lagi.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pandas as pd

from src import db
from src.config import load


def main():
    cfg = load()
    path = cfg["_root"] / cfg["data"]["raw_path"]

    print(f"Membaca {path.name} ...")
    raw = pd.read_csv(path)
    print(f"  {raw.shape[0]:,} baris, {raw.shape[1]} kolom")

    print("Mengosongkan bronze_loans_raw ...")
    db.truncate("bronze_loans_raw")

    print("Menulis ke bronze_loans_raw ...")
    db.write_table(raw, "bronze_loans_raw")

    n = db.row_count("bronze_loans_raw")
    print(f"Selesai. bronze_loans_raw berisi {n:,} baris.")


if __name__ == "__main__":
    main()