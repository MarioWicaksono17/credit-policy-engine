"""Menilai satu pemohon, lalu menjelaskan kenapa hasilnya begitu.

Di tahap sebelumnya kita menilai ratusan ribu pinjaman sekaligus untuk
mengukur mutu model. File ini kebalikannya: satu pemohon, dengan
penjelasan lengkap.

Inilah yang membuat Logistic Regression dipilih. Rumusnya berbentuk
penjumlahan, jadi pengaruh setiap variabel bisa dipisah dan dihitung
persis:

    log-odds = intercept
             + (koefisien_1 x nilai_1)
             + (koefisien_2 x nilai_2)
             + ...

Setiap suku dalam penjumlahan itu adalah sumbangan satu variabel
terhadap risiko. Tinggal diurutkan, dan yang terbesar menjadi alasan
penolakan.

Hasilnya PASTI dan BISA DILACAK: data yang sama selalu menghasilkan
alasan yang sama, dan setiap alasan bisa ditunjuk asal angkanya. Model
seperti Gradient Boosting tidak bisa memberikan ini.

Satu hal penting soal cara membacanya: nilai setiap variabel sudah
diseragamkan terhadap RATA-RATA PEMOHON di data latih. Jadi sumbangan
positif berarti "lebih berisiko dibanding pemohon rata-rata", bukan
"berisiko" secara mutlak.
"""
import numpy as np
import pandas as pd

from src.calibration import apply_offset


# ---------------------------------------------------------------------
# Melengkapi isian
# ---------------------------------------------------------------------
def fill_defaults(app: dict, reference: dict, meta: dict) -> dict:
    """Lengkapi isian yang kosong dengan nilai pemohon rata-rata.

    Formulir di aplikasi hanya menanyakan sebagian variabel -- tidak
    mungkin meminta pemohon mengisi 19 kolom. Sisanya diisi nilai tengah
    dari data latih, dan karena nilai tengah berarti "rata-rata", variabel
    itu tidak akan muncul sebagai alasan penolakan.
    """
    lengkap = dict(reference["defaults"])
    lengkap.update({k: v for k, v in app.items() if v is not None})
    return {k: lengkap[k] for k in meta["numeric"] + meta["categorical"]}


def to_frame(app: dict, meta: dict) -> pd.DataFrame:
    """Ubah satu pemohon menjadi tabel satu baris, urutan kolom sesuai model."""
    return pd.DataFrame([app])[meta["numeric"] + meta["categorical"]]


# ---------------------------------------------------------------------
# Menghitung sumbangan tiap variabel
# ---------------------------------------------------------------------
def category_baselines(model, meta: dict, reference: dict) -> dict:
    """Sumbangan RATA-RATA setiap variabel kategori di seluruh populasi.

    Kenapa ini perlu. Variabel angka sudah diseragamkan terhadap rata-rata
    pemohon, jadi nilai rata-rata menghasilkan sumbangan nol. Variabel
    kategori tidak begitu: model membandingkannya dengan satu kategori
    acuan yang dipilih otomatis menurut abjad.

    Akibatnya kategori paling umum bisa muncul sebagai alasan penolakan,
    padahal mayoritas pemohon ada di situ. Itu alasan yang tidak masuk akal
    untuk disampaikan ke pemohon.

    Fungsi ini menghitung rata-rata tertimbang sumbangan tiap kategori,
    memakai porsi populasi di data latih. Angka itu lalu dikurangkan,
    sehingga kategori paling umum mendekati nol -- sama seperti variabel
    angka yang nilainya rata-rata.
    """
    nama = list(model[:-1].get_feature_names_out())
    koef = model[-1].coef_[0]

    dasar = {}
    for f in meta["categorical"]:
        porsi = reference["categorical"].get(f, {}).get("shares", {})
        rata = 0.0
        for nilai, bagian in porsi.items():
            kolom = f"cat__{f}_{nilai}"
            # Kategori acuan tidak punya kolom sendiri, sumbangannya nol
            if kolom in nama:
                rata += bagian * float(koef[nama.index(kolom)])
        dasar[f] = rata
    return dasar


