"""Metrik evaluasi.

Dua kelompok yang mengukur hal berbeda:

  Diskriminasi  Apakah URUTAN risikonya benar. Diukur dengan AUC, KS, Gini.
                Cukup untuk keputusan terima-tolak.

  Kalibrasi     Apakah ANGKA PD-nya sesuai kenyataan. Diukur dengan Brier
                score dan selisih rata-rata prediksi terhadap realisasi.
                Dibutuhkan ketika PD dikalikan dengan uang.
"""
import numpy as np
import pandas as pd
from sklearn.metrics import brier_score_loss, roc_auc_score, roc_curve


def ks_statistic(y_true, y_prob) -> float:
    """Jarak terlebar antara sebaran peminjam lunas dan gagal bayar."""
    fpr, tpr, _ = roc_curve(y_true, y_prob)
    return float(np.max(tpr - fpr))


def evaluate(y_true, y_prob) -> dict:
    """Seluruh metrik untuk satu himpunan prediksi."""
    y = np.asarray(y_true).astype(int)
    p = np.asarray(y_prob, dtype=float)
    auc = float(roc_auc_score(y, p))
    return {
        "n": int(len(y)),
        "auc": round(auc, 4),
        "gini": round(2 * auc - 1, 4),
        "ks": round(ks_statistic(y, p), 4),
        "brier": round(float(brier_score_loss(y, p)), 5),
        "mean_predicted": round(float(p.mean()), 4),
        "actual_rate": round(float(y.mean()), 4),
        # Positif = model terlalu optimis: kenyataannya lebih banyak gagal bayar
        "calibration_gap_pp": round(float((y.mean() - p.mean()) * 100), 2),
    }


def calibration_table(y_true, y_prob, bins: int = 10) -> list:
    """Perkiraan dibanding kenyataan, per tingkat risiko.

    Urutkan semua pinjaman dari PD terendah ke tertinggi, bagi jadi 10
    kelompok sama besar, lalu bandingkan di tiap kelompok.

    Selisih searah di semua kelompok  -> pergeseran level, bisa dikoreksi
    Selisih berganti arah             -> bentuk model yang salah
    """
    d = pd.DataFrame({"y": np.asarray(y_true).astype(int),
                      "p": np.asarray(y_prob, dtype=float)})
    d["k"] = pd.qcut(d["p"], q=bins, labels=False, duplicates="drop")
    hasil = []
    for k, g in d.groupby("k"):
        hasil.append({
            "decile": int(k) + 1,
            "n": int(len(g)),
            "mean_predicted": round(float(g["p"].mean()), 4),
            "actual_rate": round(float(g["y"].mean()), 4),
            "gap_pp": round(float((g["y"].mean() - g["p"].mean()) * 100), 2),
        })
    return hasil


def vintage_table(years, y_true, y_prob) -> list:
    """Perkiraan dibanding kenyataan, per tahun pencairan."""
    d = pd.DataFrame({"t": np.asarray(years), "y": np.asarray(y_true).astype(int),
                      "p": np.asarray(y_prob, dtype=float)})
    hasil = []
    for t, g in d.groupby("t"):
        hasil.append({
            "vintage": int(t),
            "n": int(len(g)),
            "predicted_defaults": int(round(g["p"].sum())),
            "actual_defaults": int(g["y"].sum()),
            "mean_predicted": round(float(g["p"].mean()), 4),
            "actual_rate": round(float(g["y"].mean()), 4),
            "gap_pp": round(float((g["y"].mean() - g["p"].mean()) * 100), 2),
        })
    return hasil