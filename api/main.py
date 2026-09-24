"""Titik masuk API.

Satu program ini melayani dua hal sekaligus:
  - menjawab pertanyaan dari halaman web (alamat berawalan /api/)
  - menyajikan halaman webnya sendiri (folder web/)

Kenapa digabung: cukup satu program yang berjalan di server, dan halaman
web memanggil API di alamat yang sama. Tidak ada urusan izin lintas
alamat, dan biaya server jauh lebih murah.

Cara menjalankan: buka file ini di VS Code, klik Run. Lalu buka
http://127.0.0.1:8000 di browser.
"""
import sys
from contextlib import asynccontextmanager
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from api.artifacts import get
from api.routers import application, modelcard, policy

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "web"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Muat artefak SEKALI saat program dinyalakan.

    Kalau artefaknya belum ada atau rusak, program gagal di sini --
    bukan nanti saat pengguna pertama membuka halaman.
    """
    a = get()
    print(f"Artefak dimuat: model {a.meta['model_version']}, "
          f"{len(a.features)} fitur, garis batas {a.cutoff:.0%}")
    if a.form_skipped:
        print(f"Catatan: isian formulir dilewati karena bukan fitur model: "
              f"{a.form_skipped}")
    yield


app = FastAPI(
    title="Credit Policy Engine",
    description="Application scorecard dan simulasi kebijakan kredit "
                "untuk pinjaman konsumen tanpa agunan tenor 36 bulan.",
    version="2.0",
    lifespan=lifespan,
)

# Diperlukan saat halaman web masih dibuka dari file lokal waktu
# pengembangan. Setelah digabung dalam satu program, ini tidak terpakai.
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],
)

app.include_router(application.router)
app.include_router(policy.router)
app.include_router(modelcard.router)


@app.get("/api/health", tags=["Pemeriksaan"], summary="Cek program hidup")
def health():
    """Dipakai server untuk memastikan program masih berjalan."""
    a = get()
    return {
        "status": "ok",
        "model_version": a.meta["model_version"],
        "n_features": len(a.features),
        "cutoff": a.cutoff,
    }


# Halaman web disajikan dari folder web/. Dibuat di Langkah 7 --
# sebelum itu, alamat utama diarahkan ke dokumentasi API.
if WEB.exists() and (WEB / "index.html").exists():
    app.mount("/", StaticFiles(directory=str(WEB), html=True), name="web")
else:
    @app.get("/", include_in_schema=False)
    def beranda():
        return RedirectResponse("/docs")


if __name__ == "__main__":
    uvicorn.run("api.main:app", host="127.0.0.1", port=8000, reload=False)