def contributions(model, meta: dict, app: dict, baselines: dict = None) -> tuple:
    """Pecah risiko pemohon menjadi sumbangan per variabel.

    Mengembalikan (pd_mentah, daftar_sumbangan).

    Kolom kategori dipecah model menjadi beberapa kolom 0/1 -- misalnya
    purpose_small_business. Sumbangannya dikembalikan ke nama aslinya,
    supaya yang tampil "Tujuan pinjaman", bukan nama teknis.
    """
    X = to_frame(app, meta)
    Z = model[:-1].transform(X)[0]           # nilai setelah diseragamkan
    nama = list(model[:-1].get_feature_names_out())
    koef = model[-1].coef_[0]
    intercept = float(model[-1].intercept_[0])

    kategori = meta["categorical"]
    kumpul = {}
    for n, z, c in zip(nama, Z, koef):
        jenis, _, kolom = n.partition("__")
        if jenis == "cat":
            kolom = next((k for k in kategori if kolom.startswith(k + "_")), kolom)
        kumpul[kolom] = kumpul.get(kolom, 0.0) + float(z * c)

    log_odds = intercept + sum(kumpul.values())
    pd_mentah = float(1 / (1 + np.exp(-log_odds)))

    # Sumbangan kategori digeser supaya dibandingkan dengan pemohon
    # rata-rata, bukan dengan kategori acuan. PD tidak ikut berubah --
    # yang bergeser hanya cara membaca sumbangannya.
    if baselines:
        for f, rata in baselines.items():
            if f in kumpul:
                kumpul[f] -= rata

    daftar = [{"feature": k, "contribution": round(v, 4)} for k, v in kumpul.items()]
    daftar.sort(key=lambda b: -b["contribution"])
    return pd_mentah, daftar


# ---------------------------------------------------------------------
# Menjelaskan dalam bahasa manusia
# ---------------------------------------------------------------------
def percentile_of(value: float, quantiles: list) -> int:
    """Posisi sebuah nilai di antara pemohon lain, dalam persen.

    Hasil 80 berarti: nilai pemohon ini lebih tinggi dari 80% pemohon
    di data latih.
    """
    q = np.asarray(quantiles, dtype=float)
    return int(np.searchsorted(q, float(value), side="right"))


def describe(feature: str, value, reference: dict, labels: dict) -> str:
    """Susun satu kalimat alasan, lengkap dengan pembandingnya."""
    nama = labels.get("features", {}).get(feature, feature)

    if feature in reference["categorical"]:
        arti = labels.get("values", {}).get(feature, {}).get(str(value), str(value))
        porsi = reference["categorical"][feature]["shares"].get(str(value))
        tambahan = f", {porsi:.0%} pemohon" if porsi else ""
        return f"{nama}: {arti}{tambahan}"

    stat = reference["numeric"][feature]
    p = percentile_of(value, stat["quantiles"])

    # Di ujung sebaran, letak terhadap nilai tengah dan terhadap rata-rata
    # sejalan, jadi kalimat persentil aman dipakai.
    if p >= 90:
        return f"{nama} tertinggi 10% populasi"
    if p >= 75:
        return f"{nama} kuartil tertinggi populasi"
    if p <= 10:
        return f"{nama} terendah 10% populasi"
    if p <= 25:
        return f"{nama} kuartil terendah populasi"

    # Di tengah sebaran keduanya bisa bertentangan. Contohnya penghasilan:
    # segelintir orang berpenghasilan sangat besar menarik rata-rata ke
    # atas, sehingga orang di persentil 51 justru ADA DI BAWAH rata-rata.
    # Model membandingkan dengan rata-rata, jadi kalimatnya harus begitu
    # juga -- kalau tidak, kalimat dan angkanya saling bertentangan.
    rata, sebar = stat.get("mean"), stat.get("std")
    if rata is None or not sebar:
        return f"{nama} di sekitar tengah populasi"

    jarak = (float(value) - rata) / sebar
    if abs(jarak) < 0.25:
        return f"{nama} mendekati rata-rata pemohon"
    return f"{nama} {'di atas' if jarak > 0 else 'di bawah'} rata-rata pemohon"


