# Keputusan Kolom — Dataset Lengkap Lending Club

Dataset: `accepted_2007_to_2018Q4.csv` (Kaggle, wordsforthewise)
Sumber keputusan: `LCDataDictionary.xlsx`, sheet `LoanStats` dan `browseNotes`

Dokumen ini menjelaskan nasib setiap kolom dari 151 kolom yang ada, beserta alasannya.

---

## Cara memilah: dua saringan

### Saringan 1 — Apakah informasinya ada SEBELUM keputusan kredit?

Kamus kolom Lending Club punya sheet bernama `browseNotes`: daftar informasi yang ditampilkan kepada investor **sebelum** sebuah pinjaman didanai.

Kalau sebuah kolom ada di daftar itu, informasinya tersedia saat keputusan diambil — boleh dipertimbangkan sebagai fitur. Kalau tidak ada, informasinya baru muncul setelah pinjaman berjalan — tidak boleh dilihat model.

Hasil pencocokan:

| | Jumlah kolom |
|---|---|
| Ada di `browseNotes` — tersedia sebelum pendanaan | 107 |
| Tidak ada — muncul setelah pinjaman berjalan | 44 |

Ini aturan yang bisa dipertanggungjawabkan, karena berasal dari dokumentasi Lending Club sendiri, bukan penilaian pribadi.

### Saringan 2 — Kalaupun tersedia, apakah layak dipakai?

Tersedia sebelum keputusan belum tentu boleh dipakai. Beberapa kolom lolos saringan pertama tetapi tetap dikeluarkan karena:

- merupakan **hasil penilaian risiko Lending Club sendiri** (grade, suku bunga)
- berupa **identitas atau teks bebas** yang tidak bisa diolah
- berupa **lokasi**, yang berisiko menjadi dasar diskriminasi
- merupakan **keputusan operasional platform**, bukan karakteristik pemohon
- hanya berlaku untuk **pengajuan bersama**, yang tidak kita pakai

---

## Ringkasan

| Kelompok | Jumlah | Artinya |
|---|---|---|
| **Fitur inti** | 27 | Dilihat model. Tersedia sejak awal. |
| **Fitur kandidat** | 50 | Boleh dilihat model, **tapi** kemungkinan baru ada di tahun-tahun belakangan. Perlu dicek dengan data. |
| **Pembanding** | 4 | Penilaian Lending Club sendiri. Tidak pernah dipakai model utama. |
| **Hasil** | 9 | Informasi setelah pencairan. Dipakai untuk menghitung target, EAD, LGD, dan untung. **Tidak pernah dilihat model.** |
| **Pengatur** | 3 | Kunci baris, tahun, dan penyaring. |
| **Buang** | 58 | Tidak dipakai sama sekali. |
| **Total** | **151** | |

---

## Tiga jebakan paling halus

### 1. Dua FICO yang namanya hampir sama

| Kolom | Arti | Keputusan |
|---|---|---|
| `fico_range_low` | Skor FICO **saat pengajuan** | Fitur |
| `last_fico_range_low` | Skor FICO **terbaru**, diperbarui selama pinjaman berjalan | **Buang** |

Kalau seseorang menunggak, skor FICO terbarunya pasti anjlok. Memakai kolom kedua sama dengan melihat jawabannya. Model akan terlihat sangat akurat, padahal menyontek.

### 2. Nama yang menyesatkan ke arah sebaliknya

`chargeoff_within_12_mths` terdengar seperti "pinjaman ini dihapusbukukan dalam 12 bulan" — seperti jawaban yang bocor.

Padahal artinya: **berapa kredit milik pemohon di lembaga lain yang dihapusbukukan dalam 12 bulan sebelum pengajuan**. Ini riwayat biro kredit, tersedia sebelum keputusan, dan ada di `browseNotes`.

Beberapa project Lending Club di internet keliru membuang kolom ini karena namanya. Pelajarannya: **jangan menilai kolom dari namanya, periksa definisinya.**

### 3. Kolom yang dulu kita pakai

