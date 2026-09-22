"""Tahap 3: pilih fitur, latih model, dan evaluasi.

Urutannya:
  1. Pilih fitur dengan Information Value -- dari data latih saja
  2. Latih model utama, buang fitur yang arah koefisiennya tidak masuk akal
  3. Latih tiga pembanding:
       - model utama dengan pembagian ACAK         -> seberapa jauh berbeda
                                                      dari pembagian waktu
       - model utama DITAMBAH suku bunga           -> seberapa bergantung
                                                      pada penilaian LC
       - model rumit dengan SEMUA 67 fitur         -> berapa akurasi yang
                                                      dikorbankan demi model
                                                      yang bisa dijelaskan
  4. Periksa kalibrasi per tingkat risiko dan per tahun

Hasil yang disimpan di artifacts/:
  model.pkl               model utama
  feature_meta.json       daftar fitur yang dipakai model utama
  feature_selection.json  alasan setiap fitur dipilih atau dibuang
  metrics.json            seluruh angka evaluasi
"""
import json
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import joblib
import pandas as pd

from src import db
from src.config import load
from src.features import (coefficient_table, prepare, select_features, sign_flips,
                          split_numeric_categorical, split_xy)
from src.metrics import calibration_table, evaluate, vintage_table
from src.model import build_pipeline
from src.preprocess import model_features
from src.split import split_by_year, split_random


def latih(nama, fitur, cfg, data_latih):
    """Latih satu model dengan daftar fitur tertentu."""
    numerik, kategori = split_numeric_categorical(fitur, cfg)
    X, y = split_xy(data_latih, fitur)
    pipe = build_pipeline(nama, numerik, kategori, cfg)
    pipe.fit(X, y)
    return pipe


def nilai(pipe, fitur, himpunan: dict) -> dict:
    """Evaluasi satu model di beberapa himpunan data sekaligus."""
    hasil = {}
    for label, df in himpunan.items():
        X, y = split_xy(df, fitur)
        hasil[label] = evaluate(y, pipe.predict_proba(X)[:, 1])
    return hasil


