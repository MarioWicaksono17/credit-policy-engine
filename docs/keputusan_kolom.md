# Keputusan Kolom

Dataset: `accepted_2007_to_2018Q4.csv` — Lending Club lengkap, Kaggle (wordsforthewise)
Acuan: `LCDataDictionary.xlsx`, sheet `LoanStats` dan `browseNotes`
Status: **final**, setelah pemeriksaan data

Dokumen ini menjelaskan nasib setiap kolom dari 151 kolom yang ada, dan alasannya.

---

## Ringkasan

| Kelompok | Jumlah | Peran |
|---|---|---|
| **Fitur** | 62 | Dilihat model |
| **Pembanding** | 4 | Penilaian Lending Club sendiri — tidak pernah dilihat model utama |
| **Hasil** | 9 | Menghitung target, EAD, LGD, dan untung — **dilarang dilihat model** |
| **Pengatur** | 4 | Kunci baris, tahun, dan penyaring |
| **Buang** | 72 | Tidak dipakai |
| **Total** | **151** | |

---

## Cakupan data

Tiga penyaring dipakai sekali di awal, sebelum model melihat apa pun:

| Penyaring | Aturan | Alasan |
|---|---|---|
| `loan_status` | Hanya pinjaman yang sudah selesai | Yang masih berjalan belum ketahuan hasil akhirnya |
| `application_type` | Hanya pengajuan perorangan | Pengajuan bersama punya kolom berbeda, dan hanya 5% data |
| `term` | **Hanya tenor 36 bulan** | Lihat bawah |

Pembagian waktu:

| Bagian | Tahun | Pinjaman 36 bulan | Kegunaan |
|---|---|---|---|
| Latih | 2013 | 100.422 | Melatih model |
| Validasi | 2014 | 162.570 | Memilih model dan garis batas |
| Uji | 2015 | sekitar 282.600 | Menilai hasil akhir, disentuh sekali |

Tahun 2016–2018 tidak dipakai: saat data diambil, hanya 11–67% pinjamannya yang sudah selesai.

### Kenapa hanya tenor 36 bulan

| Tahun | Tenor | % selesai | Default rate |
|---|---|---|---|
| 2013 | 36 | 100,0 | 12,3% |
| 2013 | 60 | 100,0 | 25,1% |
| 2014 | 36 | 100,0 | 13,7% |
| 2014 | 60 | **82,9** | 31,1% |
| 2015 | 36 | 99,9 | 14,9% |
| 2015 | 60 | **67,1** | 36,4% |

Pada 2013, ketika semua pinjaman sudah selesai, default rate tenor 60 bulan sekitar dua kali lipat tenor 36 bulan. Kalau hubungan itu tetap, default rate 60 bulan pada 2015 seharusnya sekitar 30%. Data menunjukkan 36,4%.

Selisih sekitar 6 poin itu kemungkinan besar efek pemotongan data. Pinjaman yang gagal bayar biasanya macet lebih awal, sedangkan yang lancar baru selesai di akhir tenor. Jadi ketika sepertiga pinjaman 60 bulan belum selesai, yang sudah tercatat didominasi yang gagal bayar.

Bias ini membuat default rate seluruh data uji terlihat sekitar 1,5 poin lebih tinggi dari kenyataan — ukuran yang sama dengan pergeseran kalibrasi yang ingin diukur. Membatasi ke tenor 36 bulan menghilangkan bias itu dari akarnya: semua tahun yang dipakai 100% selesai.

Dengan tenor seragam, `term` tidak lagi bisa menjadi fitur — nilainya sama untuk semua pinjaman. Ia berpindah peran menjadi penyaring.

---

## Cara memilah fitur: dua saringan

### Saringan 1 — Apakah informasinya ada SEBELUM keputusan kredit?

Sheet `browseNotes` di kamus kolom berisi informasi yang ditampilkan Lending Club kepada investor **sebelum** pinjaman didanai. Kolom yang ada di daftar itu tersedia saat keputusan diambil. Yang tidak ada, baru muncul setelah pinjaman berjalan.

| | Jumlah kolom |
|---|---|
| Ada di `browseNotes` | 107 |
| Tidak ada | 44 |

Ke-44 kolom yang tidak ada seluruhnya berupa pembayaran, penagihan, program keringanan, dan penyelesaian utang — ditambah status pinjaman dan tanggal pencairan.

