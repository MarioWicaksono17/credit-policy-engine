"""Halaman 1 -- Penilaian aplikasi.

Menjawab: "orang ini diterima atau ditolak, dan kenapa?"

Dua alamat:
  GET  /api/application/form   bentuk formulirnya seperti apa
  POST /api/application/score  nilai satu pemohon
"""
from fastapi import APIRouter, HTTPException

from api.artifacts import get
from api.schemas import FormField, ScoreRequest, ScoreResponse
from src.explain import apply_scenarios, assess

router = APIRouter(prefix="/api/application", tags=["Penilaian aplikasi"])


@router.get("/form", response_model=list[FormField], summary="Bentuk formulir")
def form():
    """Daftar isian formulir beserta batas dan nilai bawaannya.

    Halaman web memakai ini untuk membangun formulirnya sendiri. Jadi
    kalau daftar variabel di config diubah, formulirnya ikut berubah --
    tidak ada nama variabel yang ditulis tangan di sisi tampilan.

    Nilai bawaan tiap isian adalah nilai tengah pemohon di data latih,
    supaya pengguna tidak mulai dari formulir kosong.
    """
    a = get()
    nama_label = a.labels.get("features", {})
    nama_pilihan = a.labels.get("values", {})
    hasil = []

    for f in a.form_fields:
        if f in a.meta["categorical"]:
            pilihan = a.reference["categorical"][f]
            hasil.append(FormField(
                name=f,
                label=nama_label.get(f, f),
                type="pilihan",
                default=a.reference["defaults"][f],
                options=[{"value": v,
                          "label": nama_pilihan.get(f, {}).get(v, v),
                          "share": pilihan["shares"].get(v)}
                         for v in pilihan["values"]],
            ))
        else:
            s = a.reference["numeric"][f]
            hasil.append(FormField(
                name=f, label=nama_label.get(f, f), type="angka",
                default=s["median"], min=s["min"], max=s["max"],
                p25=s["p25"], median=s["median"], p75=s["p75"],
            ))

    return hasil


@router.post("/score", response_model=ScoreResponse, summary="Nilai satu pemohon")
def score(req: ScoreRequest):
    """Hitung PD, keputusan, alasan penentu, dan tawaran alternatif.

    Isian yang tidak dikirim diisi nilai pemohon rata-rata. Karena
    nilainya rata-rata, variabel itu tidak akan muncul sebagai alasan.

    Parameter cutoff hanya untuk simulasi. Tanpa itu, dipakai garis batas
    yang berlaku dari policy.json.
    """
    a = get()

    asing = [k for k in req.application if k not in a.features]
    if asing:
        raise HTTPException(
            status_code=400,
            detail=f"Variabel tidak dikenali: {asing}. "
                   f"Lihat /api/application/form untuk daftar yang benar.",
        )

    garis = req.cutoff if req.cutoff is not None else a.cutoff

    hasil = assess(req.application, a.model, a.meta, a.reference, garis, a.labels)
    hasil["scenarios"] = apply_scenarios(
        req.application, a.model, a.meta, a.reference, garis, a.scenarios
    )
    return hasil