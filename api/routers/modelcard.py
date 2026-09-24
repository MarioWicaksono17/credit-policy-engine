"""Halaman 3 -- Model card.

Menjawab: "alat ini bisa dipercaya sampai mana?"

Isinya dirangkum dari metrics.json, feature_selection.json, dan
policy.json, lalu disusun jadi satu jawaban yang siap ditampilkan.

Di bank, dokumen seperti ini wajib ada untuk setiap model kredit, dan
diperiksa unit validasi yang terpisah dari pembuat model.
"""
from fastapi import APIRouter

from api.artifacts import get

router = APIRouter(prefix="/api/model", tags=["Model card"])


@router.get("/card", summary="Isi model card")
def card():
    """Identitas model, hasil validasi, variabel, dan batas penggunaannya."""
    a = get()
    m, cfg = a.metrics, a.cfg
    juara = m["results"]["champion"]
    terkoreksi = m["results"].get("champion_calibrated", juara)

    # Variabel yang dipakai, beserta kekuatan dan arah pengaruhnya.
    #
    # Kolom kategori dipecah model menjadi beberapa kolom 0/1 -- misalnya
    # purpose_small_business. Di sini dikembalikan ke nama manusianya,
    # jadi yang tampil "Tujuan pinjaman: Usaha kecil".
    nama = a.labels.get("features", {})
    nilai_nama = a.labels.get("values", {})
    kategori = a.meta["categorical"]

    dipakai = []
    for b in m["coefficients"]:
        dasar = next((k for k in kategori if b["feature"].startswith(k + "_")),
                     b["feature"])
        tingkat = b["feature"][len(dasar) + 1:] if dasar != b["feature"] else None
        label = nama.get(dasar, dasar)
        if tingkat:
            label += ": " + nilai_nama.get(dasar, {}).get(tingkat, tingkat)

        dipakai.append({**b, "base": dasar, "level": tingkat, "label": label,
                        "direction": "naik" if b["coef"] > 0 else "turun"})

    # Diurutkan menurut Information Value, bukan besar koefisien.
    #
    # Koefisien kategori tidak bisa dibandingkan dengan koefisien angka:
    # yang satu berlaku untuk semua pemohon, yang lain hanya untuk sebagian
    # kecil. Tujuan pinjaman "usaha kecil" koefisiennya +1,13 -- terbesar --
    # padahal hanya menyangkut 1% pemohon dan IV-nya paling rendah.
    # Mengurutkan menurut koefisien membuatnya terlihat paling penting.
    dipakai.sort(key=lambda b: (-(b["iv"] if b["iv"] == b["iv"] else 0),
                                -abs(b["coef"])))

    # Variabel yang dibuang, dikelompokkan menurut alasannya
    dibuang = {}
    for f in a.selection["features"]:
        if f["status"] == "dibuang":
            kunci = f["reason"].split(" ")[0]
            label = {"IV": "Tidak membedakan pemohon",
                     "kembar": "Kembar dengan variabel lain",
                     "di": "Di luar batas jumlah",
                     "arah": "Arah pengaruh tidak masuk akal"}.get(kunci, kunci)
            dibuang.setdefault(label, []).append(
                {"feature": f["feature"], "label": nama.get(f["feature"], f["feature"]),
                 "iv": f["iv"], "reason": f["reason"]})

    return {
        "identity": {
            "name": cfg["project"],
            "version": cfg["model_version"],
            "type": "Application scorecard",
            "algorithm": m["champion"],
            "product": f"Pinjaman konsumen tanpa agunan, tenor "
                       f"{cfg['filters']['term_months']} bulan",
            "default_definition": "Charged off, sekitar 120 hari menunggak",
            "horizon": "Seumur pinjaman",
            "train_years": cfg["split"]["train_years"],
            "validation_years": cfg["split"]["validation_years"],
            "test_years": cfg["split"]["test_years"],
            "n_train": m["split_sizes"]["train"],
            "generated_at": m["generated_at"],
        },
        "validation": {
            # Diskriminasi: apakah URUTAN risikonya benar
            "discrimination": {
                "auc": juara["oot_test"]["auc"],
                "ks": juara["oot_test"]["ks"],
                "gini": juara["oot_test"]["gini"],
                "stable_over_time": juara["oot_test"]["auc"] == terkoreksi["oot_test"]["auc"],
            },
            # Kalibrasi: apakah ANGKA PD-nya sesuai kenyataan
            "calibration": {
                "gap_pp_before": juara["oot_test"]["calibration_gap_pp"],
                "gap_pp_after": terkoreksi["oot_test"]["calibration_gap_pp"],
                "offset": m["calibration"]["offset"],
                "fit_on": m["calibration"]["fit_on"],
                "mean_predicted": terkoreksi["oot_test"]["mean_predicted"],
                "actual_rate": terkoreksi["oot_test"]["actual_rate"],
            },
            "comparisons": {
                nama_model: r["oot_test"] for nama_model, r in m["results"].items()
            },
            "random_split_benchmark": juara.get("random_test"),
            "by_vintage": m["diagnostics"].get("by_vintage_calibrated",
                                               m["diagnostics"]["by_vintage"]),
            "calibration_deciles": m["diagnostics"]["calibration_deciles"],
        },
        "features": {
            "n_candidates": a.selection["n_candidates"],
            "n_selected": a.selection["n_selected"],
            "rules": a.selection["rules"],
            "used": dipakai,
            "dropped": dibuang,
            "excluded_by_design": {
                "pricing": cfg["columns"]["benchmark"],
                "reason": "Penilaian risiko originator, bukan karakteristik pemohon, "
                          "dan belum ada saat keputusan kredit diambil",
            },
        },
        "limitations": {
            "can_be_used_for": [
                "Mengurutkan pemohon dari yang paling aman",
                "Keputusan terima-tolak",
                "Memberi alasan penolakan",
                "Simulasi kebijakan kredit",
            ],
            "cannot_be_used_for": [
                "Menghitung cadangan kerugian tanpa koreksi dan margin kehati-hatian",
                f"Pinjaman selain tenor {cfg['filters']['term_months']} bulan",
                "Pengajuan bersama",
                "Produk kredit lain seperti KPR atau kartu kredit",
            ],
            "data_limitations": [
                "Hanya berisi pemohon yang disetujui, tidak ada data yang ditolak",
                "Tidak ada variabel kondisi ekonomi",
                "Definisi gagal bayar seumur pinjaman, bukan 12 bulan seperti Basel",
                "Data Amerika 2013-2015, tidak mewakili pemohon Indonesia",
            ],
            "policy_review_needed": not a.policy["holds_on_test"],
        },
    }