`initial_list_status` sempat dipakai sebagai fitur di versi sebelumnya. Sekarang dibuang.

Kolom ini menyatakan apakah pinjaman ditawarkan utuh kepada satu investor atau dipecah ke banyak investor. Itu **keputusan operasional platform**, bukan karakteristik pemohon — dan kebijakannya berubah dari waktu ke waktu, sehingga polanya tidak stabil antar tahun.

---

## Fitur inti — 27 kolom

Karakteristik pemohon yang tersedia saat pengajuan dan diperkirakan terisi sejak tahun-tahun awal.

| Kolom | Arti | Catatan |
|---|---|---|
| `loan_amnt` | Jumlah pinjaman yang diajukan | |
| `term` | Tenor, 36 atau 60 bulan | |
| `emp_length` | Lama bekerja | Diubah jadi angka |
| `home_ownership` | Status tempat tinggal | Kategori langka digabung |
| `annual_inc` | Penghasilan per tahun, dilaporkan sendiri | Nilai 0 dianggap kosong |
| `verification_status` | Apakah penghasilan diverifikasi | |
| `purpose` | Tujuan pinjaman | |
| `dti` | Rasio cicilan terhadap penghasilan | Nilai tidak wajar dianggap kosong |
| `delinq_2yrs` | Berapa kali menunggak 30+ hari dalam 2 tahun terakhir | |
| `earliest_cr_line` | Kapan rekening kredit pertama dibuka | Diolah jadi lama riwayat kredit |
| `fico_range_low` | Batas bawah skor FICO saat pengajuan | Digabung dengan batas atas jadi satu angka |
| `fico_range_high` | Batas atas skor FICO saat pengajuan | Idem |
| `inq_last_6mths` | Berapa kali mengajukan kredit dalam 6 bulan terakhir | |
| `mths_since_last_delinq` | Bulan sejak terakhir menunggak | **Kosong berarti tidak pernah** |
| `mths_since_last_record` | Bulan sejak catatan publik terakhir | **Kosong berarti tidak ada** |
| `open_acc` | Jumlah rekening kredit aktif | |
| `pub_rec` | Jumlah catatan publik negatif | |
| `revol_bal` | Saldo kartu kredit | |
| `revol_util` | Pemakaian limit kartu kredit | |
| `total_acc` | Total rekening kredit | |
| `mort_acc` | Jumlah KPR | Ditandai kalau kosong |
| `pub_rec_bankruptcies` | Catatan kebangkrutan | |
| `collections_12_mths_ex_med` | Ditagih pihak ketiga dalam 12 bulan, selain medis | |
| `acc_now_delinq` | Rekening yang sedang menunggak saat pengajuan | |
| `chargeoff_within_12_mths` | Kredit di tempat lain yang dihapusbukukan dalam 12 bulan terakhir | Lihat jebakan nomor 2 |
| `delinq_amnt` | Jumlah tunggakan saat pengajuan | |
| `tax_liens` | Sitaan pajak | |

**Catatan penting soal kolom "bulan sejak ...":** kekosongan di kolom-kolom ini **bukan data hilang**, melainkan informasi — orang itu tidak pernah menunggak. Mengisinya dengan median akan salah, karena menyamakan "tidak pernah menunggak" dengan "menunggak sekian bulan lalu". Penanganannya dibahas saat menulis kode pembersihan.

---

## Fitur kandidat — 50 kolom

Semuanya riwayat biro kredit yang tersedia saat pengajuan. Masalahnya: **Lending Club menambahkan sebagian besar kolom ini belakangan.**

Karena model dilatih di tahun-tahun lama lalu diuji di tahun-tahun baru, kolom yang kosong di tahun-tahun lama **tidak bisa dipakai** — model tidak punya kesempatan mempelajarinya. Keputusan akhirnya menunggu hasil pemeriksaan data.

