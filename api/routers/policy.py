"""Halaman 2 -- Kebijakan kredit.

Menjawab: "di mana garis batasnya, dan berapa harganya?"

Dua alamat:
  GET /api/policy/sweep    dampak SEMUA garis batas, untuk slider
  GET /api/policy/summary  angka kebijakan yang berlaku
"""
from fastapi import APIRouter

from api.artifacts import get

router = APIRouter(prefix="/api/policy", tags=["Kebijakan kredit"])


@router.get("/sweep", summary="Dampak semua garis batas")
def sweep():
    """Seluruh tabel garis batas sekaligus, dari 2% sampai 40%.

    Dikirim sekali, lalu disimpan browser. Saat pengguna menggeser
    slider, halaman web tinggal mengambil baris yang sesuai dari tabel
    yang sudah ada -- tidak perlu bertanya lagi ke server.

    Itu sebabnya slider terasa seketika.
    """
    a = get()
    return {
        "model_version": a.policy["model_version"],
        "evaluated_on": a.policy["evaluated_on"],
        "n_total": a.policy["n_total"],
        "risk_appetite": a.policy["risk_appetite"],
        "chosen_cutoff": a.policy["chosen_cutoff"],
        "loss_parameters": a.policy["loss_parameters"],
        "rows": a.policy["sweep"],
    }


@router.get("/summary", summary="Kebijakan yang berlaku")
def summary():
    """Angka kebijakan yang sedang berlaku, beserta cara memilihnya.

    Termasuk hal yang jarang ditampilkan: berapa pemohon baik yang ikut
    ditolak, dan seberapa tebal bantalannya kalau kerugian membesar.
    """
    a = get()
    p = a.policy
    aktif = p["active"]

    return {
        "chosen_cutoff": p["chosen_cutoff"],
        "chosen_on": p["chosen_on"],
        "evaluated_on": p["evaluated_on"],
        "risk_appetite": p["risk_appetite"],
        "holds_on_test": p["holds_on_test"],
        "scenario": p["scenario"],
        "selection": p["selection"],
        "active": aktif,
        "loss_parameters": p["loss_parameters"],
        "stress_test": p["stress_test"],
        # Selisih antara perkiraan model dan kerugian sebenarnya
        "loss_shortfall": {
            "expected": aktif["expected_loss"],
            "realized": aktif["realized_loss"],
            "gap": round(aktif["realized_loss"] - aktif["expected_loss"], 2),
            "gap_pct": round(
                (aktif["realized_loss"] - aktif["expected_loss"])
                / aktif["expected_loss"], 4) if aktif["expected_loss"] else None,
        },
    }