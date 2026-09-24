"""Memuat artefak sekali saja, lalu menyimpannya di memori.

Inilah yang membuat aplikasi ringan. Model dan seluruh angka dibaca
SEKALI waktu program dinyalakan, lalu disimpan di memori. Setiap
pertanyaan yang masuk dijawab dari memori -- tidak membuka file lagi,
dan tidak menyentuh database sama sekali.

Akibatnya:
  - jawaban keluar dalam hitungan milidetik
  - server tidak perlu PostgreSQL terpasang
  - yang perlu diunggah ke server cuma sekitar 80 KB

Database tetap di laptop, dipakai hanya saat melatih ulang model.
"""
import json
from pathlib import Path

import joblib

from src.config import load

WAJIB = ["model.pkl", "feature_meta.json", "metrics.json",
         "policy.json", "reference.json", "feature_selection.json"]


class Artefak:
    """Seluruh bahan yang dibutuhkan aplikasi, disimpan di memori."""

    def __init__(self):
        self.cfg = load()
        art = self.cfg["_root"] / "artifacts"

        kurang = [f for f in WAJIB if not (art / f).exists()]
        if kurang:
            raise RuntimeError(
                f"Artefak belum lengkap: {kurang}. "
                f"Jalankan run_all.py lebih dulu."
            )

        baca = lambda nama: json.loads((art / nama).read_text(encoding="utf-8"))

        self.model = joblib.load(art / "model.pkl")
        self.meta = baca("feature_meta.json")
        self.metrics = baca("metrics.json")
        self.policy = baca("policy.json")
        self.reference = baca("reference.json")
        self.selection = baca("feature_selection.json")

        self.labels = self.cfg.get("labels", {})
        self.scenarios = self.cfg.get("scenarios", [])
        self.features = self.meta["numeric"] + self.meta["categorical"]
        self.cutoff = self.policy["chosen_cutoff"]

        # Variabel yang ditanyakan di formulir. Yang ternyata bukan fitur
        # model dilewati -- daftar di config aman diubah tanpa merusak API.
        diminta = self.cfg.get("form", {}).get("fields", [])
        self.form_fields = [f for f in diminta if f in self.features]
        self.form_skipped = [f for f in diminta if f not in self.features]


_artefak = None


def get() -> Artefak:
    """Ambil artefak yang sudah dimuat. Dimuat sekali di pemakaian pertama."""
    global _artefak
    if _artefak is None:
        _artefak = Artefak()
    return _artefak