Aturan ini berasal dari dokumentasi Lending Club sendiri, bukan penilaian pribadi.

### Saringan 2 — Kalaupun tersedia, apakah layak dipakai?

Kolom yang lolos saringan pertama tetap dikeluarkan bila:

- merupakan **penilaian risiko Lending Club sendiri** (grade, suku bunga)
- berupa **identitas atau teks bebas**
- berupa **lokasi**, yang berisiko menjadi dasar diskriminasi
- merupakan **keputusan operasional platform**, bukan karakteristik pemohon
- hanya berlaku untuk **pengajuan bersama**
- **belum terisi** di tahun latih

---

## Tiga jebakan paling halus

### 1. Dua FICO yang namanya hampir sama

| Kolom | Arti | Keputusan |
|---|---|---|
| `fico_range_low` | Skor FICO **saat pengajuan** | Fitur |
| `last_fico_range_low` | Skor FICO **terbaru**, diperbarui selama pinjaman berjalan | **Buang** |

Kalau seseorang menunggak, skor FICO terbarunya pasti anjlok. Memakai kolom kedua sama dengan melihat jawabannya.

### 2. Nama yang menyesatkan ke arah sebaliknya

`chargeoff_within_12_mths` terdengar seperti "pinjaman ini dihapusbukukan dalam 12 bulan". Padahal artinya **jumlah kredit pemohon di lembaga lain yang dihapusbukukan dalam 12 bulan sebelum pengajuan**. Ini riwayat biro kredit dan tercantum di `browseNotes`.

Pelajarannya: jangan menilai kolom dari namanya, periksa definisinya.

### 3. Kolom yang dulu dipakai

`initial_list_status` sempat menjadi fitur di versi pertama. Kolom ini menyatakan apakah pinjaman ditawarkan utuh atau dipecah ke banyak investor — keputusan operasional platform, bukan karakteristik pemohon, dan kebijakannya berubah dari waktu ke waktu.

---

## Fitur — 62 kolom

### Dari formulir pengajuan (7)

| Kolom | Arti | Catatan |
|---|---|---|
| `loan_amnt` | Jumlah pinjaman yang diajukan | |
| `emp_length` | Lama bekerja | Diubah jadi angka; ditandai kalau kosong |
| `home_ownership` | Status tempat tinggal | Kategori |
| `annual_inc` | Penghasilan per tahun, dilaporkan sendiri | Nilai di bawah 1 dianggap kosong |
| `verification_status` | Apakah penghasilan diverifikasi | Kategori |
| `purpose` | Tujuan pinjaman | Kategori |
| `dti` | Rasio cicilan terhadap penghasilan | Di luar 0–100 dianggap kosong |

### Riwayat kredit dasar (19)

| Kolom | Arti | Catatan |
|---|---|---|
| `fico_range_low` | Batas bawah FICO saat pengajuan | Digabung jadi satu angka |
| `fico_range_high` | Batas atas FICO saat pengajuan | Idem |
| `earliest_cr_line` | Kapan rekening kredit pertama dibuka | Diolah jadi lama riwayat kredit |
| `delinq_2yrs` | Berapa kali menunggak 30+ hari dalam 2 tahun | |
| `inq_last_6mths` | Pengajuan kredit dalam 6 bulan terakhir | |
| `mths_since_last_delinq` | Bulan sejak terakhir menunggak | **Kosong berarti tidak pernah** |
| `mths_since_last_record` | Bulan sejak catatan publik terakhir | **Kosong berarti tidak ada** |
| `open_acc` | Rekening kredit aktif | |
| `pub_rec` | Catatan publik negatif | |
| `revol_bal` | Saldo kartu kredit | |
| `revol_util` | Pemakaian limit kartu kredit | |
| `total_acc` | Total rekening kredit | |
| `mort_acc` | Jumlah KPR | |
| `pub_rec_bankruptcies` | Catatan kebangkrutan | |
| `collections_12_mths_ex_med` | Ditagih pihak ketiga dalam 12 bulan, selain medis | |
| `acc_now_delinq` | Rekening yang sedang menunggak saat pengajuan | |
| `chargeoff_within_12_mths` | Kredit di tempat lain yang dihapusbukukan | Lihat jebakan nomor 2 |
| `delinq_amnt` | Jumlah tunggakan saat pengajuan | |
| `tax_liens` | Sitaan pajak | |

