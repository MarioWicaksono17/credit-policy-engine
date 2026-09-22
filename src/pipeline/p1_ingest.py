"""Tahap 1: file CSV menjadi tabel bronze.

Memuat SEMUA baris, tapi hanya kolom yang terdaftar di config.yaml.
Isinya tidak diubah -- teks tetap teks, angka tetap angka.
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pandas as pd

from src import db
from src.config import load
from src.preprocess import BRONZE_TEXT_COLUMNS, bronze_columns


def ke_angka(s: pd.Series, nama: str) -> pd.Series:
    """Pastikan kolom berisi angka. Tanda persen dibuang kalau ada.

    Kalau ada isian yang gagal diubah jadi angka, jumlahnya dilaporkan
    -- tidak dibiarkan hilang diam-diam.
    """
    if pd.api.types.is_numeric_dtype(s):
        return s
    hasil = pd.to_numeric(s.astype(str).str.strip().str.rstrip("%"), errors="coerce")
    gagal = int(s.notna().sum() - hasil.notna().sum())
    if gagal:
        print(f"  PERHATIAN: {gagal:,} isian di {nama} bukan angka, dianggap kosong")
    return hasil


def main():
    mulai = time.time()
    cfg = load()
    root = cfg["_root"]
    path = root / cfg["data"]["raw_path"]
    kolom = bronze_columns(cfg)

    print(f"Membaca {path.name} ({len(kolom)} dari 151 kolom) ...")
    teks = {c: str for c in kolom if c in BRONZE_TEXT_COLUMNS}
    df = pd.read_csv(path, usecols=kolom, dtype=teks, low_memory=False)
    print(f"  {len(df):,} baris, {time.time() - mulai:.0f} detik")

    # Di akhir file ada beberapa baris ringkasan, misalnya
    # "Total amount funded in policy code 1: ...". Itu bukan pinjaman --
    # tidak punya tanggal pencairan -- jadi dibuang.
    sampah = df["issue_d"].isna()
    if sampah.any():
        print(f"  {int(sampah.sum())} baris ringkasan di akhir file dibuang")
        df = df[~sampah]

    for c in kolom:
        if c not in BRONZE_TEXT_COLUMNS:
            df[c] = ke_angka(df[c], c)

    print("Membuat tabel bronze_loans_raw ...")
    db.run_sql_file(root / "sql" / "01_bronze.sql")

    print("Menulis ke database dengan COPY ...")
    db.copy_dataframe(df[kolom], "bronze_loans_raw")

    n = db.row_count("bronze_loans_raw")
    print(f"Selesai. bronze_loans_raw berisi {n:,} baris. "
          f"Total {time.time() - mulai:.0f} detik.")


if __name__ == "__main__":
    main()