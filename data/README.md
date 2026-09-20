# Data

Dataset tidak disertakan dalam repositori karena ukurannya sekitar 100 MB.

## Cara mendapatkan

1. Unduh dari Kaggle: Lending Club Loan Data (`lending_club_loan_two.csv`)
2. Letakkan di `data/raw/lending_club_loan_two.csv`

## Isi

- 396.030 baris, 27 kolom
- Sudah tersaring ke pinjaman yang selesai: `Fully Paid` dan `Charged Off`
- Base default rate 19,6%
- Vintage 2007–2016

## Catatan penting

Dataset hanya memuat pinjaman yang **disetujui** Lending Club. Pemohon yang
ditolak tidak tercatat, sehingga model mengestimasi PD untuk populasi yang
sudah tersaring.

Hanya pinjaman yang sudah selesai yang tercatat. Vintage terbaru karenanya
hanya terwakili oleh pinjaman berdurasi pendek — default rate 2016 tampak
rendah bukan karena kualitas kredit membaik.