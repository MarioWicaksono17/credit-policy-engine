"""Pemuat konfigurasi.

Satu-satunya tempat config.yaml dan .env dibaca. Modul lain memanggil
load() dan tidak pernah membaca file itu sendiri.

Setiap kali config dimuat, daftar fitur diperiksa: kalau ada kolom HASIL
atau PEMBANDING yang tercampur ke fitur, program langsung berhenti.
Penjagaan ini ada di sini -- bukan di tempat lain -- supaya tidak ada
satu pun bagian program yang bisa berjalan dengan daftar fitur yang bocor.
"""
from functools import lru_cache
from pathlib import Path

import yaml
from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parents[1]

REQUIRED = ["project", "model_version", "seed", "data", "filters", "split",
            "columns", "feature_policy", "cleaning", "feature_selection",
            "model", "policy"]


def all_features(cfg: dict) -> list:
    """Gabungkan tiga kelompok fitur menjadi satu daftar."""
    f = cfg["columns"]["features"]
    return f["application"] + f["credit_history"] + f["bureau_detail"]


def _cek_kebocoran(cfg: dict) -> None:
    """Hentikan program kalau kolom terlarang masuk daftar fitur."""
    fitur = set(all_features(cfg))

    bocor_hasil = fitur & set(cfg["columns"]["outcome"])
    if bocor_hasil:
        raise ValueError(
            f"KEBOCORAN DATA: kolom hasil masuk daftar fitur: {sorted(bocor_hasil)}. "
            f"Kolom ini baru ada setelah pinjaman berjalan."
        )

    bocor_pembanding = fitur & set(cfg["columns"]["benchmark"])
    if bocor_pembanding:
        raise ValueError(
            f"Kolom pembanding masuk daftar fitur: {sorted(bocor_pembanding)}. "
            f"Pakai feature_policy with_pricing_adds untuk pembanding."
        )

    ganda = [x for x in fitur if all_features(cfg).count(x) > 1]
    if ganda:
        raise ValueError(f"Fitur tercantum lebih dari sekali: {sorted(ganda)}")


@lru_cache(maxsize=1)
def load() -> dict:
    """Baca config.yaml, periksa, lalu kembalikan sebagai dictionary."""
    with open(ROOT / "config.yaml", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    kurang = [k for k in REQUIRED if k not in cfg]
    if kurang:
        raise ValueError(f"config.yaml kehilangan bagian wajib: {kurang}")

    _cek_kebocoran(cfg)

    cfg["_root"] = ROOT
    return cfg


def db_url() -> str:
    """Susun connection string PostgreSQL dari file .env.

    Nilai dibaca langsung dari file, tidak lewat variabel lingkungan
    Windows, supaya setelan project lain tidak ikut terbawa.
    """
    env = dotenv_values(ROOT / ".env")

    user = env.get("DB_USER")
    if not user:
        raise ValueError("DB_USER belum diisi di .env")

    pwd = env.get("DB_PASSWORD", "")
    host = env.get("DB_HOST", "localhost")
    port = env.get("DB_PORT", "5432")
    name = env.get("DB_NAME", "credit_policy")

    return f"postgresql+psycopg2://{user}:{pwd}@{host}:{port}/{name}"