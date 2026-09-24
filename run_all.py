"""Jalankan seluruh pipeline dari awal sampai akhir.

Pengganti Makefile. Makefile adalah alat baris perintah yang tidak
tersedia di Windows, jadi dipakai script Python biasa yang bisa
dijalankan dengan tombol Run di VS Code.

Tahap 1 (memuat CSV ke database) butuh sekitar 4 menit dan jarang perlu
diulang -- datanya tidak berubah. Jadi bawaannya dilewati. Ubah
MUAT_ULANG_CSV jadi True kalau file CSV-nya diganti atau tabel bronze
terhapus.
"""
import time
from importlib import import_module

MUAT_ULANG_CSV = False

TAHAP = [
    ("p1_ingest", "CSV ke tabel bronze", True),
    ("p2_clean", "bronze ke tabel silver", False),
    ("p3_train", "pilih fitur, latih model, koreksi kalibrasi", False),
    ("p4_policy", "tentukan garis batas dan hitung uangnya", False),
    ("p5_export", "siapkan bahan pembanding dan uji artefak", False),
]


def main():
    mulai = time.time()
    dijalankan, dilewati = [], []

    for nama, keterangan, berat in TAHAP:
        if berat and not MUAT_ULANG_CSV:
            dilewati.append(nama)
            print(f"[lewat ] {nama:<12} {keterangan}")
            continue

        print(f"\n{'=' * 70}")
        print(f"[jalan ] {nama:<12} {keterangan}")
        print("=" * 70)

        t = time.time()
        import_module(f"src.pipeline.{nama}").main()
        lama = time.time() - t
        dijalankan.append((nama, lama))
        print(f"\n[selesai] {nama} dalam {lama:.0f} detik")

    print(f"\n{'=' * 70}")
    print("RINGKASAN")
    print("=" * 70)
    for nama, lama in dijalankan:
        print(f"  {nama:<12} {lama:>6.0f} detik")
    if dilewati:
        print(f"  dilewati: {', '.join(dilewati)}")
    print(f"\nTotal {time.time() - mulai:.0f} detik.")


if __name__ == "__main__":
    main()