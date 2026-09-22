"""Akses database.

Satu-satunya tempat koneksi PostgreSQL dibuat. Modul lain tidak pernah
menyusun connection string atau membuka koneksi sendiri.
"""
import io
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text

from src.config import db_url

_engine = None


def get_engine():
    """Kembalikan engine SQLAlchemy -- dibuat sekali, lalu dipakai ulang."""
    global _engine
    if _engine is None:
        _engine = create_engine(db_url(), future=True)
    return _engine


def run_sql_file(path) -> None:
    """Jalankan seluruh isi file .sql.

    Dipakai pipeline untuk membuat tabelnya sendiri, supaya seluruh
    proses bisa dijalankan dari database kosong tanpa langkah manual.
    """
    sql = Path(path).read_text(encoding="utf-8")
    with get_engine().begin() as conn:
        conn.exec_driver_sql(sql)


def copy_dataframe(df: pd.DataFrame, table: str, chunk_rows: int = 200_000) -> None:
    """Tulis DataFrame ke tabel memakai perintah COPY milik PostgreSQL.

    Kenapa COPY, bukan INSERT: INSERT mengirim data baris demi baris
    sebagai perintah SQL. COPY mengirim data sebagai satu aliran teks
    besar, yang diterima PostgreSQL sekaligus. Untuk jutaan baris,
    perbedaannya bisa puluhan kali lebih cepat.

    Data dikirim per potongan 200 ribu baris supaya memori laptop tidak
    penuh -- mengubah 2 juta baris jadi teks sekaligus butuh banyak RAM.

    Nama kolom disebutkan satu per satu dalam perintah COPY, jadi urutan
    kolom di DataFrame tidak harus sama dengan urutan di tabel.
    """
    kolom = ", ".join(f'"{c}"' for c in df.columns)
    perintah = f"COPY {table} ({kolom}) FROM STDIN WITH (FORMAT csv, NULL '')"

    raw = get_engine().raw_connection()
    try:
        with raw.cursor() as cur:
            for mulai in range(0, len(df), chunk_rows):
                potongan = df.iloc[mulai:mulai + chunk_rows]
                buf = io.StringIO()
                potongan.to_csv(buf, index=False, header=False)
                buf.seek(0)
                cur.copy_expert(perintah, buf)
        raw.commit()
    except Exception:
        raw.rollback()
        raise
    finally:
        raw.close()


def table_columns(table: str) -> list:
    """Daftar kolom sebuah tabel, sesuai urutan di database."""
    sql = text("""
        SELECT column_name FROM information_schema.columns
        WHERE table_name = :t ORDER BY ordinal_position
    """)
    with get_engine().connect() as conn:
        return [r[0] for r in conn.execute(sql, {"t": table})]


def read_query(sql, params: dict = None) -> pd.DataFrame:
    """Jalankan query SELECT dan kembalikan hasilnya sebagai DataFrame."""
    with get_engine().connect() as conn:
        return pd.read_sql(sql, conn, params=params)


def read_table(table: str) -> pd.DataFrame:
    """Baca seluruh isi tabel."""
    return read_query(text(f"SELECT * FROM {table}"))


def row_count(table: str) -> int:
    """Hitung jumlah baris sebuah tabel."""
    with get_engine().connect() as conn:
        return conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()