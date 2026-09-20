"""Kebijakan kredit: mengubah angka PD menjadi keputusan.

Model menghasilkan PD. PD itu sendiri belum keputusan -- baru jadi
keputusan setelah kita menarik garis batas.

Menarik garis adalah keputusan bisnis, bukan keputusan statistik.
Karena itu file ini terpisah dari model.py: di bank pun, tim yang
membangun model dan tim yang menetapkan kebijakan kredit adalah
tim yang berbeda.
"""
import numpy as np
import pandas as pd


def decide(pd_scores, cutoff: float) -> np.ndarray:
    """Terapkan garis batas. True artinya disetujui.

    pd_scores = angka PD tiap pinjaman
    cutoff    = garis batas, misalnya 0.20
    """
    return np.asarray(pd_scores, dtype=float) < cutoff


def outcome_counts(pd_scores, y_true, cutoff: float) -> dict:
    """Bagi seluruh pinjaman ke empat kotak hasil.

    Empat kotak itu:
      approved_good   disetujui, ternyata lunas      -> untung
      approved_bad    disetujui, ternyata gagal      -> rugi
      rejected_good   ditolak, padahal akan lunas    -> peluang hilang
      rejected_bad    ditolak, memang gagal          -> kerugian dicegah

    Kotak ketiga adalah biaya yang tidak pernah muncul di laporan
    keuangan mana pun, karena uangnya memang tidak pernah dipinjamkan.
    """
    approved = decide(pd_scores, cutoff)
    bad = np.asarray(y_true).astype(bool)

    return {
        "approved_good": int((approved & ~bad).sum()),
        "approved_bad": int((approved & bad).sum()),
        "rejected_good": int((~approved & ~bad).sum()),
        "rejected_bad": int((~approved & bad).sum()),
    }


def expected_loss(pd_scores, ead, lgd: float, mask=None) -> float:
    """Hitung perkiraan kerugian: PD x LGD x EAD, dijumlahkan.

    pd_scores = angka PD tiap pinjaman
    ead       = besar pinjaman (loan_amnt)
    lgd       = porsi yang hilang bila gagal bayar, ASUMSI
    mask      = pilih sebagian pinjaman saja, misalnya yang disetujui
    """
    p = np.asarray(pd_scores, dtype=float)
    e = np.asarray(ead, dtype=float)

    if mask is not None:
        p, e = p[mask], e[mask]

    return float((p * e * lgd).sum())


def evaluate_cutoff(pd_scores, y_true, ead, cutoff: float, lgd: float) -> dict:
    """Hitung seluruh dampak dari satu garis batas."""
    p = np.asarray(pd_scores, dtype=float)
    y = np.asarray(y_true).astype(int)
    e = np.asarray(ead, dtype=float)

    approved = decide(p, cutoff)
    counts = outcome_counts(p, y, cutoff)

    n_approved = int(approved.sum())
    n_total = len(p)

    # Kalau batasnya sangat ketat, bisa saja tidak ada yang disetujui.
    # Pembagian dengan nol harus dicegah.
    if n_approved == 0:
        return {
            "cutoff": round(cutoff, 4),
            "approval_rate": 0.0,
            "n_approved": 0,
            "exposure": 0.0,
            "default_rate": None,
            "expected_loss": 0.0,
            "el_pct_exposure": None,
            **counts,
            "good_rejected_per_bad_avoided": None,
        }

    exposure = float(e[approved].sum())
    el = expected_loss(p, e, lgd, mask=approved)

    # Berapa pemohon baik yang ikut tertolak untuk setiap satu
    # gagal bayar yang berhasil dihindari. Inilah harga dari
    # memperketat batas.
    rasio = (counts["rejected_good"] / counts["rejected_bad"]
             if counts["rejected_bad"] > 0 else None)

    return {
        "cutoff": round(cutoff, 4),
        "approval_rate": round(n_approved / n_total, 4),
        "n_approved": n_approved,
        "exposure": round(exposure, 2),
        "default_rate": round(float(y[approved].mean()), 4),
        "expected_loss": round(el, 2),
        "el_pct_exposure": round(el / exposure, 4),
        **counts,
        "good_rejected_per_bad_avoided": round(rasio, 2) if rasio else None,
    }


def sweep(pd_scores, y_true, ead, cfg: dict, lgd: float = None) -> list:
    """Hitung dampak untuk SEMUA garis batas yang mungkin.

    Hasilnya ini yang dipakai slider di halaman Kebijakan kredit.
    Seluruh tabel dihitung sekali di sini, lalu diunduh browser
    sekaligus -- supaya menggeser slider terasa seketika dan tidak
    perlu bolak-balik ke server.
    """
    s = cfg["policy"]["sweep"]
    lgd = lgd if lgd is not None else cfg["policy"]["lgd_assumption"]

    cutoffs = np.arange(s["start"], s["stop"] + s["step"] / 2, s["step"])
    return [evaluate_cutoff(pd_scores, y_true, ead, float(c), lgd) for c in cutoffs]


def lgd_sensitivity(pd_scores, y_true, ead, cfg: dict) -> list:
    """Uji seberapa berubah kesimpulan bila asumsi LGD diganti.

    LGD tidak bisa dihitung dari dataset ini karena tidak ada catatan
    penagihan setelah gagal bayar. Karena itu nilainya diuji pada
    beberapa kemungkinan, bukan dipakai satu angka seolah pasti.
    """
    cutoff = cfg["policy"]["cutoff"]
    hasil = []

    for lgd in cfg["policy"]["lgd_sensitivity"]:
        r = evaluate_cutoff(pd_scores, y_true, ead, cutoff, lgd)
        hasil.append({
            "lgd": lgd,
            "expected_loss": r["expected_loss"],
            "el_pct_exposure": r["el_pct_exposure"],
        })

    return hasil