| Keluarga | Kolom |
|---|---|
| **Tunggakan dan catatan buruk** (9) | `mths_since_last_major_derog`, `mths_since_recent_bc_dlq`, `mths_since_recent_revol_delinq`, `num_accts_ever_120_pd`, `num_tl_120dpd_2m`, `num_tl_30dpd`, `num_tl_90g_dpd_24m`, `pct_tl_nvr_dlq`, `tot_coll_amt` |
| **Saldo dan limit** (10) | `tot_cur_bal`, `avg_cur_bal`, `total_rev_hi_lim`, `tot_hi_cred_lim`, `total_bal_ex_mort`, `total_bc_limit`, `total_il_high_credit_limit`, `total_bal_il`, `max_bal_bc`, `bc_open_to_buy` |
| **Pemakaian limit** (4) | `bc_util`, `il_util`, `all_util`, `percent_bc_gt_75` |
| **Pembukaan rekening baru** (11) | `acc_open_past_24mths`, `num_tl_op_past_12m`, `open_acc_6m`, `open_il_12m`, `open_il_24m`, `open_rv_12m`, `open_rv_24m`, `mo_sin_rcnt_rev_tl_op`, `mo_sin_rcnt_tl`, `mths_since_rcnt_il`, `mths_since_recent_bc` |
| **Umur rekening** (2) | `mo_sin_old_il_acct`, `mo_sin_old_rev_tl_op` |
| **Jumlah rekening** (11) | `num_actv_bc_tl`, `num_actv_rev_tl`, `num_bc_sats`, `num_bc_tl`, `num_il_tl`, `num_op_rev_tl`, `num_rev_accts`, `num_rev_tl_bal_gt_0`, `num_sats`, `open_act_il`, `total_cu_tl` |
| **Pengajuan kredit** (3) | `mths_since_recent_inq`, `inq_fi`, `inq_last_12m` |

Dua kolom di sini tidak tercantum di `browseNotes` karena perbedaan penamaan antar sheet: `mo_sin_old_il_acct` tercatat di sana sebagai `mths_since_oldest_il_open`, sedangkan `mths_since_recent_bc_dlq` adalah atribut biro kredit yang menurut definisinya menggambarkan riwayat sebelum pengajuan.

---

## Pembanding — 4 kolom

Hasil penilaian risiko oleh Lending Club. **Tidak pernah dipakai model utama.**

| Kolom | Arti | Dipakai untuk |
|---|---|---|
| `grade` | Kelas risiko A–G dari Lending Club | Membuktikan suku bunga adalah turunannya |
| `sub_grade` | Kelas risiko terperinci A1–G5 | Idem |
| `int_rate` | Suku bunga | Kebijakan fitur `with_pricing`, sebagai pembanding |
| `installment` | Angsuran bulanan | Idem |

Keempatnya lolos saringan pertama — memang tersedia sebelum pendanaan. Tapi memakainya berarti menilai risiko dengan penilaian pihak lain.

---

## Hasil — 9 kolom

Informasi setelah pinjaman berjalan. **Dilarang masuk daftar fitur**, tapi sangat berharga untuk menghitung hasil.

| Kolom | Arti | Dipakai untuk |
|---|---|---|
| `loan_status` | Status akhir pinjaman | Membuat kolom target |
| `funded_amnt` | Uang yang benar-benar dipinjamkan | Dasar EAD |
| `total_rec_prncp` | Pokok yang sudah kembali | EAD saat gagal bayar |
| `recoveries` | Uang yang berhasil ditagih setelah hapus buku | LGD |
| `collection_recovery_fee` | Biaya untuk menagih | LGD |
| `total_pymnt` | Seluruh uang yang masuk | Untung atau rugi per pinjaman |
| `total_rec_int` | Bunga yang benar-benar diterima | Rincian untung |
| `out_prncp` | Sisa pokok | Pemeriksaan: pinjaman yang selesai harus bernilai 0 |
| `last_pymnt_d` | Tanggal pembayaran terakhir | Memeriksa pemotongan data; dasar kalau nanti beralih ke PD 12 bulan |

### Rumus yang dipakai

