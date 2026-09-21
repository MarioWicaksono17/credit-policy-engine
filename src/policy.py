"""Kebijakan kredit: mengubah angka PD menjadi keputusan.

Model menghasilkan PD. PD belum keputusan -- baru jadi keputusan
setelah kita menarik garis batas.

Garis batas dipilih dengan dua pertimbangan:
  1. Untung  -- garis mana yang menghasilkan untung bersih terbesar
  2. Risiko  -- garis mana yang masih memenuhi batas risiko

Yang dipilih: garis paling untung di antara garis yang memenuhi
batas risiko. Seperti memilih makanan paling enak, asal harganya
tidak melebihi uang saku.
"""
import numpy as np


def decide(pd_scores, cutoff: float) -> np.ndarray:
    """Terapkan garis batas. True artinya disetujui."""
    return np.asarray(pd_scores, dtype=float) < cutoff


def net_interest(installment, term_months, loan_amnt, net_margin: float) -> np.ndarray:
    """Untung bersih bank dari satu pinjaman, KALAU pinjaman itu lunas.

    Total bunga = angsuran per bulan x jumlah bulan - pokok pinjaman.
    Tidak semuanya jadi untung: sebagian habis untuk biaya dana dan
    operasional. net_margin adalah bagian yang tersisa.

    Catatan kejujuran: ini perkiraan tertinggi. Pinjaman yang dilunasi
    lebih cepat membayar bunga lebih sedikit, dan dataset tidak
    mencatat kapan pelunasan terjadi.
    """
    angsuran = np.asarray(installment, dtype=float)
    bulan = np.asarray(term_months, dtype=float)
    pokok = np.asarray(loan_amnt, dtype=float)

    total_bunga = angsuran * bulan - pokok
    return total_bunga * net_margin


def evaluate_cutoff(pd_scores, y_true, ead, revenue, cutoff: float, lgd: float) -> dict:
    """Hitung seluruh dampak dari satu garis batas.

    pd_scores = PD tiap pinjaman, dari model
    y_true    = kejadian sebenarnya (1 = gagal bayar, 0 = lunas)
    ead       = besar pinjaman
    revenue   = untung bersih tiap pinjaman kalau lunas
    cutoff    = garis batas yang dinilai
    lgd       = porsi yang hilang bila gagal bayar
    """
    p = np.asarray(pd_scores, dtype=float)
    gagal = np.asarray(y_true).astype(bool)
    e = np.asarray(ead, dtype=float)
    r = np.asarray(revenue, dtype=float)

    disetujui = decide(p, cutoff)

    # Empat kotak hasil
    setuju_lunas = disetujui & ~gagal
    setuju_gagal = disetujui & gagal
    tolak_lunas = ~disetujui & ~gagal
    tolak_gagal = ~disetujui & gagal

    n_setuju = int(disetujui.sum())

    # Kalau tidak ada yang disetujui, tidak ada yang bisa dihitung
    if n_setuju == 0:
        return {
            "cutoff": round(cutoff, 4), "approval_rate": 0.0, "n_approved": 0,
            "exposure": 0.0, "default_rate": None,
            "expected_loss": 0.0, "el_pct_exposure": None,
            "income": 0.0, "realized_loss": 0.0, "net_profit": 0.0,
            "approved_good": 0, "approved_bad": 0,
            "rejected_good": int(tolak_lunas.sum()),
            "rejected_bad": int(tolak_gagal.sum()),
            "good_rejected_per_bad_avoided": None,
        }

    exposure = float(e[disetujui].sum())

    # Perkiraan kerugian dari model (PD x LGD x EAD). Dilaporkan karena
    # ini metrik standar, tapi TIDAK dipakai memilih garis -- kita tahu
    # PD model meleset.
    expected_loss = float((p[disetujui] * e[disetujui] * lgd).sum())

    # Uang yang benar-benar masuk dan keluar, dari kejadian sebenarnya
    uang_masuk = float(r[setuju_lunas].sum())
    uang_keluar = float((e[setuju_gagal] * lgd).sum())
    untung_bersih = uang_masuk - uang_keluar

    n_tolak_gagal = int(tolak_gagal.sum())
    rasio = int(tolak_lunas.sum()) / n_tolak_gagal if n_tolak_gagal > 0 else None

    return {
        "cutoff": round(cutoff, 4),
        "approval_rate": round(n_setuju / len(p), 4),
        "n_approved": n_setuju,
        "exposure": round(exposure, 2),
        "default_rate": round(float(gagal[disetujui].mean()), 4),
        "expected_loss": round(expected_loss, 2),
        "el_pct_exposure": round(expected_loss / exposure, 4),
        "income": round(uang_masuk, 2),
        "realized_loss": round(uang_keluar, 2),
        "net_profit": round(untung_bersih, 2),
        "approved_good": int(setuju_lunas.sum()),
        "approved_bad": int(setuju_gagal.sum()),
        "rejected_good": int(tolak_lunas.sum()),
        "rejected_bad": n_tolak_gagal,
        "good_rejected_per_bad_avoided": round(rasio, 2) if rasio else None,
    }


def sweep(pd_scores, y_true, ead, revenue, cfg: dict) -> list:
    """Hitung dampak untuk SEMUA garis batas, dari 5% sampai 60%.

    Hasilnya dipakai slider di aplikasi. Dihitung sekali di sini,
    lalu diunduh browser sekaligus -- jadi menggeser slider terasa
    seketika tanpa bolak-balik ke server.
    """
    s = cfg["policy"]["sweep"]
    lgd = cfg["policy"]["lgd_assumption"]

    garis = np.arange(s["start"], s["stop"] + s["step"] / 2, s["step"])
    return [evaluate_cutoff(pd_scores, y_true, ead, revenue, float(c), lgd) for c in garis]


def choose_cutoff(tabel: list, max_default_rate: float) -> dict:
    """Pilih garis batas: paling untung di antara yang aman.

    Mengembalikan tiga hal:
      puncak    garis paling untung, tanpa peduli risiko
      terpilih  garis paling untung yang memenuhi batas risiko
      skenario  1 = batas risiko yang menentukan
                2 = untung yang menentukan
    """
    ada_isi = [r for r in tabel if r["n_approved"] > 0]
    aman = [r for r in ada_isi if r["default_rate"] <= max_default_rate]

    if not aman:
        raise ValueError(
            f"Tidak ada garis batas yang memenuhi default rate <= {max_default_rate:.0%}. "
            f"Longgarkan batas risiko di config.yaml."
        )

    puncak = max(ada_isi, key=lambda r: r["net_profit"])
    terpilih = max(aman, key=lambda r: r["net_profit"])

    # Kalau puncaknya melanggar batas, batas risiko yang menentukan.
    skenario = 1 if puncak["default_rate"] > max_default_rate else 2

    return {"puncak": puncak, "terpilih": terpilih, "skenario": skenario}


def lgd_sensitivity(pd_scores, y_true, ead, revenue, cutoff: float, cfg: dict) -> list:
    """Uji seberapa berubah untung bila asumsi LGD diganti.

    LGD tidak bisa dihitung dari dataset ini, jadi diuji pada
    beberapa kemungkinan -- bukan dipakai satu angka seolah pasti.
    """
    hasil = []
    for lgd in cfg["policy"]["lgd_sensitivity"]:
        r = evaluate_cutoff(pd_scores, y_true, ead, revenue, cutoff, lgd)
        hasil.append({
            "lgd": lgd,
            "realized_loss": r["realized_loss"],
            "net_profit": r["net_profit"],
        })
    return hasil