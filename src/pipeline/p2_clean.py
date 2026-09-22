"""Tahap 2: tabel bronze menjadi tabel silver.

Penyaringan dilakukan di database dengan SQL, pembersihan di Python.
Seluruh aturannya ada di src/preprocess.py -- file ini hanya mengatur
alurnya, lalu melaporkan hasilnya.
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src import db
from src.config import load
from src.preprocess import clean, scope_query


def main():
    mulai = time.time()
    cfg = load()
    root = cfg["_root"]

    print("Mengambil pinjaman dalam cakupan dari bronze ...")
    sql, params = scope_query(cfg)
    raw = db.read_query(sql, params)
    total = db.row_count("bronze_loans_raw")
    print(f"  {len(raw):,} dari {total:,} baris lolos penyaringan")

    print("Membersihkan ...")
    silver = clean(raw, cfg)

    print("Membuat tabel silver_loans_clean ...")
    db.run_sql_file(root / "sql" / "02_silver.sql")

    # Kolom di tabel harus sama persis dengan hasil pembersihan. Kalau
    # daftar fitur di config.yaml diubah, file SQL-nya juga harus diubah.
    di_tabel = db.table_columns("silver_loans_clean")
    if di_tabel != list(silver.columns):
        kurang = set(silver.columns) - set(di_tabel)
        lebih = set(di_tabel) - set(silver.columns)
        raise SystemExit(
            "sql/02_silver.sql tidak cocok dengan config.yaml.\n"
            f"  Ada di hasil, tidak ada di tabel: {sorted(kurang)}\n"
            f"  Ada di tabel, tidak ada di hasil: {sorted(lebih)}"
        )

    print("Menulis ke database dengan COPY ...")
    db.copy_dataframe(silver, "silver_loans_clean")
    n = db.row_count("silver_loans_clean")
    print(f"Selesai. silver_loans_clean berisi {n:,} baris.")

    # --- ringkasan
    s = cfg["split"]
    peran = {y: "latih" for y in s["train_years"]}
    peran |= {y: "validasi" for y in s["validation_years"]}
    peran |= {y: "uji" for y in s["test_years"]}

    print(f"\n{'tahun':>6} {'peran':>9} {'pinjaman':>10} {'default':>8} {'LGD':>6}")
    for tahun, g in silver.groupby("issue_year"):
        print(f"{tahun:>6} {peran.get(tahun, '-'):>9} {len(g):>10,} "
              f"{g['default_flag'].mean():>8.1%} {g['lgd'].mean():>6.3f}")

    print(f"\nKolom           : {silver.shape[1]}")
    print(f"Default rate    : {silver['default_flag'].mean():.2%}")
    print(f"LGD rata-rata   : {silver['lgd'].mean():.3f}")
    print(f"Waktu           : {time.time() - mulai:.0f} detik")


if __name__ == "__main__":
    main()