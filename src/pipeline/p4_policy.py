"""Tahap 4: pilih garis batas dan nilai dampaknya.

Dua data untuk dua tugas berbeda:
  oot_val  (2014)  -- untuk MEMILIH garis batas
  oot_test (2015)  -- untuk MENILAI garis yang sudah dipilih

Kalau garis dipilih dan dinilai di data yang sama, hasilnya pasti terlihat
bagus -- seperti membuat soal ujian sendiri lalu mengerjakannya.

LGD dan EAD diperkirakan dari data latih 2013, lalu diterapkan ke depan.
Untung dihitung dari uang yang benar-benar berpindah tangan.
"""
import json
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import warnings

import joblib

from src import db
from src.calibration import apply_offset
from src.config import load
from src.features import prepare, split_xy
from src.policy import (choose_cutoff, evaluate_cutoff, loss_parameters,
                        stress_test, sweep)
from src.split import split_by_year

# Peringatan ini muncul ketika tahun uji punya kategori yang tidak ada di
# tahun latih. Model menanganinya dengan benar, jadi peringatannya hanya
# mengotori layar. Yang diredam HANYA peringatan ini.
warnings.filterwarnings("ignore", message="Found unknown categories",
                        category=UserWarning)


def juta(x):
    """Format angka dolar menjadi juta supaya mudah dibaca."""
    return f"${x / 1e6:,.1f} jt"


