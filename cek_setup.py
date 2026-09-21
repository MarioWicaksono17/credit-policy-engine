"""Cek apakah Langkah 0 sudah benar. Jalankan dengan tombol Run di VS Code."""
import pandas as pd
from src.config import load, db_url
from sqlalchemy import create_engine, text

print("=" * 50)

cfg = load()
print("Project      :", cfg["project"])
print("Batas risiko :", cfg["policy"]["risk_appetite"]["max_portfolio_default_rate"])
print("LGD          :", cfg["policy"]["lgd_assumption"])
print("Dikeluarkan  :", cfg["features"]["application_only"]["exclude"])
print("Split        : latih <=", cfg["split"]["train_max_year"],
      "| uji >=", cfg["split"]["test_min_year"])

print("-" * 50)

df = pd.read_csv(cfg["data"]["raw_path"])
print("Ukuran data  :", df.shape)
print(df["loan_status"].value_counts())

print("-" * 50)

engine = create_engine(db_url())
with engine.connect() as conn:
    v = conn.execute(text("SELECT version()")).scalar()
print("Database OK  :", v.split(",")[0])

print("=" * 50)
print("Langkah 0 selesai.")