# ---------------------------------------------------------------------
# Penilaian lengkap
# ---------------------------------------------------------------------
def assess(app: dict, model, meta: dict, reference: dict, cutoff: float,
           labels: dict, top_n: int = 4) -> dict:
    """Nilai satu pemohon: keputusan, PD, dan alasannya."""
    lengkap = fill_defaults(app, reference, meta)
    dasar_kategori = category_baselines(model, meta, reference)
    pd_mentah, sumbangan = contributions(model, meta, lengkap, dasar_kategori)

    # PD dikoreksi dengan penggeser yang dihitung di p3 dari data validasi
    pd_akhir = float(apply_offset(pd_mentah, meta.get("calibration_offset", 0.0)))
    disetujui = pd_akhir < cutoff

    for b in sumbangan:
        b["value"] = lengkap[b["feature"]]
        b["label"] = labels.get("features", {}).get(b["feature"], b["feature"])
        b["reason"] = describe(b["feature"], b["value"], reference, labels)

    # Alasan penolakan hanya disusun kalau pemohonnya memang DITOLAK.
    # Untuk yang disetujui tidak ada alasan yang perlu disampaikan, dan
    # memberi label "alasan" pada penyimpangan kecil justru menyesatkan.
    #
    # Yang diambil juga hanya alasan yang benar-benar menentukan: minimal
    # seperlima dari faktor terbesar. Tanpa batas ini, faktor bernilai
    # +0,04 bisa ikut tampil sebagai alasan di samping faktor +0,32.
    penaik = []
    if not disetujui:
        naik = [b for b in sumbangan if b["contribution"] > 0]
        if naik:
            ambang = naik[0]["contribution"] * 0.2
            penaik = [b for b in naik if b["contribution"] >= ambang][:top_n]

    return {
        "pd": round(pd_akhir, 4),
        "pd_uncalibrated": round(pd_mentah, 4),
        "cutoff": cutoff,
        "approved": bool(disetujui),
        "decision": "Disetujui" if disetujui else "Ditolak",
        "reason_codes": [
            {"code": f"RC{i + 1}", **b} for i, b in enumerate(penaik)
        ],
        "contributions": sumbangan,
        "application": lengkap,
    }


def apply_scenarios(app: dict, model, meta: dict, reference: dict,
                    cutoff: float, scenarios: list) -> list:
    """Hitung ulang PD untuk beberapa tawaran alternatif.

    Di bank ini disebut counter-offer: pemohon yang ditolak tidak langsung
    dilepas, tapi ditawari bentuk lain -- plafon lebih kecil, misalnya.
    """
    dasar = fill_defaults(app, reference, meta)
    hasil = []

    for s in scenarios:
        ubah = dict(dasar)
        for kolom, aturan in s["changes"].items():
            if kolom not in ubah:
                continue
            if "multiply" in aturan:
                ubah[kolom] = float(ubah[kolom]) * aturan["multiply"]
            if "set_max" in aturan:
                ubah[kolom] = min(float(ubah[kolom]), aturan["set_max"])
            if "set" in aturan:
                ubah[kolom] = aturan["set"]

        p_mentah, _ = contributions(model, meta, ubah)
        p = float(apply_offset(p_mentah, meta.get("calibration_offset", 0.0)))
        hasil.append({
            "name": s["name"],
            # Kalau tidak ada satu pun variabel yang diubah termasuk fitur
            # model, skenario ini tidak akan mengubah PD sama sekali.
            "affects_model": any(k in dasar for k in s["changes"]),
            "pd": round(p, 4),
            "approved": bool(p < cutoff),
            "decision": "Terima" if p < cutoff else "Tolak",
        })

    return hasil