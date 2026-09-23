"""Koreksi kalibrasi: menyetel ulang titik nol.

Dari tabel kalibrasi kita tahu model selalu terlalu optimis, dan
melesetnya SEARAH di kesepuluh kelompok risiko. Itu ciri timbangan yang
titik nolnya bergeser, bukan timbangan yang rusak.

Perbaikannya: geser semua angka PD dengan satu angka yang sama. Rumus
model tidak disentuh sama sekali.

Yang penting: pergeseran dilakukan pada SKALA LOG-ODDS, bukan pada
persen. Kalau PD ditambah begitu saja, misalnya semua ditambah 2%,
angka 99% akan jadi 101% -- tidak masuk akal. Skala log-odds membuat
semua hasil tetap berada di antara 0 dan 1, dan yang tinggi digeser
lebih sedikit daripada yang rendah.

Karena semua angka digeser dengan cara yang sama, URUTANNYA tidak
berubah sedikit pun. AUC sebelum dan sesudah koreksi akan sama persis
-- itu sekaligus bukti bahwa koreksi ini hanya menggeser level.
"""
import numpy as np
from scipy.optimize import brentq

EPS = 1e-6


def _logit(p):
    """Ubah peluang (0-1) menjadi skala log-odds (bebas, bisa negatif)."""
    p = np.clip(np.asarray(p, dtype=float), EPS, 1 - EPS)
    return np.log(p / (1 - p))


def _sigmoid(z):
    """Kebalikan dari _logit: kembalikan ke peluang 0-1."""
    return 1 / (1 + np.exp(-z))


def apply_offset(p, offset: float):
    """Geser seluruh PD sebesar offset pada skala log-odds."""
    if not offset:
        return np.asarray(p, dtype=float)
    return _sigmoid(_logit(p) + offset)


def fit_offset(y_true, p) -> float:
    """Cari satu angka penggeser supaya rata-rata PD sama dengan kenyataan.

    Dihitung dari data validasi, lalu dipakai apa adanya di data uji --
    sama seperti model itu sendiri. Kalau penggesernya dihitung dari data
    uji, itu sama dengan mengintip jawabannya.
    """
    target = float(np.mean(np.asarray(y_true, dtype=float)))
    p = np.asarray(p, dtype=float)

    def selisih(a):
        return float(np.mean(apply_offset(p, a))) - target

    if abs(selisih(0.0)) < 1e-12:
        return 0.0
    return float(brentq(selisih, -5.0, 5.0, xtol=1e-10))


def summarize(y_true, p, offset: float) -> dict:
    """Ringkasan sebelum dan sesudah koreksi, untuk satu himpunan data."""
    y = np.asarray(y_true, dtype=float)
    p_baru = apply_offset(p, offset)
    return {
        "actual_rate": round(float(y.mean()), 4),
        "mean_predicted_before": round(float(np.mean(p)), 4),
        "mean_predicted_after": round(float(p_baru.mean()), 4),
        "gap_pp_before": round(float((y.mean() - np.mean(p)) * 100), 2),
        "gap_pp_after": round(float((y.mean() - p_baru.mean()) * 100), 2),
    }