### Rincian biro kredit (36)

Terisi hampir penuh mulai 2013 — alasan data latih dimulai dari tahun itu.

| Keluarga | Kolom |
|---|---|
| **Tunggakan dan catatan buruk** (9) | `mths_since_last_major_derog`, `mths_since_recent_bc_dlq`, `mths_since_recent_revol_delinq`, `num_accts_ever_120_pd`, `num_tl_120dpd_2m`, `num_tl_30dpd`, `num_tl_90g_dpd_24m`, `pct_tl_nvr_dlq`, `tot_coll_amt` |
| **Saldo dan limit** (9) | `tot_cur_bal`, `avg_cur_bal`, `total_rev_hi_lim`, `tot_hi_cred_lim`, `total_bal_ex_mort`, `total_bc_limit`, `total_il_high_credit_limit`, `bc_open_to_buy`, `bc_util` |
| **Pemakaian limit** (1) | `percent_bc_gt_75` |
| **Pembukaan rekening baru** (6) | `acc_open_past_24mths`, `num_tl_op_past_12m`, `mo_sin_rcnt_rev_tl_op`, `mo_sin_rcnt_tl`, `mths_since_recent_bc`, `mths_since_recent_inq` |
| **Umur rekening** (2) | `mo_sin_old_il_acct`, `mo_sin_old_rev_tl_op` |
| **Jumlah rekening** (9) | `num_actv_bc_tl`, `num_actv_rev_tl`, `num_bc_sats`, `num_bc_tl`, `num_il_tl`, `num_op_rev_tl`, `num_rev_accts`, `num_rev_tl_bal_gt_0`, `num_sats` |

### Soal kolom "bulan sejak ..."

Beberapa kolom terisi rendah di semua tahun — `mths_since_last_record` misalnya hanya sekitar 15–20%. Itu **bukan data hilang**. Kosong berarti orang itu tidak pernah punya catatan tersebut.

Mengisinya langsung dengan median akan menyamakan "tidak pernah menunggak" dengan "menunggak sekian bulan lalu". Karena itu kolom-kolom ini diberi penanda terpisah **sebelum** diisi, supaya informasi "tidak pernah" tetap ada.

### Soal jumlah fitur

62 fitur terlalu banyak untuk model yang harus bisa dijelaskan. Banyak di antaranya saling mirip — misalnya jumlah rekening aktif, jumlah rekening terbuka, dan jumlah rekening bersaldo. Jumlahnya akan dipangkas saat melatih model, dengan alasan untuk setiap variabel yang dipertahankan.

---

## Pembanding — 4 kolom

| Kolom | Arti | Dipakai untuk |
|---|---|---|
| `grade` | Kelas risiko A–G dari Lending Club | Membuktikan suku bunga adalah turunannya |
| `sub_grade` | Kelas risiko terperinci | Idem |
| `int_rate` | Suku bunga | Kebijakan fitur `with_pricing`, sebagai pembanding |
| `installment` | Angsuran bulanan | Idem |

Keempatnya tersedia sebelum pendanaan. Tapi memakainya berarti menilai risiko dengan penilaian pihak lain.

---

## Hasil — 9 kolom

Informasi setelah pinjaman berjalan. **Dilarang masuk daftar fitur.** Program berhenti otomatis kalau salah satunya tercantum di fitur — penjagaan ini ada di `src/config.py`.

| Kolom | Dipakai untuk |
|---|---|
| `loan_status` | Membuat kolom target |
| `funded_amnt` | Dasar EAD |
| `total_rec_prncp` | EAD saat gagal bayar |
| `recoveries` | LGD |
| `collection_recovery_fee` | LGD dan untung |
| `total_pymnt` | Untung per pinjaman |
| `total_rec_int` | Rincian untung |
| `out_prncp` | Pemeriksaan: pinjaman yang selesai harus bernilai 0 |
| `last_pymnt_d` | Pemeriksaan pemotongan data |

### Rumus

```
Target
  Charged Off                -> 1 (gagal bayar)
  Fully Paid                 -> 0 (lunas)
  Status lain                -> tidak dipakai

EAD
  = funded_amnt - total_rec_prncp
  = uang yang masih di tangan peminjam saat berhenti membayar

LGD
  = 1 - (recoveries - collection_recovery_fee) / EAD
  dibatasi antara 0 dan 1

Untung atau rugi per pinjaman
  = total_pymnt - collection_recovery_fee - funded_amnt
```

