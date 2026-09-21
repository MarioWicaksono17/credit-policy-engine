"""Tahap 4: pilih garis batas dan nilai dampaknya.

Dua data dipakai untuk dua tugas berbeda:
  oot_val  (2014)   -- untuk MEMILIH garis batas
  oot_test (2015+)  -- untuk MENILAI garis yang sudah dipilih

Kenapa dipisah: kalau garis dipilih dan dinilai di data yang sama,
hasilnya pasti terlihat bagus -- seperti membuat soal ujian sendiri
lalu mengerjakannya. Data uji harus tetap belum tersentuh sampai
keputusan selesai diambil.
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
from src.policy import (choose_cutoff, evaluate_cutoff, lgd_sensitivity,
                        net_interest, sweep)
from src.split import split_out_of_time


def juta(x):
    """Format angka dolar menjadi juta supaya mudah dibaca."""
    return f"${x / 1e6:,.1f} jt"


def main():
    cfg = load()
    root = cfg["_root"]
    batas_risiko = cfg["policy"]["risk_appetite"]["max_portfolio_default_rate"]
    lgd = cfg["policy"]["lgd_assumption"]

    # --- ambil model ---
    model = joblib.load(root / "artifacts" / "model.pkl")
    meta = json.loads((root / "artifacts" / "feature_meta.json").read_text(encoding="utf-8"))

    def hitung(frame):
        """Hitung PD, kejadian nyata, besar pinjaman, dan pendapatan."""
        X, y = split_xy(frame, meta["numeric"], meta["categorical"])
        pd_scores = model.predict_proba(X)[:, 1]
        ead = frame["loan_amnt"].astype(float)
        revenue = net_interest(frame["installment"], frame["term_months"],
                               frame["loan_amnt"], cfg["policy"]["net_margin"])
        return pd_scores, y, ead, revenue

    print("Membaca data ...")
    df = prepare(db.read_table("silver_loans_clean"))
    bagian = split_out_of_time(df, cfg)
    val, test = bagian["oot_val"], bagian["oot_test"]
    print(f"  validasi (2014) : {len(val):,} pinjaman")
    print(f"  uji (2015+)     : {len(test):,} pinjaman")

    # ============================================================
    # 1. PILIH garis batas -- hanya memakai data validasi
    # ============================================================
    print("\nMemilih garis batas di data validasi ...")
    p_val, y_val, ead_val, rev_val = hitung(val)
    tabel_val = sweep(p_val, y_val, ead_val, rev_val, cfg)
    pilihan = choose_cutoff(tabel_val, batas_risiko)
    garis = pilihan["terpilih"]["cutoff"]

    # ============================================================
    # 2. NILAI garis itu -- di data uji yang belum tersentuh
    # ============================================================
    print("Menilai garis terpilih di data uji ...")
    p_test, y_test, ead_test, rev_test = hitung(test)
    tabel_test = sweep(p_test, y_test, ead_test, rev_test, cfg)
    hasil_uji = evaluate_cutoff(p_test, y_test, ead_test, rev_test, garis, lgd)
    masih_aman = hasil_uji["default_rate"] <= batas_risiko

    sensitivitas = lgd_sensitivity(p_test, y_test, ead_test, rev_test, garis, cfg)

    # --- simpan ---
    (root / "artifacts" / "policy.json").write_text(
        json.dumps({
            "model_version": cfg["model_version"],
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "chosen_on": "oot_val",
            "evaluated_on": "oot_test",
            "n_total": len(test),
            "assumptions": {
                "lgd": lgd,
                "net_margin": cfg["policy"]["net_margin"],
                "max_portfolio_default_rate": batas_risiko,
            },
            "chosen_cutoff": garis,
            "scenario": pilihan["skenario"],
            "selection": {
                "economic_optimum": pilihan["puncak"],
                "chosen": pilihan["terpilih"],
            },
            "active": hasil_uji,
            "holds_on_test": masih_aman,
            "sweep": tabel_test,
            "lgd_sensitivity": sensitivitas,
        }, indent=2),
        encoding="utf-8",
    )

    # --- tampilkan ---
    puncak, terpilih = pilihan["puncak"], pilihan["terpilih"]

    print("\n" + "=" * 62)
    print("DIPILIH DI DATA VALIDASI (2014)")
    print(f"  Puncak untung   : garis {puncak['cutoff']:.0%}"
          f"   kontribusi {juta(puncak['net_profit'])}"
          f"   default {puncak['default_rate']:.1%}")
    print(f"  Batas risiko    : default rate maksimal {batas_risiko:.0%}")
    print(f"  Garis terpilih  : garis {terpilih['cutoff']:.0%}"
          f"   kontribusi {juta(terpilih['net_profit'])}"
          f"   default {terpilih['default_rate']:.1%}")
    print(f"  Skenario        : KEMUNGKINAN {pilihan['skenario']}")

    print("\nDINILAI DI DATA UJI (2015+) -- belum pernah dilihat")
    print(f"  Garis {garis:.0%}")
    print(f"  Disetujui              {hasil_uji['n_approved']:>8,}  ({hasil_uji['approval_rate']:.1%})")
    print(f"  Default rate           {hasil_uji['default_rate']:>8.1%}")
    print(f"  Kontribusi kredit      {juta(hasil_uji['net_profit']):>12}")
    print(f"  Masih di bawah {batas_risiko:.0%}?     {'YA' if masih_aman else 'TIDAK'}")
    print("=" * 62)

    if not masih_aman:
        print("\nPERHATIAN: kebijakan yang dirancang di data 2014 tidak lagi")
        print("memenuhi batas risiko di data 2015+. Populasi peminjam")
        print("bergeser, dan kebijakan perlu ditinjau ulang.")

    print(f"\nEmpat kotak hasil di data uji:")
    print(f"  Disetujui, lunas       {hasil_uji['approved_good']:>8,}")
    print(f"  Disetujui, gagal bayar {hasil_uji['approved_bad']:>8,}")
    print(f"  Ditolak, akan lunas    {hasil_uji['rejected_good']:>8,}   <- biaya tersembunyi")
    print(f"  Ditolak, memang gagal  {hasil_uji['rejected_bad']:>8,}")
    print(f"  {hasil_uji['good_rejected_per_bad_avoided']} pemohon baik ditolak"
          f" untuk setiap 1 gagal bayar yang dihindari")

    print(f"\nKalau asumsi LGD diganti (garis {garis:.0%}, data uji):")
    for r in sensitivitas:
        print(f"  LGD {r['lgd']:.0%}  ->  kontribusi {juta(r['net_profit'])}")

    print(f"\nTersimpan di artifacts/policy.json")


if __name__ == "__main__":
    main()