def main():
    mulai = time.time()
    cfg = load()
    root = cfg["_root"]
    batas = cfg["policy"]["risk_appetite"]["max_portfolio_default_rate"]

    model = joblib.load(root / "artifacts" / "model.pkl")
    meta = json.loads((root / "artifacts" / "feature_meta.json").read_text(encoding="utf-8"))
    fitur = meta["numeric"] + meta["categorical"]

    print("Membaca data ...")
    df = prepare(db.read_table("silver_loans_clean"), cfg)
    bagian = split_by_year(df, cfg)
    val, uji = bagian["oot_val"], bagian["oot_test"]
    print(f"  validasi {len(val):,} pinjaman | uji {len(uji):,} pinjaman")

    # --- LGD dan EAD dari data latih
    par = loss_parameters(bagian["train"])
    print(f"\nDari {par['n_default']:,} pinjaman gagal bayar di data latih:")
    print(f"  LGD       {par['lgd']:.3f}  (porsi sisa pinjaman yang hilang)")
    print(f"  EAD       {par['ead_ratio']:.3f}  (sisa pinjaman saat gagal bayar)")
    print(f"  Kerugian  {par['lgd'] * par['ead_ratio']:.3f}  dari jumlah yang dipinjamkan")

    # PD dipakai SETELAH dikoreksi. Penggesernya dihitung di p3 dari data
    # validasi 2014. Urutan risikonya tidak berubah -- yang berubah hanya
    # levelnya, sehingga perhitungan uang jadi lebih mendekati kenyataan.
    offset = meta.get("calibration_offset", 0.0)
    if offset:
        print(f"  PD dikoreksi dengan penggeser {offset:+.4f} "
              f"(dihitung dari data {meta.get('calibration_fit_on')})")

    def pd_of(frame):
        X, _ = split_xy(frame, fitur)
        return apply_offset(model.predict_proba(X)[:, 1], offset)

    p_val, p_uji = pd_of(val), pd_of(uji)

    # --- 1. PILIH garis batas, hanya memakai data validasi
    print("\nMemilih garis batas di data validasi 2014 ...")
    tabel_val = sweep(val, p_val, cfg, par)
    pilihan = choose_cutoff(tabel_val, batas)
    garis = pilihan["terpilih"]["cutoff"]

    # --- 2. NILAI garis itu di data uji yang belum tersentuh
    print("Menilai garis terpilih di data uji 2015 ...")
    tabel_uji = sweep(uji, p_uji, cfg, par)
    hasil = evaluate_cutoff(uji, p_uji, garis, par)
    masih_aman = hasil["default_rate"] <= batas

    stres, impas = stress_test(uji, p_uji, garis,
                               cfg["policy"]["stress_multipliers"])

    # --- simpan
    (root / "artifacts" / "policy.json").write_text(json.dumps({
        "model_version": cfg["model_version"],
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "chosen_on": "oot_val", "evaluated_on": "oot_test",
        "n_total": len(uji),
        "loss_parameters": par,
        "calibration_offset": offset,
        "risk_appetite": batas,
        "chosen_cutoff": garis,
        "scenario": pilihan["skenario"],
        "selection": {"economic_optimum": pilihan["puncak"],
                      "chosen": pilihan["terpilih"]},
        "active": hasil,
        "holds_on_test": bool(masih_aman),
        "sweep": tabel_uji,
        "stress_test": {"break_even_multiplier": impas, "table": stres},
    }, indent=2, ensure_ascii=False), encoding="utf-8")

    # --- tampilkan
    puncak, terpilih = pilihan["puncak"], pilihan["terpilih"]

    print(f"\n{'garis':>6} {'disetujui':>10} {'default':>8} {'perkiraan':>12} "
          f"{'kenyataan':>12} {'kontribusi':>12}  {'aman?':>6}")
    for r in tabel_uji:
        if round(r["cutoff"], 2) in (0.04, 0.06, 0.08, 0.10, 0.12, 0.15, 0.20, 0.30, 0.40):
            aman = "ya" if r["default_rate"] and r["default_rate"] <= batas else "tidak"
            print(f"{r['cutoff']:>6.0%} {r['approval_rate']:>10.1%} {r['default_rate']:>8.1%} "
                  f"{juta(r['expected_loss']):>12} {juta(r['realized_loss']):>12} "
                  f"{juta(r['contribution']):>12}  {aman:>6}")

    print("\n" + "=" * 70)
    print("DIPILIH DI DATA VALIDASI 2014")
    print(f"  Puncak untung  : garis {puncak['cutoff']:.0%}"
          f"   kontribusi {juta(puncak['contribution'])}"
          f"   default {puncak['default_rate']:.1%}")
    print(f"  Batas risiko   : default rate maksimal {batas:.0%}")
    print(f"  Garis terpilih : garis {terpilih['cutoff']:.0%}"
          f"   kontribusi {juta(terpilih['contribution'])}"
          f"   default {terpilih['default_rate']:.1%}")
    print(f"  Skenario       : KEMUNGKINAN {pilihan['skenario']}")

    print("\nDINILAI DI DATA UJI 2015 -- belum pernah dilihat")
    print(f"  Garis {garis:.0%}")
    print(f"  Disetujui             {hasil['n_approved']:>9,}  ({hasil['approval_rate']:.1%})")
    print(f"  Default rate          {hasil['default_rate']:>9.1%}")
    print(f"  Masih di bawah {batas:.0%}?    {'YA' if masih_aman else 'TIDAK'}")
    print("=" * 70)

    if not masih_aman:
        # Garis paling longgar yang masih memenuhi batas risiko DI DATA UJI
        aman_uji = [r for r in tabel_uji
                    if r["default_rate"] is not None and r["default_rate"] <= batas]
        seharusnya = max(aman_uji, key=lambda r: r["cutoff"])["cutoff"] if aman_uji else None
        print("\nKEBIJAKAN TIDAK BERTAHAN.")
        print("Garis yang dirancang dengan data 2014 menghasilkan default rate")
        print(f"{hasil['default_rate']:.1%} di 2015, melewati batas {batas:.0%}.")
        print("Penyebabnya bukan model yang rusak -- urutannya masih baik. Yang")
        print("terjadi: kualitas pemohon menurun, dan PD model ikut meleset ke bawah.")
        if seharusnya:
            print(f"Dengan data 2015, garis yang memenuhi batas adalah {seharusnya:.0%}.")
        print("Di bank, inilah yang memicu peninjauan kebijakan: garis diperketat")
        print("atau angka PD dikoreksi, lalu disetujui ulang oleh komite.")

    if pilihan["skenario"] == 1:
        selisih = puncak["contribution"] - terpilih["contribution"]
        print("\nKEMUNGKINAN 1 -- batas risiko yang menentukan.")
        print(f"Harga dari kehati-hatian: {juta(selisih)} kontribusi yang dilepas.")
    else:
        print("\nKEMUNGKINAN 2 -- untung yang menentukan.")
        print("Garis paling untung sudah memenuhi batas risiko.")

    print(f"\nUANG (data uji 2015, garis {garis:.0%}):")
    print(f"  Exposure                  {juta(hasil['exposure']):>12}")
    print(f"  Perkiraan kerugian model  {juta(hasil['expected_loss']):>12}")
    print(f"  Kerugian sebenarnya       {juta(hasil['realized_loss']):>12}")
    kurang = hasil["realized_loss"] - hasil["expected_loss"]
    print(f"  Selisih                   {juta(kurang):>12}  "
          f"({kurang / hasil['expected_loss']:+.0%} dari perkiraan)")
    print(f"  Kontribusi kredit         {juta(hasil['contribution']):>12}")

    print(f"\nEMPAT KOTAK HASIL:")
    print(f"  Disetujui, lunas          {hasil['approved_good']:>9,}")
    print(f"  Disetujui, gagal bayar    {hasil['approved_bad']:>9,}")
    print(f"  Ditolak, akan lunas       {hasil['rejected_good']:>9,}   <- biaya tersembunyi")
    print(f"  Ditolak, memang gagal     {hasil['rejected_bad']:>9,}")
    print(f"  {hasil['good_rejected_per_bad_avoided']} pemohon baik ditolak "
          f"untuk setiap 1 gagal bayar yang dihindari")

    print(f"\nUJI KETAHANAN (kerugian dikalikan):")
    for r in stres:
        tanda = "" if r["contribution"] >= 0 else "   <- rugi"
        print(f"  {r['multiplier']:>4.1f}x  kerugian {juta(r['realized_loss']):>12}"
              f"   kontribusi {juta(r['contribution']):>12}{tanda}")
    if impas:
        print(f"  Kerugian boleh naik {(impas - 1) * 100:.0f}% sebelum kontribusi jadi nol.")

    print(f"\nTersimpan di artifacts/policy.json. Waktu {time.time() - mulai:.0f} detik.")


if __name__ == "__main__":
    main()