`total_pymnt` sudah mencakup `recoveries` — terbukti dari data: selisihnya persis 0,00. Karena itu `recoveries` tidak ditambahkan lagi dalam rumus untung.

### Temuan dari data

| | Asumsi versi pertama | Data sebenarnya |
|---|---|---|
| LGD | 65% | **91%** |
| EAD | 100% dari pinjaman | **69%** dari pinjaman |
| Kerugian per pinjaman gagal bayar | 65% dari pinjaman | sekitar **63%** dari pinjaman |

Asumsi versi pertama keliru di dua tempat — LGD terlalu rendah, EAD terlalu tinggi — dan kedua kesalahan itu kebetulan saling menutupi.

Sebanyak 30,7% pinjaman yang gagal bayar tidak menghasilkan pemulihan sama sekali.

LGD naik pada pinjaman 2017 (0,935) dan 2018 (0,972) karena penagihannya belum selesai saat data diambil. Tahun-tahun yang dipakai project ini (2013–2015) tidak terpengaruh.

---

## Pengatur — 4 kolom

| Kolom | Peran |
|---|---|
| `id` | Kunci unik setiap pinjaman |
| `issue_d` | Membagi data berdasarkan tahun. **Bukan fitur.** |
| `application_type` | Penyaring: hanya perorangan |
| `term` | Penyaring: hanya 36 bulan |

---

## Buang — 72 kolom

| Alasan | Kolom |
|---|---|
| **Identitas dan teks bebas** (5) | `member_id`, `url`, `desc`, `title`, `emp_title` |
| **Lokasi** (2) | `zip_code`, `addr_state` |
| **Operasional platform** (3) | `initial_list_status`, `disbursement_method`, `policy_code` |
| **Porsi investor, duplikat** (3) | `funded_amnt_inv`, `out_prncp_inv`, `total_pymnt_inv` |
| **Setelah pencairan, tidak dibutuhkan** (5) | `total_rec_late_fee`, `last_pymnt_amnt`, `next_pymnt_d`, `last_credit_pull_d`, `pymnt_plan` |
| **FICO terbaru — kebocoran** (2) | `last_fico_range_high`, `last_fico_range_low` |
| **Program keringanan pembayaran** (15) | `hardship_flag`, `hardship_type`, `hardship_reason`, `hardship_status`, `deferral_term`, `hardship_amount`, `hardship_start_date`, `hardship_end_date`, `payment_plan_start_date`, `hardship_length`, `hardship_dpd`, `hardship_loan_status`, `orig_projected_additional_accrued_interest`, `hardship_payoff_balance_amount`, `hardship_last_payment_amount` |
| **Penyelesaian utang** (7) | `debt_settlement_flag`, `debt_settlement_flag_date`, `settlement_status`, `settlement_date`, `settlement_amount`, `settlement_percentage`, `settlement_term` |
| **Pengajuan bersama** (16) | `annual_inc_joint`, `dti_joint`, `verified_status_joint`, `revol_bal_joint`, dan 12 kolom `sec_app_*` |
| **Baru ada mulai 2016** (14) | `open_acc_6m`, `open_act_il`, `open_il_12m`, `open_il_24m`, `mths_since_rcnt_il`, `total_bal_il`, `il_util`, `open_rv_12m`, `open_rv_24m`, `max_bal_bc`, `all_util`, `inq_fi`, `total_cu_tl`, `inq_last_12m` |

### Soal lokasi

Lokasi tersedia sebelum keputusan, tapi bisa menjadi pengganti tidak langsung bagi karakteristik yang tidak boleh dipakai dalam keputusan kredit. Menolak kredit berdasarkan wilayah tempat tinggal adalah praktik diskriminatif di banyak negara, dan sejalan dengan perhatian OJK terhadap bias dalam keputusan berbasis algoritma.

### Soal kolom yang baru ada mulai 2016

Keempat belas kolom ini adalah informasi biro kredit yang sah dan tersedia sebelum keputusan. Masalahnya hanya waktu: Lending Club baru mengumpulkannya mulai 2016, sementara data latih berasal dari 2013. Model tidak punya kesempatan mempelajarinya.
