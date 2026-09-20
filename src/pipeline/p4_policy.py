"""Tahap 4: hitung dampak setiap garis batas.

Menghasilkan artifacts/policy.json, yang isinya:
  - tabel dampak untuk seluruh garis batas dari 5% sampai 60%
  - dampak pada garis batas yang berlaku sekarang
  - uji sensitivitas asumsi LGD

Seluruh perhitungan memakai holdout out-of-time -- data yang belum
pernah dilihat model. Inilah perbaikan dari project sebelumnya, yang
menghitung dampak kebijakan pada data yang sebagian dipakai melatih.
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
from src.policy import evaluate_cutoff, lgd_sensitivity, sweep
from src.split import split_out_of_time


def main():
    cfg = load()
    root = cfg["_root"]
    cutoff = cfg["policy"]["cutoff"]
    lgd = cfg["policy"]["lgd_assumption"]

    # --- ambil model dan daftar fitur yang dipakai ---
    model = joblib.load(root / "artifacts" / "model.pkl")
    meta = json.loads((root / "artifacts" / "feature_meta.json").read_text(encoding="utf-8"))

    print("Membaca silver_loans_clean ...")
    df = prepare(db.read_table("silver_loans_clean"))

    # Hanya data uji yang dipakai. Menghitung dampak kebijakan pada
    # data latih akan membuat angkanya terlalu bagus.
    test = split_out_of_time(df, cfg)["oot_test"]
    print(f"  holdout out-of-time: {len(test):,} pinjaman")

    # --- hitung PD tiap pinjaman ---
    X, y = split_xy(test, meta["numeric"], meta["categorical"])
    pd_scores = model.predict_proba(X)[:, 1]
    ead = test["loan_amnt"].astype(float)

    print(f"  rata-rata PD {pd_scores.mean():.4f}  realisasi {y.mean():.4f}")

    # --- hitung semuanya ---
    print(f"\nMenghitung dampak untuk setiap garis batas ...")
    tabel = sweep(pd_scores, y, ead, cfg)

    print(f"Menghitung dampak garis batas berlaku ({cutoff:.0%}) ...")
    berlaku = evaluate_cutoff(pd_scores, y, ead, cutoff, lgd)

    print(f"Menguji sensitivitas asumsi LGD ...")
    sensitivitas = lgd_sensitivity(pd_scores, y, ead, cfg)

    # --- simpan ---
    (root / "artifacts" / "policy.json").write_text(
        json.dumps({
            "model_version": cfg["model_version"],
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "evaluated_on": "oot_test",
            "n_total": len(test),
            "lgd_assumption": lgd,
            "active_cutoff": cutoff,
            "active": berlaku,
            "sweep": tabel,
            "lgd_sensitivity": sensitivitas,
        }, indent=2),
        encoding="utf-8",
    )

    # --- tampilkan ringkasan ---
    print(f"\nPada garis batas {cutoff:.0%}:")
    print(f"  Disetujui              {berlaku['n_approved']:>8,}"
          f"  ({berlaku['approval_rate']:.1%})")
    print(f"  Exposure               ${berlaku['exposure']/1e6:>7,.0f} jt")
    print(f"  Default rate disetujui {berlaku['default_rate']:>8.1%}"
          f"  (populasi penuh {y.mean():.1%})")
    print(f"  Expected loss          ${berlaku['expected_loss']/1e6:>7,.0f} jt"
          f"  ({berlaku['el_pct_exposure']:.1%} dari exposure)")

    print(f"\nEmpat kotak hasil:")
    print(f"  Disetujui, lunas       {berlaku['approved_good']:>8,}")
    print(f"  Disetujui, gagal bayar {berlaku['approved_bad']:>8,}")
    print(f"  Ditolak, akan lunas    {berlaku['rejected_good']:>8,}   <- biaya tersembunyi")
    print(f"  Ditolak, memang gagal  {berlaku['rejected_bad']:>8,}")
    print(f"\n  {berlaku['good_rejected_per_bad_avoided']} pemohon baik ditolak"
          f" untuk setiap 1 gagal bayar yang dihindari")

    print(f"\nBeberapa garis batas lain:")
    print(f"  {'batas':>6} {'disetujui':>10} {'default':>9} {'exp.loss':>11} {'baik ditolak':>13}")
    for r in tabel:
        if round(r["cutoff"], 2) in (0.10, 0.15, 0.20, 0.25, 0.30, 0.40, 0.60):
            dr = f"{r['default_rate']:.1%}" if r["default_rate"] else "-"
            print(f"  {r['cutoff']:>6.0%} {r['approval_rate']:>10.1%} {dr:>9}"
                  f" ${r['expected_loss']/1e6:>9,.0f} jt {r['rejected_good']:>13,}")

    print(f"\nSensitivitas asumsi LGD:")
    for r in sensitivitas:
        print(f"  LGD {r['lgd']:.0%}  ->  expected loss ${r['expected_loss']/1e6:>6,.0f} jt"
              f"  ({r['el_pct_exposure']:.1%} dari exposure)")

    print(f"\nTersimpan di artifacts/policy.json")


if __name__ == "__main__":
    main()