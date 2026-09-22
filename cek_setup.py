"""Cek apakah persiapan versi 2 sudah benar. Jalankan dengan tombol Run."""
import pandas as pd
from sqlalchemy import create_engine, text

from src.config import all_features, db_url, load

print("=" * 60)

# ---- 1. config
cfg = load()   # sekaligus memeriksa kebocoran fitur
fitur = all_features(cfg)
f = cfg["columns"]["features"]
print("Project        :", cfg["project"], cfg["model_version"])
print("Penyaring      : tenor", cfg["filters"]["term_months"], "bulan,",
      cfg["filters"]["application_type"])
print("Pembagian      : latih", cfg["split"]["train_years"],
      "| validasi", cfg["split"]["validation_years"],
      "| uji", cfg["split"]["test_years"])
print(f"Fitur          : {len(fitur)} "
      f"({len(f['application'])} formulir + {len(f['credit_history'])} riwayat "
      f"+ {len(f['bureau_detail'])} biro)")
print("Batas risiko   :", cfg["policy"]["risk_appetite"]["max_portfolio_default_rate"])
print("Kebocoran      : tidak ada")

# ---- 2. dataset: hanya membaca baris judul, bukan seluruh file
print("-" * 60)
path = cfg["_root"] / cfg["data"]["raw_path"]
if not path.exists():
    raise SystemExit(f"Dataset tidak ditemukan: {path}")

header = set(pd.read_csv(path, nrows=0).columns)
c = cfg["columns"]
dibutuhkan = (fitur + c["benchmark"] + c["outcome"] + c["filter_columns"]
              + [c["id"], c["time"]])
hilang = [x for x in dibutuhkan if x not in header]
if hilang:
    raise SystemExit(f"Kolom tidak ada di dataset: {hilang}")
print(f"Dataset        : {path.name}")
print(f"Kolom          : {len(dibutuhkan)} dibutuhkan, semua ada")

# ---- 3. database
print("-" * 60)
engine = create_engine(db_url())
with engine.connect() as conn:
    nama = conn.execute(text("SELECT current_database()")).scalar()
if nama != "credit_policy":
    raise SystemExit(f"SALAH DATABASE: terhubung ke '{nama}', seharusnya 'credit_policy'")
print("Database       :", nama)

print("=" * 60)
print("Persiapan versi 2 selesai.")