"""Tahap 3: latih dan evaluasi model.

Menghasilkan dua artefak:
  artifacts/model.pkl      champion, siap dipakai menilai aplikasi
  artifacts/metrics.json   seluruh angka evaluasi

Rancangan eksperimen:
  - Tiga algoritma dilatih pada kedua kebijakan fitur, dievaluasi
    out-of-time.
  - Pembanding pembagian acak hanya dijalankan untuk champion,
    karena tujuannya membandingkan skema validasi, bukan algoritma.
"""
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import joblib

from src import db
from src.config import load
from src.features import get_features, prepare, split_xy
from src.metrics import calibration_table, evaluate, vintage_table
from src.model import build_pipeline
from src.split import split_out_of_time, split_random


def fit_and_score(name, numeric, categorical, cfg, train_df, eval_sets):
    """Latih satu model, lalu evaluasi pada beberapa himpunan sekaligus."""
    X_train, y_train = split_xy(train_df, numeric, categorical)

    pipe = build_pipeline(name, numeric, categorical, cfg)
    pipe.fit(X_train, y_train)

    scores = {}
    for label, df_eval in eval_sets.items():
        X, y = split_xy(df_eval, numeric, categorical)
        scores[label] = evaluate(y, pipe.predict_proba(X)[:, 1])

    return pipe, scores


def main():
    cfg = load()
    root = cfg["_root"]
    champion = cfg["model"]["champion"]
    active = cfg["features"]["active_policy"]
    algorithms = [champion] + cfg["model"]["challengers"]

    print("Membaca silver_loans_clean ...")
    df = prepare(db.read_table("silver_loans_clean"))
    print(f"  {len(df):,} baris")

    oot = split_out_of_time(df, cfg)
    for k, v in oot.items():
        print(f"  {k:9s} {len(v):>8,} baris   default rate {v['default_flag'].mean():.4f}")

    rnd = split_random(df, cfg) if cfg["split"].get("keep_random_benchmark") else {}

    results = {}
    champion_pipe = None

    for policy in ["application_only", "with_pricing"]:
        numeric, categorical = get_features(df, cfg, policy)
        print(f"\nKebijakan fitur: {policy}")
        print(f"  {len(numeric)} numerik + {len(categorical)} kategorik")

        results[policy] = {}

        for name in algorithms:
            print(f"  melatih {name} ...", flush=True)

            eval_sets = {"oot_val": oot["oot_val"], "oot_test": oot["oot_test"]}
            pipe, scores = fit_and_score(
                name, numeric, categorical, cfg, oot["train"], eval_sets
            )

            # Pembanding pembagian acak, hanya untuk champion
            if rnd and name == champion:
                _, rnd_scores = fit_and_score(
                    name, numeric, categorical, cfg,
                    rnd["random_train"], {"random_test": rnd["random_test"]},
                )
                scores.update(rnd_scores)

            results[policy][name] = scores
            print(f"    AUC oot_test {scores['oot_test']['auc']:.4f}"
                  f"   selisih kalibrasi {scores['oot_test']['calibration_gap_pp']:+.2f} pp")

            if policy == active and name == champion:
                champion_pipe = pipe
                champion_features = {"numeric": numeric, "categorical": categorical}

                # Hitung dua tabel diagnosis, hanya untuk model utama.
                # Model pembanding tidak perlu -- kita tidak akan memakainya.

                # Ambil data uji dan hitung PD tiap pinjaman
                X_test, y_test = split_xy(oot["oot_test"], numeric, categorical)
                p_test = pipe.predict_proba(X_test)[:, 1]

                diagnostics = {
                    # Meleset merata atau tidak?
                    "calibration_deciles": calibration_table(y_test, p_test),
                    # Meleset makin parah seiring waktu atau tidak?
                    "by_vintage": vintage_table(
                        oot["oot_test"]["issue_year"], y_test, p_test
                    ),
                }

    # --- simpan artefak ---
    artifacts = root / "artifacts"
    artifacts.mkdir(exist_ok=True)

    joblib.dump(champion_pipe, artifacts / "model.pkl")

    (artifacts / "feature_meta.json").write_text(
        json.dumps({
            "policy": active,
            "champion": champion,
            **champion_features,
        }, indent=2),
        encoding="utf-8",
    )

    (artifacts / "metrics.json").write_text(
        json.dumps({
            "model_version": cfg["model_version"],
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "active_policy": active,
            "champion": champion,
            "split_sizes": {k: len(v) for k, v in {**oot, **rnd}.items()},
            "results": results,
            "diagnostics": diagnostics,
        }, indent=2),
        encoding="utf-8",
    )

    best = results[active][champion]["oot_test"]
    print(f"\nChampion: {champion} pada {active}")
    print(f"  AUC {best['auc']}  KS {best['ks']}  Gini {best['gini']}")
    print(f"  Prediksi rata-rata {best['mean_predicted']} vs realisasi {best['actual_rate']}")

    # Tampilkan tabel diagnosis di layar supaya bisa langsung dibaca
    print("\nPerbandingan per tingkat risiko (10 kelompok, dari paling aman):")
    print(f"  {'klp':>4} {'jumlah':>9} {'perkiraan':>11} {'kenyataan':>11} {'selisih':>10}")
    for r in diagnostics["calibration_deciles"]:
        print(f"  {r['decile']:>4} {r['n']:>9,} {r['mean_predicted']:>11.4f} "
              f"{r['actual_rate']:>11.4f} {r['gap_pp']:>+9.2f} pp")

    print("\nPerbandingan per tahun pencairan:")
    print(f"  {'tahun':>5} {'jumlah':>9} {'perkiraan':>11} {'kenyataan':>11} {'selisih':>10}")
    for r in diagnostics["by_vintage"]:
        print(f"  {r['vintage']:>5} {r['n']:>9,} {r['predicted_defaults']:>11,} "
              f"{r['actual_defaults']:>11,} {r['gap_pp']:>+9.2f} pp")

    print(f"\nArtefak tersimpan di artifacts/")


if __name__ == "__main__":
    main()