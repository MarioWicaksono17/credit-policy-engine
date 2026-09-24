"""Tahap 5: siapkan bahan pembanding, lalu uji seluruh artefak.

Dua pekerjaan.

PERTAMA, membuat artifacts/reference.json. Isinya gambaran pemohon di
data latih: nilai tengah tiap variabel, sebarannya, dan daftar kategori.
Dipakai untuk dua hal:
  - mengisi bagian formulir yang tidak ditanyakan ke pemohon
  - menjelaskan posisi seorang pemohon, misalnya "kuartil tertinggi"

KEDUA, memastikan seluruh artefak benar-benar bisa dipakai bersama.
Satu pemohon contoh dinilai dari awal sampai akhir. Kalau ada yang tidak
cocok -- daftar fitur berbeda, kolom hilang -- ketahuan di sini, bukan
nanti setelah aplikasi web dibuat.
"""
import json
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import joblib
import numpy as np

from src import db
from src.config import load
from src.explain import apply_scenarios, assess
from src.features import prepare
from src.split import split_by_year


def main():
    mulai = time.time()
    cfg = load()
    root = cfg["_root"]
    art = root / "artifacts"

    meta = json.loads((art / "feature_meta.json").read_text(encoding="utf-8"))
    kebijakan = json.loads((art / "policy.json").read_text(encoding="utf-8"))
    model = joblib.load(art / "model.pkl")
    fitur = meta["numeric"] + meta["categorical"]

    print("Membaca data latih ...")
    df = prepare(db.read_table("silver_loans_clean"), cfg)
    latih = split_by_year(df, cfg)["train"]
    print(f"  {len(latih):,} pinjaman, {len(fitur)} fitur model")

    # ---------------------------------------------------- bahan pembanding
    print("Menyusun bahan pembanding ...")
    angka, kategori, bawaan = {}, {}, {}

    for f in meta["numeric"]:
        kolom = latih[f].astype(float).dropna()
        angka[f] = {
            "median": round(float(kolom.median()), 4),
            "p25": round(float(kolom.quantile(0.25)), 4),
            "p75": round(float(kolom.quantile(0.75)), 4),
            "min": round(float(kolom.min()), 4),
            "max": round(float(kolom.max()), 4),
            # 101 titik sebaran, dipakai untuk mencari posisi seorang
            # pemohon di antara pemohon lain
            "quantiles": [round(float(v), 4)
                          for v in np.quantile(kolom, np.linspace(0, 1, 101))],
        }
        bawaan[f] = angka[f]["median"]

    for f in meta["categorical"]:
        porsi = latih[f].value_counts(normalize=True)
        kategori[f] = {
            "values": [str(v) for v in porsi.index],
            "shares": {str(k): round(float(v), 4) for k, v in porsi.items()},
        }
        bawaan[f] = str(porsi.index[0])          # kategori tersering

    (art / "reference.json").write_text(json.dumps({
        "model_version": cfg["model_version"],
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "built_from": "train",
        "n_train": len(latih),
        "numeric": angka,
        "categorical": kategori,
        "defaults": bawaan,
    }, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  reference.json: {len(angka)} variabel angka, {len(kategori)} kategori")

    # ---------------------------------------------------- uji menyeluruh
    referensi = json.loads((art / "reference.json").read_text(encoding="utf-8"))
    garis = kebijakan["chosen_cutoff"]
    label = cfg.get("labels", {})

    print(f"\nMenguji penilaian satu pemohon (garis batas {garis:.0%}) ...")

    # Pemohon rata-rata: semua isian diisi nilai tengah
    hasil = assess({}, model, meta, referensi, garis, label)
    print(f"\n  PEMOHON RATA-RATA")
    print(f"    PD {hasil['pd']:.1%}  ->  {hasil['decision']}")

    # Pemohon berisiko: beberapa isian dibuat lebih buruk
    # Dibuat cukup ekstrem -- memakai kuartil saja sering tidak cukup untuk
    # menguji skenario alternatif, karena nilainya bisa sudah lebih baik
    # dari target skenario.
    def titik(f, persen):
        return angka[f]["quantiles"][persen] if f in angka else None

    berisiko = {}
    for f in ("dti", "revol_util", "inq_last_6mths", "acc_open_past_24mths"):
        if f in angka:
            berisiko[f] = titik(f, 95)          # jauh lebih buruk dari kebanyakan
    for f in ("fico_score", "annual_inc"):
        if f in angka:
            berisiko[f] = titik(f, 10)

    hasil2 = assess(berisiko, model, meta, referensi, garis, label)
    print(f"\n  PEMOHON BERISIKO")
    print(f"    PD {hasil2['pd']:.1%}  ->  {hasil2['decision']}")
    print(f"    Alasan penentu:")
    for r in hasil2["reason_codes"]:
        print(f"      {r['code']}  {r['reason']:<52} {r['contribution']:+.3f}")

    skenario = apply_scenarios(berisiko, model, meta, referensi, garis,
                               cfg.get("scenarios", []))
    if skenario:
        print(f"    Skenario alternatif:")
        for s in skenario:
            catatan = "" if s["affects_model"] else "   <- tidak menyentuh fitur model"
            print(f"      {s['name']:<34} PD {s['pd']:>6.1%}   {s['decision']}{catatan}")
        mati = [s["name"] for s in skenario if not s["affects_model"]]
        if mati:
            print(f"\n    PERHATIAN: skenario berikut tidak berpengaruh karena")
            print(f"    variabel yang diubah bukan fitur model: {', '.join(mati)}")

    # ---------------------------------------------------- daftar artefak
    daftar = []
    for nama in ["model.pkl", "feature_meta.json", "feature_selection.json",
                 "metrics.json", "policy.json", "reference.json"]:
        f = art / nama
        daftar.append({"file": nama, "size_kb": round(f.stat().st_size / 1024, 1)})

    (art / "manifest.json").write_text(json.dumps({
        "model_version": cfg["model_version"],
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "chosen_cutoff": garis,
        "files": daftar,
    }, indent=2), encoding="utf-8")

    print(f"\n  Artefak siap dipakai aplikasi:")
    total = 0
    for d in daftar:
        total += d["size_kb"]
        print(f"    {d['file']:<26} {d['size_kb']:>8.1f} KB")
    print(f"    {'TOTAL':<26} {total:>8.1f} KB")

    print(f"\nSelesai. Waktu {time.time() - mulai:.0f} detik.")


if __name__ == "__main__":
    main()