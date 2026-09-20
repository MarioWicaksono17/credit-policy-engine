"""Metrik evaluasi model.

Dipisahkan menjadi dua kelompok yang mengukur hal berbeda:

  Diskriminasi  Apakah urutan risikonya benar -- apakah yang gagal
                bayar ditempatkan lebih berisiko daripada yang lunas.
                Diukur dengan AUC, KS, dan Gini.

  Kalibrasi     Apakah angka PD-nya sesuai kenyataan. Diukur dengan
                Brier score dan perbandingan rata-rata prediksi
                terhadap realisasi.

Model bisa bagus di satu kelompok dan buruk di kelompok lain.
Keputusan terima-tolak hanya butuh diskriminasi; perhitungan
kerugian butuh kalibrasi.
"""
import numpy as np
from sklearn.metrics import brier_score_loss, roc_auc_score, roc_curve


def ks_statistic(y_true, y_prob) -> float:
    """Jarak maksimum antara distribusi kumulatif good dan bad."""
    fpr, tpr, _ = roc_curve(y_true, y_prob)
    return float(np.max(tpr - fpr))


def evaluate(y_true, y_prob) -> dict:
    """Hitung seluruh metrik untuk satu himpunan prediksi."""
    y_true = np.asarray(y_true).astype(int)
    y_prob = np.asarray(y_prob, dtype=float)

    auc = float(roc_auc_score(y_true, y_prob))

    return {
        "n": int(len(y_true)),
        # diskriminasi
        "auc": round(auc, 4),
        "gini": round(2 * auc - 1, 4),
        "ks": round(ks_statistic(y_true, y_prob), 4),
        # kalibrasi
        "brier": round(float(brier_score_loss(y_true, y_prob)), 5),
        "mean_predicted": round(float(y_prob.mean()), 4),
        "actual_rate": round(float(y_true.mean()), 4),
        "calibration_gap_pp": round(float((y_true.mean() - y_prob.mean()) * 100), 2),
    }