"""Akses database.

Satu-satunya tempat koneksi PostgreSQL dibuat. Modul lain tidak
pernah menyusun connection string sendiri.
"""
import pandas as pd
from sqlalchemy import create_engine, text

from src.config import db_url

_engine = None


def get_engine():
    """Kembalikan engine SQLAlchemy, dibuat sekali lalu dipakai ulang."""
    global _engine
    if _engine is None:
        _engine = create_engine(db_url(), future=True)
    return _engine


def truncate(table: str) -> None:
    """Kosongkan tabel dan reset penomoran id.

    Dipanggil sebelum menulis, supaya pipeline bisa dijalankan
    berulang kali dengan hasil yang sama.
    """
    with get_engine().begin() as conn:
        conn.execute(text(f"TRUNCATE TABLE {table} RESTART IDENTITY"))


def write_table(df: pd.DataFrame, table: str) -> None:
    """Tulis DataFrame ke tabel yang sudah ada.

    chunksize dihitung dari jumlah kolom karena PostgreSQL membatasi
    65.535 parameter per perintah. Tanpa ini, INSERT akan gagal
    pada data besar.
    """
    chunk = max(1, 60000 // max(1, len(df.columns)))
    df.to_sql(
        table,
        get_engine(),
        if_exists="append",
        index=False,
        chunksize=chunk,
        method="multi",
    )


def read_table(table: str) -> pd.DataFrame:
    """Baca seluruh isi tabel sebagai DataFrame."""
    return pd.read_sql(f"SELECT * FROM {table}", get_engine())


def row_count(table: str) -> int:
    """Hitung jumlah baris dalam tabel."""
    with get_engine().connect() as conn:
        return conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()