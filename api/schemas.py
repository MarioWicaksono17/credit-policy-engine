"""Bentuk data yang masuk dan keluar dari API.

Dipakai untuk dua hal:

  1. MEMERIKSA. Kalau halaman web mengirim data yang salah bentuk --
     misalnya penghasilan berupa teks -- API menolaknya dengan pesan
     jelas, bukan error yang membingungkan.

  2. MENDOKUMENTASIKAN. FastAPI membaca bentuk ini dan membuat halaman
     dokumentasi otomatis di /docs, lengkap dengan contoh dan tombol
     untuk mencoba. Tidak ada dokumentasi yang perlu ditulis manual.
"""
from typing import Dict, List, Optional, Union

from pydantic import BaseModel, Field


class ScoreRequest(BaseModel):
    """Data pemohon yang dikirim dari halaman Penilaian aplikasi."""

    application: Dict[str, Union[float, int, str, None]] = Field(
        default_factory=dict,
        description="Isian formulir. Yang tidak diisi memakai nilai pemohon rata-rata.",
    )
    cutoff: Optional[float] = Field(
        default=None,
        ge=0.0, le=1.0,
        description="Garis batas untuk simulasi. Kosongkan untuk memakai yang berlaku.",
    )


class ReasonCode(BaseModel):
    """Satu alasan yang paling menentukan hasil penilaian."""
    code: str
    feature: str
    label: str
    value: Union[float, int, str, None]
    contribution: float
    reason: str


class Scenario(BaseModel):
    """Hasil satu tawaran alternatif."""
    name: str
    pd: float
    approved: bool
    decision: str
    affects_model: bool


class ScoreResponse(BaseModel):
    """Jawaban lengkap untuk satu pemohon."""
    pd: float
    pd_uncalibrated: float
    cutoff: float
    approved: bool
    decision: str
    reason_codes: List[ReasonCode]
    contributions: List[dict]
    scenarios: List[Scenario]
    application: dict


class FormField(BaseModel):
    """Satu isian di formulir, lengkap dengan batas dan nilai bawaannya."""
    name: str
    label: str
    type: str                      # "angka" atau "pilihan"
    default: Union[float, int, str]
    min: Optional[float] = None
    max: Optional[float] = None
    p25: Optional[float] = None
    median: Optional[float] = None
    p75: Optional[float] = None
    options: Optional[List[dict]] = None