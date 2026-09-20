"""Pemuat konfigurasi.

Satu-satunya tempat config.yaml dan .env dibaca. Modul lain
memanggil load() dan tidak pernah membaca file ini langsung.
"""
import os
from functools import lru_cache
from pathlib import Path

import yaml
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]

REQUIRED = ["project", "model_version", "seed", "data",
            "split", "features", "model", "policy"]


@lru_cache(maxsize=1)
def load() -> dict:
    """Baca config.yaml, validasi field wajib, kembalikan sebagai dict."""
    with open(ROOT / "config.yaml", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    missing = [k for k in REQUIRED if k not in cfg]
    if missing:
        raise ValueError(f"config.yaml kehilangan field wajib: {missing}")

    cfg["_root"] = ROOT
    return cfg


def db_url() -> str:
    """Susun connection string PostgreSQL dari .env."""
    load_dotenv(ROOT / ".env")
    user = os.getenv("DB_USER")
    pwd = os.getenv("DB_PASSWORD")
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "5432")
    name = os.getenv("DB_NAME", "credit_policy")

    if not user:
        raise ValueError("DB_USER belum diisi di .env")

    return f"postgresql+psycopg2://{user}:{pwd}@{host}:{port}/{name}"