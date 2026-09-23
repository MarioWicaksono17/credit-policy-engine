"""Kebijakan kredit: mengubah angka PD menjadi keputusan.

Model menghasilkan PD. PD belum keputusan -- baru jadi keputusan setelah
ditarik garis batas. Menarik garis adalah keputusan bisnis, bukan
keputusan statistik, jadi file ini terpisah dari model.py.

Yang berbeda dari versi pertama: seluruh angka uang di sini berasal dari
data, bukan asumsi.

  LGD dan EAD   dihitung dari data penagihan, diambil dari DATA LATIH lalu
                diterapkan ke depan -- sama seperti model itu sendiri.
                Untuk pemohon baru kita belum tahu berapa yang akan hilang;
                yang bisa dipakai hanya pengalaman masa lalu.

  Untung        dari net_cash, yaitu uang yang benar-benar kembali
                dikurangi uang yang keluar. Tidak ada asumsi margin.

Jadi ada dua angka kerugian yang bisa dibandingkan:
  expected_loss   perkiraan model  = PD x LGD x EAD
  realized_loss   kenyataan        = yang benar-benar hilang
Selisih keduanya menunjukkan akibat nyata dari PD yang meleset.
"""
import numpy as np
import pandas as pd

TARGET = "default_flag"


def loss_parameters(train: pd.DataFrame) -> dict:
    """Perkirakan LGD dan EAD dari data latih.

    lgd        rata-rata porsi yang hilang dari sisa pinjaman
    ead_ratio  rata-rata sisa pinjaman saat gagal bayar, sebagai porsi
               dari jumlah yang dipinjamkan

    Keduanya dihitung HANYA dari pinjaman yang gagal bayar di data latih.
    """
    gagal = train[train[TARGET] == 1]
    return {
        "lgd": float(gagal["lgd"].mean()),
        "ead_ratio": float((gagal["ead"] / gagal["funded_amnt"]).mean()),
        "n_default": int(len(gagal)),
    }


def decide(pd_scores, cutoff: float) -> np.ndarray:
    """Terapkan garis batas. True artinya disetujui."""
    return np.asarray(pd_scores, dtype=float) < cutoff


def evaluate_cutoff(df: pd.DataFrame, pd_scores, cutoff: float, params: dict) -> dict:
    """Hitung seluruh dampak dari satu garis batas."""
    p = np.asarray(pd_scores, dtype=float)
    setuju = decide(p, cutoff)
    gagal = df[TARGET].values.astype(bool)

    kotak = {
        "approved_good": int((setuju & ~gagal).sum()),
        "approved_bad": int((setuju & gagal).sum()),
        "rejected_good": int((~setuju & ~gagal).sum()),
        "rejected_bad": int((~setuju & gagal).sum()),
    }
    n_setuju = int(setuju.sum())

    if n_setuju == 0:
        return {"cutoff": round(cutoff, 4), "approval_rate": 0.0, "n_approved": 0,
                "exposure": 0.0, "default_rate": None, "expected_loss": 0.0,
                "realized_loss": 0.0, "contribution": 0.0,
                **kotak, "good_rejected_per_bad_avoided": None}

    dana = df["funded_amnt"].values

    # Perkiraan model: PD x LGD x EAD, memakai LGD dan EAD dari data latih
    perkiraan = float((p[setuju] * params["lgd"] * params["ead_ratio"]
                       * dana[setuju]).sum())

    # Kenyataan: sisa pinjaman dikali porsi yang benar-benar hilang
    rugi_baris = (df["ead"] * df["lgd"]).fillna(0).values
    kenyataan = float(rugi_baris[setuju].sum())

    # Untung: uang yang kembali dikurangi uang yang keluar
    kontribusi = float(df["net_cash"].values[setuju].sum())

    rasio = (kotak["rejected_good"] / kotak["rejected_bad"]
             if kotak["rejected_bad"] > 0 else None)

    return {
        "cutoff": round(cutoff, 4),
        "approval_rate": round(n_setuju / len(p), 4),
        "n_approved": n_setuju,
        "exposure": round(float(dana[setuju].sum()), 2),
        "default_rate": round(float(gagal[setuju].mean()), 4),
        "expected_loss": round(perkiraan, 2),
        "realized_loss": round(kenyataan, 2),
        "contribution": round(kontribusi, 2),
        **kotak,
        "good_rejected_per_bad_avoided": round(rasio, 2) if rasio else None,
    }


def sweep(df: pd.DataFrame, pd_scores, cfg: dict, params: dict) -> list:
    """Hitung dampak untuk SEMUA garis batas yang mungkin.

    Hasilnya dipakai slider di halaman Kebijakan kredit: seluruh tabel
    dihitung sekali di sini, lalu dibaca browser sekaligus, supaya
    menggeser slider terasa seketika.
    """
    s = cfg["policy"]["sweep"]
    garis = np.arange(s["start"], s["stop"] + s["step"] / 2, s["step"])
    return [evaluate_cutoff(df, pd_scores, float(c), params) for c in garis]


def choose_cutoff(tabel: list, max_default_rate: float) -> dict:
    """Pilih garis paling menguntungkan di antara yang memenuhi batas risiko.

    puncak    garis paling untung, tanpa peduli risiko
    terpilih  garis paling untung yang masih memenuhi batas risiko
    skenario  1 = batas risiko yang menentukan
              2 = untung yang menentukan
    """
    ada = [r for r in tabel if r["n_approved"] > 0]
    aman = [r for r in ada if r["default_rate"] <= max_default_rate]
    if not aman:
        raise ValueError(
            f"Tidak ada garis batas dengan default rate di bawah "
            f"{max_default_rate:.0%}. Longgarkan batas risiko di config.yaml."
        )

    puncak = max(ada, key=lambda r: r["contribution"])
    terpilih = max(aman, key=lambda r: r["contribution"])
    return {
        "puncak": puncak,
        "terpilih": terpilih,
        "skenario": 1 if puncak["default_rate"] > max_default_rate else 2,
    }


def stress_test(df: pd.DataFrame, pd_scores, cutoff: float, pengali: list) -> tuple:
    """Seberapa tebal bantalannya kalau keadaan memburuk.

    Kerugian dikalikan beberapa kali lipat, lalu dilihat apakah kontribusi
    masih positif. Ini pertanyaan yang sebenarnya dijawab bank: bukan
    "berapa untungnya di tahun biasa", tapi "apakah masih bertahan di
    tahun terburuk".

    Angka pengali bukan ramalan. Sebagai acuan, di dataset ini default rate
    naik dari 12,3% (2013) ke 14,9% (2015) tanpa ada krisis besar.

    Mengembalikan (tabel, pengali_impas). Pengali impas adalah kelipatan
    kerugian yang membuat kontribusi tepat nol -- makin besar, makin tebal
    bantalannya.
    """
    setuju = decide(pd_scores, cutoff)
    rugi = float((df["ead"] * df["lgd"]).fillna(0).values[setuju].sum())
    kontribusi = float(df["net_cash"].values[setuju].sum())
    masuk = kontribusi + rugi                      # uang masuk sebelum kerugian

    tabel = [{"multiplier": x,
              "realized_loss": round(rugi * x, 2),
              "contribution": round(masuk - rugi * x, 2)} for x in pengali]

    impas = round(masuk / rugi, 2) if rugi > 0 else None
    return tabel, impas