```
Target
  Charged Off  -> 1 (gagal bayar)
  Fully Paid   -> 0 (lunas)
  Status lain  -> tidak dipakai, pinjamannya belum selesai

EAD (hanya untuk yang gagal bayar)
  = funded_amnt - total_rec_prncp
  = uang yang masih di tangan peminjam saat berhenti membayar

Pemulihan bersih
  = recoveries - collection_recovery_fee

LGD
  = 1 - (pemulihan bersih / EAD)
  dibatasi antara 0 dan 1

Untung atau rugi per pinjaman
  = total_pymnt - funded_amnt
```

Satu hal yang harus diperiksa dengan data: apakah `total_pymnt` sudah mencakup `recoveries`. Kalau belum, rumus untung perlu ditambah `recoveries`.

---

## Pengatur — 3 kolom

| Kolom | Dipakai untuk |
|---|---|
| `id` | Kunci unik setiap pinjaman |
| `issue_d` | Membagi data berdasarkan tahun. **Bukan fitur** — alasannya sama seperti di versi sebelumnya. |
| `application_type` | Penyaring: hanya pengajuan perorangan yang dipakai |

---

## Buang — 58 kolom

| Alasan | Kolom |
|---|---|
| **Identitas dan teks bebas** (5) | `member_id`, `url`, `desc`, `title`, `emp_title` |
| **Lokasi** (2) | `zip_code`, `addr_state` |
| **Operasional platform** (3) | `initial_list_status`, `disbursement_method`, `policy_code` |
| **Porsi investor, duplikat kolom lain** (3) | `funded_amnt_inv`, `out_prncp_inv`, `total_pymnt_inv` |
| **Setelah pencairan, tidak dibutuhkan** (5) | `total_rec_late_fee`, `last_pymnt_amnt`, `next_pymnt_d`, `last_credit_pull_d`, `pymnt_plan` |
| **FICO terbaru — kebocoran** (2) | `last_fico_range_high`, `last_fico_range_low` |
| **Program keringanan pembayaran** (15) | `hardship_flag`, `hardship_type`, `hardship_reason`, `hardship_status`, `deferral_term`, `hardship_amount`, `hardship_start_date`, `hardship_end_date`, `payment_plan_start_date`, `hardship_length`, `hardship_dpd`, `hardship_loan_status`, `orig_projected_additional_accrued_interest`, `hardship_payoff_balance_amount`, `hardship_last_payment_amount` |
| **Penyelesaian utang** (7) | `debt_settlement_flag`, `debt_settlement_flag_date`, `settlement_status`, `settlement_date`, `settlement_amount`, `settlement_percentage`, `settlement_term` |
| **Pengajuan bersama** (16) | `annual_inc_joint`, `dti_joint`, `verified_status_joint`, `revol_bal_joint`, dan 12 kolom `sec_app_*` |

### Soal lokasi

Lokasi tersedia sebelum keputusan, jadi secara teknis boleh dipakai. Kolom ini dibuang dengan alasan lain: lokasi bisa menjadi **pengganti tidak langsung** bagi karakteristik yang tidak boleh dipakai dalam keputusan kredit. Di banyak negara, menolak kredit berdasarkan wilayah tempat tinggal adalah praktik diskriminatif yang dilarang.

Ini juga sejalan dengan perhatian OJK terhadap bias dalam pengambilan keputusan berbasis algoritma.

### Soal program keringanan dan penyelesaian utang

Keduanya adalah kebocoran paling mudah dikenali: program keringanan hanya diberikan kepada peminjam yang sudah kesulitan membayar. Kalau model melihatnya, model tahu jawabannya.

---

## Yang masih harus dipastikan dengan data

1. **Kolom kandidat mana yang sudah terisi di tahun-tahun awal** — menentukan berapa dari 50 kolom yang bisa dipakai
2. **Apakah `total_pymnt` sudah mencakup `recoveries`** — menentukan rumus untung
3. **Apakah tingkat pemulihan tahun terbaru lebih rendah** — tanda penagihan belum selesai
4. **Berapa banyak pengajuan bersama** — memastikan membuangnya tidak menghilangkan terlalu banyak data
