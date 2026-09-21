"""Tahap 4: pilih garis batas dan hitung dampaknya.

Langkahnya:
  1. Hitung PD tiap pinjaman di data uji
  2. Hitung untung bersih tiap pinjaman kalau lunas
  3. Untuk setiap garis batas 5%-60%, hitung untung dan risikonya
  4. Pilih garis paling untung yang tidak melanggar batas risiko

Semua memakai data uji out-of-time -- data yang belum pernah dilihat
model. Hasilnya tersimpan di artifacts/policy.json.
"""
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import joblib

from src import db
from src.config import load
from src.features import prepare, split_xy
from src.policy import choose_cutoff, lgd_sensitivity, net_interest, sweep
from src.split import split_out_of_time


def juta(x):
    """Format angka dolar menjadi juta, supaya mudah dibaca."""
    return f"${x / 1e6:,.1f} jt"


def main():
    cfg = load()
    root = cfg["_root"]
    batas_risiko = cfg["policy"]["risk_appetite"]["max_portfolio_default_rate"]

    # --- 1. ambil model dan data uji ---
    model = joblib.load(root / "artifacts" / "model.pkl")
    meta = json.loads((root / "artifacts" / "feature_meta.json").read_text(encoding="utf-8"))

    print("Membaca data ...")
    df = prepare(db.read_table("silver_loans_clean"))
    test = split_out_of_time(df, cfg)["oot_test"]
    print(f"  data uji: {len(test):,} pinjaman")

    X, y = split_xy(test, meta["numeric"], meta["categorical"])
    pd_scores = model.predict_proba(X)[:, 1]
    ead = test["loan_amnt"].astype(float)

    # --- 2. untung bersih tiap pinjaman kalau lunas ---
    # Suku bunga BOLEH dipakai di sini: ini menghitung hasil setelah
    # pinjaman berjalan, bukan membantu model memutuskan.
    revenue = net_interest(
        test["installment"], test["term_months"], test["loan_amnt"],
        cfg["policy"]["net_margin"],
    )

    # --- 3. dampak setiap garis batas ---
    print("Menghitung setiap garis batas ...")
    tabel = sweep(pd_scores, y, ead, revenue, cfg)

    # --- 4. pilih garis ---
    pilihan = choose_cutoff(tabel, batas_risiko)
    puncak, terpilih = pilihan["puncak"], pilihan["terpilih"]

    sensitivitas = lgd_sensitivity(pd_scores, y, ead, revenue, terpilih["cutoff"], cfg)

    # --- simpan ---
    (root / "artifacts" / "policy.json").write_text(
        json.dumps({
            "model_version": cfg["model_version"],
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "evaluated_on": "oot_test",
            "n_total": len(test),
            "assumptions": {
                "lgd": cfg["policy"]["lgd_assumption"],
                "net_margin": cfg["policy"]["net_margin"],
                "max_portfolio_default_rate": batas_risiko,
            },
            "economic_optimum": puncak,
            "chosen": terpilih,
            "scenario": pilihan["skenario"],
            "sweep": tabel,
            "lgd_sensitivity": sensitivitas,
        }, indent=2),
        encoding="utf-8",
    )

    # --- tampilkan ---
    print(f"\n{'garis':>6} {'disetujui':>10} {'default':>9} {'uang masuk':>13} "
          f"{'uang keluar':>13} {'untung bersih':>14}  {'aman?':>6}")
    for r in tabel:
        if round(r["cutoff"], 2) in (0.10, 0.12, 0.14, 0.16, 0.18, 0.20,
                                     0.25, 0.30, 0.35, 0.40, 0.50):
            aman = "ya" if r["default_rate"] and r["default_rate"] <= batas_risiko else "tidak"
            print(f"{r['cutoff']:>6.0%} {r['approval_rate']:>10.1%} {r['default_rate']:>9.1%} "
                  f"{juta(r['income']):>13} {juta(r['realized_loss']):>13} "
                  f"{juta(r['net_profit']):>14}  {aman:>6}")

    print("\n" + "=" * 60)
    print(f"Puncak untung   : garis {puncak['cutoff']:.0%}"
          f"   untung {juta(puncak['net_profit'])}"
          f"   default {puncak['default_rate']:.1%}")
    print(f"Batas risiko    : default rate maksimal {batas_risiko:.0%}")
    print(f"GARIS TERPILIH  : garis {terpilih['cutoff']:.0%}"
          f"   untung {juta(terpilih['net_profit'])}"
          f"   default {terpilih['default_rate']:.1%}")
    print("=" * 60)

    if pilihan["skenario"] == 1:
        print("\nKEMUNGKINAN 1 -- batas risiko yang menentukan.")
        print("Garis paling untung melanggar batas risiko, jadi dipilih")
        print("garis paling untung yang masih aman.")
        selisih = puncak["net_profit"] - terpilih["net_profit"]
        print(f"Harga dari kehati-hatian ini: {juta(selisih)} untung yang dilepas.")
    else:
        print("\nKEMUNGKINAN 2 -- untung yang menentukan.")
        print("Garis paling untung sudah aman, jadi itulah yang dipakai.")

    print(f"\nPada garis terpilih:")
    print(f"  Disetujui              {terpilih['n_approved']:>8,}  ({terpilih['approval_rate']:.1%})")
    print(f"  Disetujui, lunas       {terpilih['approved_good']:>8,}")
    print(f"  Disetujui, gagal bayar {terpilih['approved_bad']:>8,}")
    print(f"  Ditolak, akan lunas    {terpilih['rejected_good']:>8,}   <- biaya tersembunyi")
    print(f"  Ditolak, memang gagal  {terpilih['rejected_bad']:>8,}")

    print(f"\nKalau asumsi LGD diganti (pada garis {terpilih['cutoff']:.0%}):")
    for r in sensitivitas:
        print(f"  LGD {r['lgd']:.0%}  ->  untung bersih {juta(r['net_profit'])}")

    print(f"\nTersimpan di artifacts/policy.json")


if __name__ == "__main__":
    main()