"""Tahap 2: tabel bronze menjadi tabel silver.

Seluruh logika pembersihan ada di src/preprocess.py. File ini hanya
mengatur alurnya: baca, bersihkan, tulis, laporkan.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src import db
from src.config import load
from src.preprocess import clean


def main():
    cfg = load()

    print("Membaca bronze_loans_raw ...")
    raw = db.read_table("bronze_loans_raw")
    print(f"  {raw.shape[0]:,} baris")

    print("Membersihkan ...")
    silver = clean(raw, cfg)
    print(f"  {silver.shape[0]:,} baris, {silver.shape[1]} kolom")

    print("Mengosongkan silver_loans_clean ...")
    db.truncate("silver_loans_clean")

    print("Menulis ke silver_loans_clean ...")
    db.write_table(silver, "silver_loans_clean")

    n = db.row_count("silver_loans_clean")
    rate = silver["default_flag"].mean()
    print(f"Selesai. silver_loans_clean berisi {n:,} baris.")
    print(f"Base default rate: {rate:.4f}")


if __name__ == "__main__":
    main()