def main():
    mulai = time.time()
    cfg = load()
    root = cfg["_root"]
    juara = cfg["model"]["champion"]

    # ------------------------------------------------------------ data
    print("Membaca silver_loans_clean ...")
    df = prepare(db.read_table("silver_loans_clean"), cfg)
    bagian = split_by_year(df, cfg)
    for k, v in bagian.items():
        print(f"  {k:9s} {len(v):>9,} pinjaman   default {v['default_flag'].mean():.2%}")
    acak = split_random(df, cfg) if cfg["split"].get("keep_random_benchmark") else {}
    uji_waktu = {"oot_val": bagian["oot_val"], "oot_test": bagian["oot_test"]}

    # ------------------------------------------------------------ 1. pilih fitur
    print(f"\n1. Memilih fitur dari {len(model_features(cfg))} kandidat (hanya data latih) ...")
    terpilih, laporan, curiga = select_features(bagian["train"], cfg)
    for f in curiga:
        print(f"  PERHATIAN: IV {f} di atas {cfg['feature_selection']['suspicious_iv']} "
              f"-- periksa kemungkinan kebocoran")
    print(f"  {len(terpilih)} fitur lolos penyaringan IV dan korelasi")

    # ------------------------------------------------------------ 2. model utama
    print("\n2. Melatih model utama dan memeriksa arah koefisien ...")
    while True:
        pipe = latih(juara, terpilih, cfg, bagian["train"])
        numerik, _ = split_numeric_categorical(terpilih, cfg)
        terbalik = sign_flips(pipe, bagian["train"], numerik)
        if not terbalik:
            break
        # Buang yang IV-nya paling rendah di antara yang terbalik, lalu ulangi
        iv = laporan.set_index("feature")["iv"]
        buang = min(terbalik, key=lambda t: iv[t["feature"]])
        f = buang["feature"]
        terpilih.remove(f)
        laporan.loc[laporan["feature"] == f, ["status", "reason"]] = [
            "dibuang",
            f"arah koefisien berlawanan dengan hubungan aslinya "
            f"(koefisien {buang['coef']:+.3f}, hubungan satu variabel {buang['univariate']:+.3f})",
        ]
        print(f"  dibuang: {f} -- arah koefisien berlawanan")

    numerik, kategori = split_numeric_categorical(terpilih, cfg)
    print(f"  Model utama memakai {len(terpilih)} fitur")
    hasil = {"champion": nilai(pipe, terpilih, uji_waktu)}
    model_utama = pipe

    # ------------------------------------------------------------ 3. pembanding
    print("\n3. Melatih pembanding ...")

    if acak:
        print("  - model utama, pembagian acak")
        p = latih(juara, terpilih, cfg, acak["random_train"])
        hasil["champion"].update(nilai(p, terpilih, {"random_test": acak["random_test"]}))

    tambah = cfg["feature_policy"]["with_pricing_adds"]
    print(f"  - model utama + {', '.join(tambah)}")
    p = latih(juara, terpilih + tambah, cfg, bagian["train"])
    hasil["with_pricing"] = nilai(p, terpilih + tambah, uji_waktu)

    semua = model_features(cfg)
    for nama in cfg["model"]["challengers"]:
        print(f"  - {nama}, semua {len(semua)} fitur")
        p = latih(nama, semua, cfg, bagian["train"])
        hasil[nama] = nilai(p, semua, uji_waktu)

    # ------------------------------------------------------------ 4. kalibrasi
    X_uji, y_uji = split_xy(bagian["oot_test"], terpilih)
    p_uji = model_utama.predict_proba(X_uji)[:, 1]
    gabung = pd.concat([bagian["train"], bagian["oot_val"], bagian["oot_test"]])
    X_g, y_g = split_xy(gabung, terpilih)
    diagnosis = {
        "calibration_deciles": calibration_table(y_uji, p_uji),
        "by_vintage": vintage_table(gabung["issue_year"], y_g,
                                    model_utama.predict_proba(X_g)[:, 1]),
    }

    iv_semua = laporan.set_index("feature")["iv"].to_dict()
    koefisien = coefficient_table(model_utama, iv_semua, kategori)

    # ------------------------------------------------------------ simpan
    art = root / "artifacts"
    art.mkdir(exist_ok=True)
    joblib.dump(model_utama, art / "model.pkl")

    tulis = lambda nama, isi: (art / nama).write_text(
        json.dumps(isi, indent=2, ensure_ascii=False), encoding="utf-8")

    tulis("feature_meta.json", {
        "model_version": cfg["model_version"],
        "champion": juara,
        "numeric": numerik,
        "categorical": kategori,
    })
    tulis("feature_selection.json", {
        "chosen_on": "train",
        "rules": cfg["feature_selection"],
        "n_candidates": len(semua),
        "n_selected": len(terpilih),
        "suspicious": curiga,
        "features": laporan.round({"iv": 4}).to_dict(orient="records"),
    })
    tulis("metrics.json", {
        "model_version": cfg["model_version"],
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "champion": juara,
        "split_sizes": {k: len(v) for k, v in {**bagian, **acak}.items()},
        "results": hasil,
        "coefficients": koefisien,
        "diagnostics": diagnosis,
    })

    # ------------------------------------------------------------ tampilkan
    print("\n" + "=" * 68)
    print("FITUR MODEL UTAMA")
    print("=" * 68)
    print(f"{'fitur':<34} {'IV':>6} {'koefisien':>10}")
    for b in koefisien:
        print(f"{b['feature']:<34} {b['iv']:>6.3f} {b['coef']:>+10.3f}")

    ringkas = laporan.groupby("status").size().to_dict()
    print(f"\nDari {len(semua)} kandidat: {ringkas.get('dipilih', 0)} dipilih, "
          f"{ringkas.get('dibuang', 0)} dibuang")
    alasan = laporan[laporan["status"] == "dibuang"]["reason"].str.split(" ").str[0]
    for a, n in alasan.value_counts().items():
        label = {"IV": "IV terlalu rendah", "kembar": "kembar dengan fitur lain",
                 "di": "di luar batas jumlah", "arah": "arah koefisien terbalik"}.get(a, a)
        print(f"  {n:>3} {label}")

    print("\n" + "=" * 68)
    print("PERBANDINGAN MODEL (data uji 2015)")
    print("=" * 68)
    print(f"{'model':<32} {'fitur':>6} {'AUC':>7} {'KS':>7} {'selisih kalibrasi':>18}")
    jumlah = {"champion": len(terpilih), "with_pricing": len(terpilih) + len(tambah)}
    for nama, r in hasil.items():
        t = r["oot_test"]
        print(f"{nama:<32} {jumlah.get(nama, len(semua)):>6} {t['auc']:>7.4f} "
              f"{t['ks']:>7.4f} {t['calibration_gap_pp']:>+17.2f} pp")
    if "random_test" in hasil["champion"]:
        r = hasil["champion"]["random_test"]
        print(f"{'champion, pembagian acak':<32} {len(terpilih):>6} {r['auc']:>7.4f} "
              f"{r['ks']:>7.4f} {r['calibration_gap_pp']:>+17.2f} pp")

    print("\n" + "=" * 68)
    print("KALIBRASI PER TINGKAT RISIKO (data uji 2015)")
    print("=" * 68)
    print(f"{'klp':>4} {'perkiraan':>11} {'kenyataan':>11} {'selisih':>10}")
    for r in diagnosis["calibration_deciles"]:
        print(f"{r['decile']:>4} {r['mean_predicted']:>11.4f} "
              f"{r['actual_rate']:>11.4f} {r['gap_pp']:>+9.2f} pp")

    print("\n" + "=" * 68)
    print("PERKIRAAN DAN KENYATAAN PER TAHUN")
    print("=" * 68)
    print(f"{'tahun':>6} {'pinjaman':>10} {'perkiraan':>11} {'kenyataan':>11} {'selisih':>10}")
    for r in diagnosis["by_vintage"]:
        print(f"{r['vintage']:>6} {r['n']:>10,} {r['predicted_defaults']:>11,} "
              f"{r['actual_defaults']:>11,} {r['gap_pp']:>+9.2f} pp")

    print(f"\nTersimpan di artifacts/. Waktu {time.time() - mulai:.0f} detik.")


if __name__ == "__main__":
    main()