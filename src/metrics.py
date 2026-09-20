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
import pandas as pd
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

def calibration_table(y_true, y_prob, bins: int = 10) -> list:
    """Bandingkan perkiraan dengan kenyataan, per tingkat risiko.

    Cara kerjanya: urutkan semua pinjaman dari PD terendah ke
    tertinggi, bagi jadi 10 kelompok sama banyak, lalu untuk tiap
    kelompok hitung dua angka -- rata-rata PD yang diperkirakan
    model, dan berapa persen yang benar-benar gagal bayar.

    y_true  = kenyataan (1 = gagal bayar, 0 = lunas)
    y_prob  = perkiraan model (angka 0 sampai 1)
    bins    = jumlah kelompok, default 10
    """
    # Satukan kenyataan dan perkiraan dalam satu tabel
    df = pd.DataFrame({
        "kenyataan": np.asarray(y_true).astype(int),
        "perkiraan": np.asarray(y_prob, dtype=float),
    })

    # qcut membagi jadi 10 kelompok berisi jumlah baris yang sama.
    # Kelompok 0 = PD terendah, kelompok 9 = PD tertinggi.
    df["kelompok"] = pd.qcut(df["perkiraan"], q=bins, labels=False, duplicates="drop")

    hasil = []
    for nomor, kelompok in df.groupby("kelompok"):
        rata_perkiraan = float(kelompok["perkiraan"].mean())
        rata_kenyataan = float(kelompok["kenyataan"].mean())

        hasil.append({
            "decile": int(nomor) + 1,              # 1 sampai 10
            "n": int(len(kelompok)),               # jumlah pinjaman
            "pd_min": round(float(kelompok["perkiraan"].min()), 4),
            "pd_max": round(float(kelompok["perkiraan"].max()), 4),
            "mean_predicted": round(rata_perkiraan, 4),
            "actual_rate": round(rata_kenyataan, 4),
            # Selisih dalam poin persentase. Positif = model terlalu
            # optimis, kenyataannya lebih banyak yang gagal bayar.
            "gap_pp": round((rata_kenyataan - rata_perkiraan) * 100, 2),
        })

    return hasil

def vintage_table(years, y_true, y_prob) -> list:
    """Bandingkan perkiraan dengan kenyataan, per tahun pencairan.

    Sama seperti fungsi di atas, tapi pengelompokannya berdasarkan
    tahun pinjaman dicairkan, bukan tingkat risiko.

    years   = tahun pencairan tiap pinjaman
    y_true  = kenyataan (1 = gagal bayar, 0 = lunas)
    y_prob  = perkiraan model
    """
    df = pd.DataFrame({
        "tahun": np.asarray(years),
        "kenyataan": np.asarray(y_true).astype(int),
        "perkiraan": np.asarray(y_prob, dtype=float),
    })

    hasil = []
    for tahun, kelompok in df.groupby("tahun"):
        jumlah = len(kelompok)
        rata_perkiraan = float(kelompok["perkiraan"].mean())
        rata_kenyataan = float(kelompok["kenyataan"].mean())

        hasil.append({
            "vintage": int(tahun),
            "n": int(jumlah),
            # Diubah jadi jumlah pinjaman, bukan persen, supaya
            # lebih mudah dibaca orang non-teknis
            "predicted_defaults": int(round(rata_perkiraan * jumlah)),
            "actual_defaults": int(kelompok["kenyataan"].sum()),
            "mean_predicted": round(rata_perkiraan, 4),
            "actual_rate": round(rata_kenyataan, 4),
            "gap_pp": round((rata_kenyataan - rata_perkiraan) * 100, 2),
        })

    return hasil