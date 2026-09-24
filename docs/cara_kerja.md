# Cara Kerja Project Ini

Dokumen ini menjelaskan project dari dua sisi: keputusan kredit apa saja yang diambil beserta alasannya, dan bagaimana keputusan itu diterjemahkan menjadi program yang bisa dijalankan.

---

## Isi dokumen

**Bagian 1 — Cerita dari sisi kredit.** Masalah apa yang dijawab, keputusan apa saja yang diambil, dan kenapa. Tidak ada nama file di sini.

**Bagian 2 — Cara kerja programnya.** Setiap file: isinya apa, dipanggil siapa, memanggil apa.

---

# BAGIAN 1 — Cerita dari sisi kredit

## Masalah yang dijawab

Sebuah lembaga pemberi pinjaman menerima ratusan ribu pengajuan. Sebagian akan membayar lunas, sebagian akan gagal bayar. **Masalahnya: tidak ada yang tahu yang mana.**

Kalau semua pengajuan diterima, kerugian dari yang gagal bayar bisa menelan keuntungan dari yang lunas. Kalau terlalu ketat, pemberi pinjaman kehilangan nasabah baik — dan bisnisnya tidak jalan.

Project ini membangun alat bantu untuk menjawab tiga pertanyaan:

| Pertanyaan | Siapa yang bertanya |
|---|---|
| Orang ini seberapa berisiko? | Analis kredit |
| Di angka berapa kita menarik garis, dan berapa harganya? | Pembuat kebijakan kredit |
| Alat ini bisa dipercaya sampai mana? | Auditor dan regulator |

### Di mana posisi project ini dalam siklus kredit

Siklus kredit di bank punya lima tahap:

| Tahap | Isinya | Ada di project ini? |
|---|---|---|
| 1. Pemasaran | Menjaring calon nasabah | Tidak |
| 2. **Analisis kredit** | Menilai risiko, memutuskan terima-tolak | **Ya** |
| 3. Penetapan harga | Menentukan bunga dan plafon | Tidak |
| 4. Pemantauan | Mengawasi pinjaman berjalan | Tidak |
| 5. Penagihan | Menangani yang menunggak | Tidak |

Cakupannya sengaja sempit. Project yang mengaku mencakup seluruh siklus biasanya tidak mendalami satu pun.

---

## Keputusan 1 — Apa yang disebut "gagal bayar"

Sebelum bisa memprediksi gagal bayar, harus jelas dulu **apa artinya gagal bayar**.

Pilihan yang diambil: pinjaman yang **dihapusbukukan** — ketika pemberi pinjaman menyerah menagih dan mencatatnya sebagai kerugian. Di Lending Club, ini terjadi setelah menunggak **120 hari atau lebih**.

### Kenapa penting disebut

Definisi ini **berbeda dari yang dipakai bank di Indonesia**:

| | Definisi | Selisihnya |
|---|---|---|
| Project ini | Hapus buku, sekitar 120 hari menunggak | — |
| OJK | Kolektibilitas 3, 90 hari menunggak | Sekitar satu bulan lebih awal |
| Basel | Gagal bayar dalam 12 bulan pertama | Jangka waktunya berbeda |

Selisih dengan OJK cuma sekitar satu bulan — tidak besar. Yang lebih berbeda adalah **jangka waktunya**: project ini melihat seluruh umur pinjaman, sementara bank umumnya memakai jangka tetap 12 bulan.

### Kenapa tidak pakai 12 bulan saja

Karena datanya tidak mencatat **kapan** seseorang berhenti membayar, hanya **apakah** dia berhenti. Tanpa tanggalnya, pertanyaan "gagal bayar dalam 12 bulan pertama?" tidak bisa dijawab.

Akibatnya terasa: dengan definisi seumur pinjaman, harus menunggu pinjaman selesai sebelum datanya bisa dipakai. Itu sebabnya data terbaru yang bisa dipakai cuma sampai 2015, padahal datasetnya sampai 2018.

---

## Keputusan 2 — Produk mana yang dinilai

Cakupannya dipersempit jadi: **pinjaman konsumen tanpa agunan, tenor 36 bulan, pengajuan perorangan.**

Tiga penyaring, masing-masing dengan alasannya.

### Hanya pinjaman yang sudah selesai

Pinjaman yang masih berjalan belum ketahuan hasilnya. Memasukkannya berarti menebak.

### Hanya pengajuan perorangan

Pengajuan bersama punya kolom yang berbeda — ada data penghasilan dan riwayat kredit pasangan. Hanya 5% data, jadi membuangnya tidak banyak berpengaruh.

### Hanya tenor 36 bulan

Ini yang paling penting, dan alasannya tidak langsung terlihat.

Saat data diambil, pinjaman 60 bulan dari 2014–2015 **belum semuanya selesai** — baru 67% sampai 83%. Dan yang sudah selesai bukan sembarang: orang yang gagal bayar biasanya macet lebih awal, sedangkan yang lancar baru selesai di akhir tenor.

Akibatnya, yang tercatat didominasi yang gagal bayar:

| Tahun | Tenor | Sudah selesai | Default rate terlihat |
|---|---|---|---|
| 2013 | 36 bulan | 100% | 12,3% |
| 2013 | 60 bulan | 100% | 25,1% |
| 2015 | 36 bulan | 99,9% | 14,9% |
| 2015 | 60 bulan | **67,1%** | **36,4%** |

Di 2013, ketika semuanya sudah selesai, pinjaman 60 bulan gagal bayar sekitar dua kali lipat tenor 36 bulan. Kalau perbandingan itu tetap, angka 2015 seharusnya sekitar 30%, bukan 36,4%.

Selisih 6 poin itu **bukan risiko sungguhan** — itu efek data yang terpotong.

Masalahnya, selisih sebesar itu sama besarnya dengan hal yang ingin diukur project ini. Membatasi ke tenor 36 bulan menghilangkan gangguan itu dari akarnya: semua tahun yang dipakai 100% selesai.

### Di bank

Memisahkan produk memang praktik standar. KTA, KPR, dan kartu kredit punya scorecard sendiri-sendiri, karena pola risikonya berbeda. Pinjaman 60 bulan dengan risiko dua kali lipat memang layak dimodelkan terpisah.

---

## Keputusan 3 — Variabel mana yang boleh dilihat

Aturannya satu kalimat: **model hanya boleh melihat informasi yang tersedia saat keputusan kredit diambil.**

Dari 151 kolom, ini nasibnya:

| Kelompok | Jumlah | Keputusan |
|---|---|---|
| Informasi pemohon saat pengajuan | 62 | **Dipakai** |
| Penilaian Lending Club sendiri | 4 | Dibuang, disimpan sebagai pembanding |
| Informasi setelah pinjaman berjalan | 9 | Dibuang dari model, dipakai menghitung uang |
| Penyaring dan pengenal | 4 | Bukan fitur |
| Lainnya | 72 | Dibuang |

### Yang paling penting: membuang suku bunga dan grade

Data Lending Club punya kolom `grade` (kelas risiko A–G) dan `int_rate` (suku bunga). Keduanya kelihatan sangat berguna — bunga tinggi biasanya berarti peminjam berisiko.

**Tapi keduanya adalah penilaian risiko Lending Club sendiri.** Memakainya bukan memprediksi risiko — itu menyontek jawaban pihak lain.

Dan ada masalah yang lebih mendasar: saat pemohon baru datang, **bunganya belum ada**. Bunga ditetapkan setelah risikonya dinilai. Model yang butuh suku bunga tidak bisa dipakai pada saat keputusan diambil.

Buktinya ada di angka. Model yang ditambah suku bunga:

| | Tanpa suku bunga | Dengan suku bunga |
|---|---|---|
| AUC | 0,6655 | 0,6923 |
| Melesetnya angka PD | +2,13 poin | **+4,01 poin** |

Lebih pintar mengurutkan, tapi angkanya **hampir dua kali lebih meleset**. Masuk akal: suku bunga adalah penilaian tahun 2013. Ketika keadaan berubah di 2015, penilaian lama itu menyesatkan.

### Yang dibuang karena alasan keadilan

Kode pos dan provinsi tersedia saat pengajuan, jadi secara teknis boleh dipakai. Tetap dibuang.

Alasannya: lokasi bisa menjadi **pengganti tidak langsung** bagi hal-hal yang tidak boleh dipakai dalam keputusan kredit — suku, agama, atau status ekonomi suatu wilayah. Menolak kredit berdasarkan tempat tinggal adalah praktik diskriminatif yang dilarang di banyak negara.

OJK sendiri menyoroti bias dalam pengambilan keputusan berbasis algoritma sebagai salah satu tantangan utama.

### Satu jebakan yang halus

Dataset punya dua kolom skor FICO yang namanya hampir sama:

| Kolom | Artinya | Keputusan |
|---|---|---|
| `fico_range_low` | Skor **saat pengajuan** | Dipakai |
| `last_fico_range_low` | Skor **terbaru**, diperbarui selama pinjaman berjalan | Dibuang |

Kalau seseorang menunggak, skor terbarunya pasti anjlok. Memakai kolom kedua sama dengan melihat jawabannya — model akan terlihat sangat akurat, padahal menyontek.

Inilah alasan program punya pemeriksaan otomatis yang menolak berjalan kalau kolom terlarang masuk daftar fitur.

---

## Keputusan 4 — Cara menguji model

Cara yang lazim di project pemula: bagi data **secara acak**, 80% untuk belajar, 20% untuk menguji.

Project ini memakai cara lain: **bagi berdasarkan tahun.**

| Bagian | Tahun | Pinjaman | Gagal bayar | Tugasnya |
|---|---|---|---|---|
| Latih | 2013 | 100.422 | 12,3% | Model belajar dari sini |
| Validasi | 2014 | 162.570 | 13,7% | Semua pemilihan terjadi di sini |
| Uji | 2015 | 282.787 | 14,9% | Dinilai sekali di akhir |

### Kenapa

Model kredit dipakai untuk menilai pemohon **di masa depan**. Menguji dengan data acak dari periode yang sama seperti memberi ujian yang soalnya sudah bocor — model sudah pernah melihat "zaman" yang sama.

Bedanya besar sekali:

| Cara menguji | AUC | Melesetnya angka PD |
|---|---|---|
| Acak | 0,6617 | **−0,01 poin** |
| Berdasarkan tahun | 0,6655 | **+2,13 poin** |

Dengan pembagian acak, model terlihat **sempurna** kalibrasinya. Dengan pembagian tahun, terlihat meleset 2 poin.

Angka kedua yang benar. Yang pertama menipu karena data latih dan data uji berasal dari periode yang sama.

### Kenapa validasi dan uji dipisah

Semua pemilihan terjadi di 2014: variabel mana yang dipakai, garis batas berapa, penggeser kalibrasi berapa.

Data 2015 disentuh **sekali saja**, di akhir. Kalau tidak dipisah, kita akan membuat soal ujian sendiri lalu mengerjakannya — nilainya pasti bagus, tapi tidak membuktikan apa pun.

---

## Keputusan 5 — Memilih variabel yang benar-benar dipakai

Dari 62 kolom fitur (yang setelah diolah jadi 67 variabel), model utama hanya memakai **19**.

Kenapa tidak semuanya? Tiga alasan.

**Banyak yang tidak berguna.** Sebagian variabel sama sekali tidak membedakan peminjam yang lunas dan yang gagal bayar.

**Banyak yang kembar.** Ada tiga variabel berbeda untuk "jumlah kartu kredit" — yang aktif, yang terbuka, yang ada saldonya. Isinya hampir sama.

**Tidak bisa dijelaskan.** Model dengan 67 variabel menghasilkan tabel penjelasan 67 baris. Tidak ada komite kredit yang mau membacanya.

### Tiga saringan

| Saringan | Cara kerjanya | Terbuang |
|---|---|---|
| Kekuatan | Buang yang Information Value-nya di bawah 0,02 | 40 |
| Kembar | Kalau dua variabel terlalu mirip, pertahankan yang lebih kuat | 7 |
| Akal sehat | Buang yang arah pengaruhnya tidak masuk akal | 1 |

**Information Value** mengukur seberapa kuat satu variabel memisahkan yang lunas dari yang gagal bayar. Kalau dua kelompok berisi campuran yang sama, variabel itu tidak memberi informasi apa pun.

Patokan industri kredit: di bawah 0,02 tidak berguna, di atas 0,5 patut dicurigai sebagai kebocoran data.

### Saringan ketiga layak dijelaskan

`total_rev_hi_lim` adalah total limit kartu kredit seseorang. Dilihat sendirian: makin besar limit, makin aman — wajar, limit besar diberikan ke orang yang dipercaya.

Tapi di dalam model, angkanya keluar **terbalik** — seolah limit besar justru berbahaya. Penyebabnya ada dua variabel lain yang sangat mirip, dan model membagi pengaruhnya dengan cara yang aneh.

Hasil seperti itu tidak bisa dijelaskan ke pemohon maupun ke komite. Jadi dibuang, dan model dilatih ulang.

### Hasilnya masuk akal semua

| Makin tinggi... | Risiko | Wajar? |
|---|---|---|
| Skor kredit | turun | ya |
| Penghasilan | turun | ya |
| Total limit kredit | turun — tanda peminjam mapan | ya |
| Rasio cicilan terhadap penghasilan | naik | ya |
| Rekening baru dalam 2 tahun | naik — tanda sedang butuh banyak utang | ya |
| Pengajuan kredit 6 bulan terakhir | naik | ya |

### Tujuan pinjaman: yang langka digabung

Tujuan pinjaman punya 13 kategori, banyak yang porsinya di bawah 1%. Kategori sekecil itu menghasilkan angka yang tidak stabil — dihitung dari sedikit orang, hasilnya bisa kebetulan.

Yang dipertahankan: yang porsinya sekitar 2% ke atas, **ditambah satu pengecualian**.

| Tujuan | Porsi | Gagal bayar | Keputusan |
|---|---|---|---|
| Konsolidasi utang | 57,3% | 12,6% | Dipertahankan |
| Kartu kredit | 26,0% | 10,7% | Dipertahankan |
| Renovasi rumah | 5,4% | 11,2% | Dipertahankan |
| Pembelian besar | 1,8% | 10,5% | Dipertahankan |
| **Usaha kecil** | **1,0%** | **23,5%** | **Dipertahankan** |
| Mobil, medis, pindahan, dll | di bawah 1% | beragam | Digabung |

Usaha kecil dipertahankan walaupun kecil, karena gagal bayarnya **hampir dua kali lipat rata-rata**. Sinyal sekuat itu akan hilang kalau digabung.

---

## Keputusan 6 — Memilih model yang bisa dijelaskan

Tiga jenis model dilatih dan dibandingkan:

| Model | Variabel | AUC |
|---|---|---|
| **Logistic Regression** — dipakai | 19 | 0,6655 |
| Random Forest | 67 | 0,6720 |
| Gradient Boosting | 67 | 0,6791 |

Yang paling rumit unggul **0,014** — sekitar satu pasang dari seratus.

### Kenapa memilih yang kalah

**Karena bisa dijelaskan.** Logistic Regression menghasilkan rumus yang bisa dibaca manusia: setiap variabel punya satu angka pengaruh. Dari situ bisa disusun **alasan penolakan** yang pasti dan bisa dilacak — bukan hasil tebakan.

Model rumit seperti Gradient Boosting menghasilkan ratusan pohon keputusan yang saling menimpa. Bisa akurat, tapi tidak bisa menjawab "kenapa orang ini ditolak" dengan jawaban yang sama setiap kali ditanya.

**Karena regulator menuntut itu.** OJK secara khusus menyoroti kurangnya transparansi algoritma — yang disebut masalah "kotak hitam" — sebagai tantangan utama pemakaian AI di perbankan.

**Karena selisihnya kecil.** 0,014 AUC adalah harga yang wajar untuk sesuatu yang bisa dipertanggungjawabkan. Dan angka itu **disebut terbuka**, bukan disembunyikan.

---

## Temuan 1 — Urutannya bertahan, angkanya bergeser

Ini temuan inti project.

Ada dua hal berbeda yang bisa diukur dari sebuah model kredit:

| | Pertanyaannya | Istilahnya |
|---|---|---|
| **Urutan** | Apakah yang berisiko benar ditempatkan lebih tinggi? | Diskriminasi |
| **Angka** | Kalau model bilang 10%, apakah benar 10 dari 100 gagal bayar? | Kalibrasi |

Hasilnya:

| | Diuji acak | Diuji per tahun |
|---|---|---|
| Urutan (AUC) | 0,6617 | 0,6655 |
| Angka (selisih) | −0,01 poin | **+2,13 poin** |

**Urutannya sama sekali tidak memburuk lintas waktu.** Yang bergeser hanya levelnya.

Per tahun, pergeserannya membesar:

| Tahun | Perkiraan gagal bayar | Kenyataan | Selisih |
|---|---|---|---|
| 2013 | 12.379 | 12.378 | data belajar |
| 2014 | 20.955 | 22.315 | +0,84 poin |
| 2015 | 36.061 | **42.089** | **+2,13 poin** |

Di 2015, model tidak melihat **5.946 orang** yang ternyata gagal bayar.

### Kenapa bergeser

Model belajar dari pinjaman 2013, ketika 12 dari 100 gagal bayar. Dipakai ke pinjaman 2015, ketika 15 dari 100 gagal bayar.

**Lending Club melebarkan penyaluran ke segmen yang lebih berisiko.** Populasi peminjamnya berubah, dan model tidak tahu.

Ini bukan bug. Ini yang benar-benar terjadi pada model kredit di dunia nyata, dan alasan bank punya tim khusus memantau model.

### Artinya untuk pemakaian

| Keperluan | Butuh apa | Model ini? |
|---|---|---|
| Keputusan terima-tolak | Urutan yang benar | **Boleh** |
| Menghitung cadangan kerugian | Angka yang tepat | **Tidak boleh mentah-mentah** |

Mengurutkan tidak butuh angka yang tepat. Mengalikan dengan uang butuh.

---

## Keputusan 7 — Menghitung kerugian dari data, bukan tebakan

Versi pertama project ini memakai asumsi: kalau gagal bayar, 65% uangnya hilang. Angka tebakan.

Dataset lengkap punya catatan penagihan yang sebenarnya, jadi angkanya bisa **dihitung**.

### Tiga singkatan

Contohnya satu pinjaman: Budi meminjam $10.000 untuk 36 bulan, mencicil lancar 14 bulan, lalu berhenti.

**EAD — uang yang masih di tangan peminjam saat berhenti**

Selama 14 bulan, Budi sudah mengembalikan sebagian pokok. Yang tersisa sekitar **57,7%** dari pinjamannya.

Ini penting: bank **tidak kehilangan $10.000**. Sebagian sudah kembali.

**LGD — dari sisa itu, berapa yang benar-benar hilang**

Bank menagih, dapat sedikit, dikurangi biaya penagihan. Yang benar-benar hilang: **88,6%** dari sisa.

Penagihan ternyata tidak banyak menolong — **30,7% pinjaman gagal bayar tidak menghasilkan pemulihan sama sekali**.

**PD — peluang gagal bayar**, dari model.

### Digabung

```
Perkiraan kerugian = PD x LGD x EAD
```

Kerugian per pinjaman gagal bayar: **51,2%** dari yang dipinjamkan.

### Asumsi lama ternyata meleset

| | Asumsi versi pertama | Kenyataan |
|---|---|---|
| Kerugian per pinjaman gagal bayar | 65% | **51,2%** |

Asumsi lama **melebihkan kerugian sekitar seperempat**, karena menghitung dari pokok penuh padahal sebagian sudah dicicil.

### Kenapa LGD diambil dari data latih

LGD dan EAD dihitung dari pinjaman yang gagal bayar di **2013**, lalu dipakai untuk menilai 2014 dan 2015.

Alasannya sama seperti modelnya sendiri: untuk pemohon baru, kita **belum tahu** berapa yang akan hilang. Yang bisa dipakai hanya pengalaman masa lalu.

---

## Keputusan 8 — Menentukan garis batas

Sekarang setiap pemohon punya angka risiko. Pertanyaannya: **di angka berapa kita bilang "tolak"?**

### Dua pertimbangan

**Untung.** Untuk setiap garis batas, hitung uang yang masuk dikurangi uang yang hilang.

**Risiko.** Batas yang ditetapkan: dari semua yang disetujui, maksimal **10 dari 100** boleh gagal bayar.

Aturannya: **pilih yang paling menguntungkan, di antara yang tidak melanggar batas risiko.** Seperti memilih makanan paling enak yang harganya masih dalam uang saku.

### Kenapa tidak ambil yang paling untung saja

Secara hitungan uang, paling untung adalah menyetujui hampir semua orang — garis 40%. Kontribusinya $180,4 juta, dibanding $143,7 juta di garis terpilih.

Kenapa tidak diambil? Dua alasan.

**Bantalannya tipis.** Kalau keadaan ekonomi memburuk, kerugian membesar:

| Garis | Kerugian boleh naik berapa sebelum rugi |
|---|---|
| **16% — terpilih** | **132%** |
| 40% | 84% |

Dan kenaikan sebesar itu bukan hal mustahil. Di data ini sendiri, default rate naik dari 12,3% ke 14,9% dalam dua tahun, tanpa ada krisis.

**Uangnya bukan milik sendiri.** Bank meminjamkan uang penabung. Pemilik usaha pribadi boleh memilih untung besar dengan risiko besar — kalau rugi, yang hilang uangnya sendiri. Bank tidak boleh berjudi dengan tabungan orang lain.

Jadi pertanyaannya bukan "berapa untungnya di tahun biasa", tapi **"apakah masih bertahan di tahun terburuk"**.

### Harga kehati-hatian

Memilih 16% alih-alih 40% berarti melepas sekitar **$36,7 juta** kontribusi. Itu harga yang dibayar untuk portfolio yang lebih tahan guncangan.

### Batas 10% itu dari mana

Dari keputusan kebijakan, bukan perhitungan. Di bank, angka seperti ini ditetapkan **direksi dan komisaris** dalam dokumen resmi, berdasarkan modal yang dimiliki, target keuntungan, aturan regulator, dan perkiraan kondisi ekonomi.

Tugas analis bukan menentukan angkanya, tapi **menyajikan akibat dari setiap pilihan**:

| Kalau batasnya | Garis | Disetujui |
|---|---|---|
| Lebih ketat | lebih rendah | lebih sedikit |
| 10% | 16% | 67,7% |
| Lebih longgar | lebih tinggi | lebih banyak |

---

## Temuan 2 — Kebijakan tidak bertahan setahun

Garis 16% dipilih dengan data 2014, di mana gagal bayarnya 9,9% — pas di bawah batas.

Diterapkan ke pinjaman 2015, hasilnya **10,7%**. Melewati batas.

### Ini bukan kegagalan

Penyebabnya bukan model rusak — urutannya masih baik. Yang terjadi: pemohon 2015 lebih berisiko, dan angka PD ikut meleset ke bawah. Garis yang sama meloloskan orang yang lebih berisiko dari perkiraan.

Di bank, inilah yang memicu **peninjauan kebijakan**. Bukan hal luar biasa — justru rutin.

Dan justru inilah bukti paling kuat project ini: **kebijakan kredit perlu ditinjau berkala.** Bukan sekadar mengutip praktik industri, tapi menunjukkannya terjadi di data sendiri.

### Empat tindakan yang dilakukan bank

Dari yang paling murah:

| Tindakan | Artinya | Kapan dipakai |
|---|---|---|
| 1. Geser garis batas | Perketat dari 16% jadi 14% | Risiko naik, urutan masih bagus |
| 2. **Koreksi angka PD** | Geser semua PD, rumus tidak disentuh | Urutan bagus, angka meleset merata |
| 3. Latih ulang | Variabel sama, data baru | Pola hubungannya berubah |
| 4. Bangun ulang | Variabel baru, mungkin metode baru | Model tidak bisa diselamatkan |

Project ini melakukan **tindakan 2**.

---

## Keputusan 9 — Koreksi kalibrasi

Karena kesepuluh kelompok risiko meleset ke **arah yang sama**, ini jenis masalah yang bisa dikoreksi. Ibarat timbangan yang titik nolnya bergeser, bukan timbangan yang rusak.

Caranya: cari satu angka penggeser dari data 2014, lalu naikkan semua PD dengan angka itu. Rumus model tidak disentuh sama sekali.

### Hasilnya

| | Sebelum | Sesudah |
|---|---|---|
| Meleset di 2014 | +0,84 poin | **+0,00 poin** |
| Meleset di 2015 | +2,13 poin | **+1,31 poin** |
| Urutan (AUC) | 0,6655 | **0,6655** |

AUC identik sampai empat angka desimal — bukti bahwa yang bergeser cuma levelnya.

### Tidak sembuh total, dan itu pun temuan

Penggesernya dihitung dari 2014, ketika model meleset 0,84 poin. Tapi di 2015 sudah meleset 2,13 poin — **pergeserannya terus berjalan**.

Kesimpulannya: koreksi berkala saja tidak cukup kalau populasinya terus berubah. Yang dibutuhkan pemantauan rutin agar koreksinya bisa diperbarui.

### Yang tidak berubah: keputusan

| | Sebelum koreksi | Sesudah koreksi |
|---|---|---|
| Angka garis batas | 15% | 16% |
| Jumlah yang disetujui | 191.316 | 191.460 |
| Gagal bayar di 2015 | 10,6% | 10,7% |

Angka garisnya berubah, tapi **orang yang disetujui hampir sama persis** — selisihnya 144 dari 282 ribu.

Masuk akal: keputusan terima-tolak bekerja dengan **urutan**, dan urutan tidak tersentuh.

> **Koreksi kalibrasi memperbaiki angka, bukan keputusan.**

---

## Dampak dalam bentuk uang

Di data 2015, dengan garis 16%:

| | |
|---|---|
| Uang yang disalurkan | $2.703,3 juta |
| Kerugian yang diperkirakan model | $124,5 juta |
| Kerugian yang sebenarnya terjadi | $149,4 juta |
| **Kurang disiapkan** | **$24,9 juta — 20%** |

Sebelum koreksi kalibrasi, kekurangannya 28%. Koreksi menutup sekitar sepertiganya.

### Kenapa 20%, padahal PD cuma meleset 2 poin

Karena **yang disetujui justru kelompok paling aman**, dan di situlah melesetnya paling parah secara persentase:

| Kelompok | Perkiraan | Kenyataan | Meleset |
|---|---|---|---|
| Paling aman | 3,26% | 4,41% | **sepertiga** |
| Paling berisiko | 26,50% | 29,72% | seperdelapan |

**Rata-rata menyembunyikan di mana letak masalahnya.**

### Apa yang dilakukan bank terhadap kekurangan ini

Empat tingkat:

| Tingkat | Tindakan | Kecepatan |
|---|---|---|
| 1 | Koreksi kalibrasi | Cepat — sudah dilakukan |
| 2 | **Tambah margin kehati-hatian** | Cepat, dan paling sering dipakai |
| 3 | Sesuaikan dengan perkiraan ekonomi | Sedang |
| 4 | Latih ulang dengan data terbaru | Lambat |

Tingkat 2 layak dijelaskan. Kalau sudah diketahui modelnya meleset 20% ke bawah, bank **tidak memakai angka model apa adanya** — ditambahkan buffer:

| | |
|---|---|
| Perkiraan model | $124,5 juta |
| Ditambah buffer 25% | **$155,6 juta** |
| Kenyataan | $149,4 juta |

Tertutup. Aturannya sederhana: **kalau ragu, bulatkan ke atas.** Menyisihkan terlalu banyak cuma membuat laba terlihat lebih kecil. Menyisihkan terlalu sedikit membuat kerugian muncul mendadak — dan itu jauh lebih berbahaya.

Tingkat 3 diwajibkan aturan akuntansi Indonesia, PSAK 71: cadangan kerugian harus bersifat **forward looking**, menyesuaikan perkiraan kondisi ekonomi ke depan. Project ini tidak punya variabel ekonomi, jadi bagian itu tercatat sebagai keterbatasan.

---

## Biaya yang tidak muncul di laporan keuangan

Di data 2015, dengan garis 16%:

| | Jumlah |
|---|---|
| Disetujui, ternyata lunas | 171.077 |
| Disetujui, ternyata gagal bayar | 20.383 |
| **Ditolak, padahal akan lunas** | **69.621** |
| Ditolak, memang gagal bayar | 21.706 |

Baris ketiga itu yang jarang dibahas. **69.621 orang yang akan membayar lunas ikut ditolak** — sekitar **3,2 orang baik untuk setiap satu gagal bayar yang dihindari**.

Pemberi pinjaman tidak pernah tahu jumlahnya, karena tidak pernah meminjamkan uang ke mereka. Tidak ada catatan yang mencatat "untung yang tidak jadi didapat".

Analisis threshold biasa hanya menampilkan manfaatnya. Menampilkan biayanya juga adalah cara berpikir yang diharapkan dari analis kredit.

---

## Batas penggunaan model

| Boleh dipakai untuk | Alasan |
|---|---|
| Mengurutkan pemohon dari yang paling aman | Urutan terbukti bertahan lintas waktu |
| Keputusan terima-tolak | Hanya butuh urutan |
| Memberi alasan penolakan | Rumusnya bisa dibaca dan dilacak |
| Simulasi kebijakan | Semua angka dari data yang sama |

| Tidak boleh dipakai untuk | Alasan |
|---|---|
| Menghitung cadangan tanpa koreksi | Meleset 20% ke bawah |
| Pinjaman tenor 60 bulan | Model tidak pernah melihatnya |
| Pengajuan bersama | Dibuang dari data |
| Produk kredit lain | KPR, kartu kredit, kredit usaha punya pola berbeda |
| Menilai pemohon di luar populasi ini | Data dari Amerika, 2013–2015 |

---

## Keterbatasan yang diakui terbuka

| Keterbatasan | Akibatnya |
|---|---|
| Hanya berisi pemohon yang **disetujui** | Model tidak pernah melihat yang ditolak. Kesalahan model bisa memperkuat dirinya sendiri |
| Definisi gagal bayar seumur pinjaman | Data terbaru harus menunggu lama sebelum bisa dipakai |
| Tidak ada variabel ekonomi | Model tidak tahu soal pengangguran atau suku bunga acuan |
| LGD dari satu periode | Kalau kondisi penagihan berubah, angkanya ikut berubah |
| Tidak ada uji keadilan | Belum diperiksa apakah model memperlakukan kelompok tertentu tidak adil |
| Data Amerika 2013–2015 | Tidak mewakili pemohon di Indonesia |

Keterbatasan yang dinyatakan terbuka jauh lebih meyakinkan daripada angka yang tampak sempurna.

---

## Kalau dipakai di bank Indonesia

| Bagian project ini | Padanannya di Indonesia |
|---|---|
| Skor FICO | Data SLIK OJK |
| Definisi hapus buku | Kolektibilitas 3, 90 hari menunggak |
| Batas risiko | Risk Appetite Statement yang disetujui direksi |
| Cadangan kerugian | CKPN menurut PSAK 71, dengan penyesuaian forward looking |
| Alasan penolakan | Tuntutan transparansi dalam panduan AI perbankan OJK |
| Pemantauan model | Unit validasi model yang independen |

---

## Ringkasan seluruh keputusan

| Keputusan | Alasan | Bukti |
|---|---|---|
| Gagal bayar = hapus buku | Satu-satunya yang tersedia di data | Selisih dengan OJK sekitar satu bulan |
| Hanya tenor 36 bulan | Tenor 60 bulan datanya terpotong | Terlihat 6 poin lebih berisiko dari seharusnya |
| Buang suku bunga dan grade | Penilaian pihak lain, belum ada saat keputusan | Kalibrasi memburuk dari +2,13 ke +4,01 poin |
| Buang lokasi | Risiko diskriminasi | Sejalan dengan perhatian OJK soal bias algoritma |
| Uji berdasarkan tahun | Model dipakai ke masa depan | Pembagian acak menyembunyikan pergeseran 2 poin |
| 19 variabel, bukan 67 | Harus bisa dijelaskan | Harga: 0,014 AUC |
| Logistic Regression | Rumus bisa dibaca, regulator menuntut | Harga: 0,014 AUC |
| LGD dan EAD dari data | Tebakan lama meleset | 51,2%, bukan 65% |
| Garis dari batas risiko | Uang penabung, bukan uang sendiri | Bantalan 132% vs 84% |
| Pilih di 2014, uji di 2015 | Jangan membuat soal ujian sendiri | Kebijakan ternyata tidak bertahan |
| Koreksi kalibrasi | Meleset searah di semua kelompok | Kekurangan cadangan turun dari 28% ke 20% |

---

---

# BAGIAN 2 — Cara kerja programnya

## Peta besar

Program ini punya **dua lapisan file**.

**Lapisan aturan** — file di `src\` yang berisi cara melakukan sesuatu, tapi tidak pernah dijalankan sendiri. Seperti resep masakan: berisi cara memasak, tapi tidak memasak apa pun kalau tidak ada yang membacanya.

**Lapisan pelaksana** — empat file di `src\pipeline\` yang benar-benar dijalankan. Seperti juru masak: membuka resep, mengambil bahan, lalu memasak.

```
LAPISAN PELAKSANA                    LAPISAN ATURAN
(dijalankan dengan tombol Run)       (hanya dipanggil)

p1_ingest.py    ──────────────────►  config.py, db.py, preprocess.py
p2_clean.py     ──────────────────►  config.py, db.py, preprocess.py
p3_train.py     ──────────────────►  config.py, db.py, preprocess.py,
                                     split.py, features.py, model.py,
                                     metrics.py, calibration.py
p4_policy.py    ──────────────────►  config.py, db.py, features.py,
                                     split.py, policy.py, calibration.py
```

Kenapa dipisah begini? Supaya setiap aturan hanya ditulis di **satu tempat**. Cara menghitung LGD hanya ada di `policy.py`. Kalau suatu saat rumusnya berubah, cukup satu file yang disentuh.

---

## Tiga aturan main

### Aturan 1 — Semua angka ada di `config.yaml`

Kode tidak boleh menulis angka keputusan sendiri. Tidak ada `if pd < 0.16` di dalam kode. Angka 0,16 datang dari perhitungan; batas risiko 10% datang dari config.

**Kenapa:** kalau auditor bertanya "kenapa batas risikonya 10%?", jawabannya ada di satu file dengan komentar alasannya — tidak perlu membaca kode sama sekali.

### Aturan 2 — Satu pintu ke database

Hanya `src\db.py` yang boleh membuka koneksi ke PostgreSQL. File lain memanggil `db.read_table(...)`, bukan menyusun sambungan sendiri.

**Kenapa:** kalau password atau nama database berubah, cukup satu tempat yang diperbaiki. Ini juga yang menyelamatkan kita dulu waktu program diam-diam terhubung ke database project lain.

### Aturan 3 — Daftar yang diizinkan, bukan daftar yang dilarang

Model hanya melihat kolom yang **tercantum** di `config.yaml`. Bukan "semua kolom kecuali yang dilarang".

**Kenapa:** kalau satu kolom lupa didaftarkan, akibatnya cuma kehilangan satu variabel. Kalau pakai daftar larangan dan satu kolom lupa dilarang, akibatnya kebocoran data dan seluruh model tidak valid.

---

# Lapisan aturan — file per file

## `config.yaml`

**Jenis:** bukan kode, hanya daftar pengaturan.
**Dibaca oleh:** `src\config.py` saja.

Isinya tujuh bagian:

| Bagian | Isinya | Contoh |
|---|---|---|
| `data` | Lokasi file dan definisi gagal bayar | Charged Off = gagal bayar |
| `filters` | Pinjaman mana yang masuk | Hanya tenor 36 bulan |
| `split` | Tahun mana untuk apa | Latih 2013, uji 2015 |
| `columns` | Kolom mana yang boleh dilihat model | 62 kolom fitur |
| `cleaning` | Aturan pembersihan | dti di luar 0–100 dianggap kosong |
| `feature_selection` | Ambang penyaringan variabel | Buang kalau IV di bawah 0,02 |
| `model` dan `policy` | Pengaturan model dan kebijakan | Batas risiko 10% |

### Sisi kredit

Inilah yang dalam istilah perbankan disebut **dokumentasi asumsi model**. Setiap model kredit di bank wajib punya dokumen seperti ini: apa definisi gagal bayarnya, periode mana yang dipakai, variabel apa yang dikeluarkan dan kenapa.

---

## `src\config.py`

**Memanggil:** tidak ada file project lain.
**Dipanggil oleh:** semua file lain.

Tiga fungsi:

**`load()`** — membaca `config.yaml`, memeriksanya, mengembalikan isinya.

**`all_features()`** — menggabungkan tiga kelompok fitur (formulir, riwayat kredit, rincian biro) jadi satu daftar 62 nama kolom.

**`db_url()`** — menyusun alamat sambungan database dari file `.env`.

### Penjaga kebocoran

Di dalam `load()` ada pemeriksaan yang jalan **setiap kali** config dibaca:

1. Apakah ada kolom hasil — seperti `recoveries` — yang nyelonong ke daftar fitur?
2. Apakah ada kolom pembanding seperti `int_rate` di daftar fitur?
3. Apakah ada kolom yang tercantum dua kali?

Kalau salah satu terjadi, program **berhenti** dengan pesan jelas.

Saya sudah mengujinya: menyisipkan `recoveries` ke daftar fitur, dan program langsung menolak jalan.

### Sisi kredit

Kesalahan paling fatal dalam pengembangan scorecard adalah memakai informasi yang belum ada saat keputusan diambil. Penjaga ini membuat kesalahan itu **tidak mungkin terjadi diam-diam**.

Kalau ditanya di interview "bagaimana Anda mencegah kebocoran data?", jawabannya bukan "saya hati-hati", tapi "program saya menolak berjalan kalau itu terjadi".

---

## `src\db.py`

**Memanggil:** `config.py` (untuk alamat database).
**Dipanggil oleh:** keempat file pipeline.

| Fungsi | Tugasnya |
|---|---|
| `get_engine()` | Membuka sambungan, sekali saja lalu dipakai ulang |
| `run_sql_file()` | Menjalankan file `.sql` — dipakai untuk membuat tabel |
| `copy_dataframe()` | Menulis data ke tabel dengan cara cepat |
| `read_query()` | Menjalankan perintah SELECT |
| `read_table()` | Membaca seluruh isi tabel |
| `table_columns()` | Melihat kolom apa saja yang ada di sebuah tabel |
| `row_count()` | Menghitung jumlah baris |

### Kenapa `copy_dataframe` istimewa

Cara biasa menulis data ke database adalah `INSERT` — mengirim baris satu per satu sebagai perintah. Untuk 2,26 juta baris, itu sangat lambat.

`copy_dataframe` memakai **COPY**, perintah bawaan PostgreSQL untuk memuat data besar: seluruh data dikirim sebagai satu aliran teks yang diterima sekaligus.

Data dikirim per potongan 200 ribu baris supaya memori laptop tidak penuh.

---

## `src\preprocess.py`

**Memanggil:** `config.py`.
**Dipanggil oleh:** `p1_ingest.py`, `p2_clean.py`, dan `features.py`.

Ini file aturan pembersihan. Enam fungsi:

| Fungsi | Tugasnya | Dipakai di |
|---|---|---|
| `bronze_columns()` | Daftar 79 kolom yang dibaca dari CSV | p1 |
| `scope_query()` | Menyusun perintah SQL penyaringan | p2 |
| `clean()` | Membersihkan isi kolom | p2 |
| `silver_columns()` | Urutan 83 kolom tabel silver | p2 |
| `model_features()` | Nama fitur setelah dibersihkan | p3, features.py |
| `_bulan_tahun()` | Mengubah `"Dec-2015"` jadi tanggal | di dalam `clean()` |

### Yang dikerjakan `clean()`, berurutan

1. Memeriksa bahwa penyaringan di database sudah berjalan
2. Membuat pengenal baris dan mengambil tahun pencairan
3. Membuat kolom target: gagal bayar 1, lunas 0
4. `"10+ years"` jadi angka 10
5. `earliest_cr_line` jadi lama riwayat kredit dalam tahun
6. Dua kolom FICO digabung jadi satu (selisihnya selalu 4 poin — memakai keduanya berarti memasukkan informasi yang sama dua kali)
7. Kategori tempat tinggal dan tujuan pinjaman yang langka digabung
8. Nilai sentinel jadi kosong — `dti` bernilai 9999 dan `annual_inc` bernilai 0 bukan angka asli, itu penanda "data tidak ada"
9. Penanda `_missing` dibuat untuk enam kolom
10. EAD, LGD, dan `net_cash` dihitung

### Aturan paling penting di file ini

**Boleh:** mengubah satu baris tanpa melihat baris lain.
**Dilarang:** menghitung sesuatu dari sekumpulan baris, misalnya nilai tengah.

Kenapa dilarang? Kalau nilai tengah dihitung dari semua data, angka itu sudah mengandung informasi dari data uji. Informasi masa depan bocor ke proses belajar.

Pengisian kolom kosong karena itu tidak dilakukan di sini — tempatnya di dalam Pipeline, yang hanya melihat data latih.

### Sisi kredit

Penanda `_missing` layak dijelaskan. Kolom `mths_since_last_delinq` berarti "berapa bulan sejak terakhir menunggak". Kalau kosong, artinya **tidak pernah menunggak** — dan hampir separuh peminjam begitu.

Kalau langsung diisi nilai tengah, model akan diberi tahu bahwa separuh peminjam pernah menunggak sekian bulan lalu. Salah besar. Penandanya menyimpan informasi "tidak pernah" sebelum kolomnya diisi.

---

## `src\split.py`

**Memanggil:** tidak ada file project lain.
**Dipanggil oleh:** `p3_train.py` dan `p4_policy.py`.

| Fungsi | Tugasnya |
|---|---|
| `split_by_year()` | Bagi jadi latih 2013, validasi 2014, uji 2015 |
| `split_random()` | Bagi acak 80/20 — hanya sebagai pembanding |

### Sisi kredit

Ini perbaikan terbesar dari project versi pertama.

Dulu data dibagi **acak**: 80% untuk belajar, 20% untuk menguji. Masalahnya, model kredit dipakai untuk menilai pemohon **di masa depan**. Menguji dengan data acak dari periode yang sama seperti memberi ujian yang soalnya sudah bocor — model sudah pernah melihat "zaman" yang sama.

Pembagian berdasarkan tahun mencerminkan cara model benar-benar dipakai.

**Kenapa validasi dan uji dipisah?** Semua pemilihan terjadi di 2014: model mana yang dipakai, garis batas berapa, penggeser kalibrasi berapa. Data 2015 disentuh **sekali saja**, di akhir. Kalau tidak dipisah, kita akan "membuat soal ujian sendiri lalu mengerjakannya".

---

## `src\features.py`

**Memanggil:** `preprocess.py`.
**Dipanggil oleh:** `p3_train.py` dan `p4_policy.py`.

| Fungsi | Tugasnya |
|---|---|
| `prepare()` | Rapikan tipe data setelah dibaca dari database |
| `split_numeric_categorical()` | Pisahkan fitur angka dan fitur kategori |
| `split_xy()` | Ambil **hanya** kolom di daftar fitur, beserta targetnya |
| `information_value()` | Hitung IV satu variabel |
| `select_features()` | Saring 67 variabel jadi paling banyak 20 |
| `sign_flips()` | Cari variabel yang arah pengaruhnya tidak masuk akal |
| `coefficient_table()` | Susun tabel koefisien yang bisa dibaca |

### `split_xy()` — fungsi kecil yang sangat penting

Satu baris: `df[features]`. Ambil kolom yang ada di daftar, titik.

Karena inilah tabel silver boleh berisi fitur **dan** kolom hasil dalam satu tabel. Kolom `recoveries` ada di tabel yang sama, tapi tidak pernah masuk ke model — karena tidak ada di daftar.

### `information_value()` — bagaimana IV dihitung

1. Bagi peminjam jadi 10 kelompok berdasarkan nilai variabel. Nilai kosong jadi kelompok tersendiri.
2. Di tiap kelompok, hitung: berapa persen dari **seluruh yang lunas** ada di sini, dan berapa persen dari **seluruh yang gagal bayar**.
3. Makin berbeda kedua persentase itu, makin kuat variabelnya.
4. IV merangkum semua selisih jadi satu angka.

Patokan industri: di bawah 0,02 tidak berguna, di atas 0,5 patut dicurigai sebagai kebocoran.

### `select_features()` — tiga saringan

| Saringan | Cara kerjanya | Terbuang |
|---|---|---|
| IV rendah | Buang yang di bawah 0,02 | 40 |
| Kembar | Urut dari IV tertinggi. Kalau korelasi dengan yang sudah dipertahankan di atas 0,7, buang | 7 |
| Batas jumlah | Ambil 20 teratas | 0 |

Semuanya memakai **data 2013 saja**.

### `sign_flips()` — pemeriksaan akal sehat

Setelah model dilatih, setiap variabel angka diperiksa: apakah arah pengaruhnya di dalam model sama dengan arah pengaruhnya kalau dilihat sendirian?

Contoh nyata dari project Anda: `total_rev_hi_lim` adalah total limit kartu kredit. Dilihat sendiri, limit besar berarti aman. Tapi di dalam model koefisiennya keluar terbalik.

Penyebabnya ada dua variabel lain yang sangat mirip, dan model membagi pengaruhnya dengan cara aneh. Koefisien seperti itu tidak bisa dijelaskan ke komite kredit, jadi variabelnya dibuang lalu model dilatih ulang. Diulang sampai semua arahnya masuk akal.

### Sisi kredit

Ketiga saringan ini adalah **praktik standar pengembangan scorecard**, bukan buatan saya. IV dan pemeriksaan arah koefisien adalah dua hal pertama yang ditanyakan validator model di bank.

---

## `src\model.py`

**Memanggil:** tidak ada file project lain.
**Dipanggil oleh:** `p3_train.py`.

| Fungsi | Tugasnya |
|---|---|
| `build_preprocessor()` | Susun pengolahan kolom angka dan kategori |
| `build_estimator()` | Pilih satu dari tiga jenis model |
| `build_pipeline()` | Gabungkan keduanya jadi satu kesatuan |

### Apa itu Pipeline

Rangkaian langkah yang dijalankan berurutan sebagai satu benda:

**Untuk kolom angka:** isi yang kosong dengan nilai tengah → seragamkan skala.
**Untuk kolom kategori:** isi yang kosong dengan nilai tersering → ubah jadi kolom 0/1.
**Lalu:** jalankan model.

### Kenapa harus di dalam Pipeline

Pipeline hanya belajar dari data yang diberikan saat melatih. Nilai tengah untuk mengisi kolom kosong dihitung dari **2013 saja**. Data 2015 tidak mungkin ikut.

Ini bukan soal kerapian kode — ini jaminan mekanis bahwa kebocoran tidak terjadi.

### Dua pengaturan yang disengaja

**`class_weight` dibiarkan kosong.** Ada pengaturan bernama "balanced" yang menaikkan kemampuan menangkap gagal bayar. Tapi cara kerjanya dengan **menggeser semua probabilitas secara sistematis** — sehingga angka yang keluar bukan PD lagi, dan tidak bisa dikalikan dengan LGD dan EAD.

Yang benar: jangan otak-atik probabilitasnya, otak-atik garis batasnya.

**`handle_unknown="ignore"`.** Kalau muncul kategori di 2015 yang tidak ada di 2013, prediksi tidak gagal — kategorinya diperlakukan sebagai kategori acuan.

---

## `src\metrics.py`

**Memanggil:** tidak ada file project lain.
**Dipanggil oleh:** `p3_train.py`.

| Fungsi | Mengukur apa |
|---|---|
| `evaluate()` | Semua metrik sekaligus |
| `ks_statistic()` | Jarak terlebar antara sebaran yang lunas dan yang gagal |
| `calibration_table()` | Perkiraan vs kenyataan, per tingkat risiko |
| `vintage_table()` | Perkiraan vs kenyataan, per tahun |

### Dua hal berbeda yang diukur

**Diskriminasi** — apakah **urutan** risikonya benar? Diukur dengan AUC, KS, Gini.

**Kalibrasi** — apakah **angka** PD-nya sesuai kenyataan? Diukur dengan Brier score dan selisih rata-rata.

### Sisi kredit

Pemisahan ini adalah inti seluruh project.

| Keperluan | Butuh apa |
|---|---|
| Keputusan terima-tolak | **Urutan** — angka boleh meleset |
| Menghitung cadangan kerugian | **Angka yang tepat** |

Mengurutkan tidak butuh angka yang tepat. Mengalikan dengan uang butuh.

`calibration_table()` membagi pinjaman jadi 10 kelompok dari PD terendah. Bentuk selisihnya membawa informasi diagnostik:

- **Searah di semua kelompok** → pergeseran level. Bisa dikoreksi.
- **Berganti arah** → bentuk model salah. Perlu ditinjau ulang.

Di project Anda, kesepuluh kelompok searah. Itu yang membuat koreksi kalibrasi layak dilakukan.

---

## `src\calibration.py`

**Memanggil:** tidak ada file project lain.
**Dipanggil oleh:** `p3_train.py` (menghitung) dan `p4_policy.py` (memakai).

| Fungsi | Tugasnya |
|---|---|
| `fit_offset()` | Cari satu angka penggeser dari data validasi |
| `apply_offset()` | Terapkan penggeser ke sekumpulan PD |
| `summarize()` | Ringkasan sebelum dan sesudah |

### Kenapa digeser di skala log-odds

Cara paling sederhana menggeser PD adalah menambahkan angka, misalnya semua ditambah 2%. Tapi PD 99% akan jadi 101% — tidak punya arti.

Skala log-odds punya tiga sifat yang dibutuhkan:

1. Hasilnya selalu antara 0% dan 100%
2. Yang rendah digeser lebih banyak daripada yang tinggi
3. **Urutannya tidak berubah sedikit pun**

Sifat ketiga bisa dibuktikan: AUC sebelum dan sesudah koreksi identik sampai empat angka desimal.

### Sisi kredit

Ini tindakan kedua dari empat yang dilakukan bank ketika model bergeser:

| Tindakan | Artinya | Kapan dipakai |
|---|---|---|
| 1. Geser garis batas | Ubah 16% jadi 14% | Risiko naik, urutan masih bagus |
| 2. **Koreksi angka** | Geser semua PD | Urutan bagus, angkanya meleset merata |
| 3. Latih ulang | Variabel sama, data baru | Pola hubungannya berubah |
| 4. Bangun ulang | Variabel baru | Model tidak bisa diselamatkan |

Penggesernya dihitung dari data 2014, bukan 2015 — prinsipnya sama seperti pemilihan fitur dan garis batas.

---

## `src\policy.py`

**Memanggil:** tidak ada file project lain.
**Dipanggil oleh:** `p4_policy.py`.

| Fungsi | Tugasnya |
|---|---|
| `loss_parameters()` | Hitung LGD dan EAD dari data latih |
| `decide()` | Terapkan garis batas |
| `evaluate_cutoff()` | Hitung seluruh dampak dari satu garis |
| `sweep()` | Coba semua garis dari 2% sampai 40% |
| `choose_cutoff()` | Pilih yang paling untung di antara yang aman |
| `stress_test()` | Seberapa tebal bantalannya kalau memburuk |

### Rumus yang dipakai

```
EAD  = funded_amnt - total_rec_prncp
       uang yang masih di tangan peminjam saat berhenti membayar

LGD  = 1 - (recoveries - collection_recovery_fee) / EAD
       dari sisa itu, berapa yang benar-benar hilang

Perkiraan kerugian = PD x LGD x EAD
Kerugian sebenarnya = EAD x LGD, dijumlahkan dari yang gagal bayar
Kontribusi = total_pymnt - collection_recovery_fee - funded_amnt
```

### Dua angka kerugian yang dibandingkan

**Perkiraan** memakai LGD dan EAD dari **data latih**, karena untuk pemohon baru kita belum tahu berapa yang akan hilang.

**Kenyataan** memakai angka tiap pinjaman yang benar-benar terjadi.

Selisih keduanya menunjukkan akibat PD yang meleset, **dalam bentuk uang**.

### Sisi kredit

Angka LGD 0,886 dan EAD 0,577 layak dipahami:

**EAD 0,577** — saat berhenti membayar, peminjam rata-rata masih memegang 57,7% dari pinjamannya. Sisanya sudah dicicil. Bank tidak kehilangan seluruh pinjaman.

**LGD 0,886** — dari sisa itu, 88,6% memang hilang. Penagihan tidak banyak menolong; 30,7% pinjaman gagal bayar tidak menghasilkan pemulihan sama sekali.

Dikalikan: kerugian sekitar **51,2%** dari yang dipinjamkan.

**Batas risiko** — maksimal 10 dari 100 yang disetujui boleh gagal bayar — adalah keputusan kebijakan, bukan hasil perhitungan. Di bank ditetapkan direksi, bukan analis. Tugas analis adalah menyajikan akibat dari setiap pilihan.

---

# Lapisan pelaksana — empat tahap

## Tahap 1 — `p1_ingest.py`

**Memanggil:** `config.py`, `db.py`, `preprocess.py`
**Membaca:** `data\raw\accepted_2007_to_2018Q4.csv`, `sql\01_bronze.sql`
**Menghasilkan:** tabel `bronze_loans_raw`

Urutannya:

1. Ambil daftar 79 kolom dari `preprocess.bronze_columns()`
2. Baca CSV, hanya kolom itu saja
3. Buang beberapa baris ringkasan di akhir file — itu bukan pinjaman
4. Pastikan kolom angka memang berisi angka. Kalau ada yang gagal diubah, jumlahnya dilaporkan
5. Jalankan `sql\01_bronze.sql` untuk membuat tabel
6. Tulis dengan COPY

**Hasil:** 2.260.668 baris, sekitar 4 menit.

### Kenapa semua baris disimpan

Bronze berisi **semua** pinjaman, termasuk tenor 60 bulan dan yang masih berjalan — padahal tidak dipakai. Gunanya: kalau suatu saat cakupan berubah, data tidak perlu dimuat ulang dari CSV 1,6 GB.

### Sisi kredit

Lapisan bronze adalah **jejak audit**. Kapan pun ada yang mempertanyakan angka di silver, bisa ditelusuri kembali ke data mentahnya tanpa bergantung pada file asli.

---

## Tahap 2 — `p2_clean.py`

**Memanggil:** `config.py`, `db.py`, `preprocess.py`
**Membaca:** tabel `bronze_loans_raw`, `sql\02_silver.sql`
**Menghasilkan:** tabel `silver_loans_clean`

Urutannya:

1. `preprocess.scope_query()` menyusun perintah SQL penyaringan
2. Jalankan di database — hanya baris yang lolos yang dikirim ke Python
3. `preprocess.clean()` membersihkan isinya
4. Jalankan `sql\02_silver.sql` untuk membuat tabel
5. **Periksa** kolom tabel sama persis dengan hasil pembersihan. Kalau tidak, program berhenti dengan pesan jelas
6. Tulis dengan COPY
7. Laporkan ringkasan per tahun dan tabel tujuan pinjaman

### Pembagian kerja yang disengaja

Dari 2,26 juta baris bronze, hanya 545.779 yang masuk cakupan. Mengirim semuanya ke Python lalu membuang tiga perempatnya itu boros.

**SQL memilih baris. Python mengubah isinya.**

### Sisi kredit

Di sini cakupan produk ditetapkan lewat tiga penyaring:

| Penyaring | Alasannya |
|---|---|
| Hanya yang sudah selesai | Yang masih berjalan belum ketahuan hasilnya |
| Hanya perorangan | Pengajuan bersama punya kolom berbeda, cuma 5% data |
| Hanya tenor 36 bulan | Tenor 60 bulan dari 2014–2015 baru 67–83% selesai, sehingga angkanya menyesatkan |

**Hasil:** 545.779 pinjaman, 83 kolom, sekitar 2 menit.

---

## Tahap 3 — `p3_train.py`

**Memanggil:** `config.py`, `db.py`, `preprocess.py`, `split.py`, `features.py`, `model.py`, `metrics.py`, `calibration.py` — delapan file
**Membaca:** tabel `silver_loans_clean`
**Menghasilkan:** empat file di `artifacts\`

Urutannya:

**1. Baca dan bagi data**
`db.read_table()` → `features.prepare()` → `split.split_by_year()`

**2. Pilih fitur**
`features.select_features()` dengan data 2013 saja. Dari 67 jadi 20.

**3. Latih model utama, periksa arah koefisien**
Latih → `features.sign_flips()` → kalau ada yang terbalik, buang yang IV-nya paling rendah → latih ulang. Diulang sampai bersih. Hasilnya 19 fitur.

**4. Latih tiga pembanding**

| Pembanding | Menjawab |
|---|---|
| Model utama, pembagian acak | Seberapa beda kalau diuji dengan cara yang salah? |
| Model utama + suku bunga | Seberapa bergantung pada penilaian Lending Club? |
| Random Forest dan Gradient Boosting, 67 fitur | Berapa akurasi yang dikorbankan demi bisa dijelaskan? |

**5. Hitung koreksi kalibrasi**
`calibration.fit_offset()` dengan data 2014.

**6. Periksa kalibrasi**
`metrics.calibration_table()` dan `metrics.vintage_table()`, sebelum dan sesudah koreksi.

**7. Simpan empat file**

| File | Isinya | Dibaca oleh |
|---|---|---|
| `model.pkl` | Model utama | p4, nanti API |
| `feature_meta.json` | Daftar fitur dan penggeser kalibrasi | p4, nanti API |
| `feature_selection.json` | Nasib setiap dari 67 variabel | nanti model card |
| `metrics.json` | Semua angka evaluasi | nanti model card |

**Waktu:** sekitar 5 menit. Yang paling lama Gradient Boosting dengan 67 fitur.

### Sisi kredit

Di sinilah **keputusan paling penting** project diambil: membuang suku bunga dan grade.

Keduanya adalah penilaian risiko Lending Club sendiri. Memakainya bukan memprediksi risiko — itu menyontek jawaban orang lain. Dan saat aplikasi baru masuk, bunganya belum ada.

Buktinya ada di angka: menambahkan suku bunga menaikkan AUC 0,027, tapi membuat kalibrasi **hampir dua kali lebih buruk** — dari +2,13 jadi +4,01 poin.

`feature_selection.json` adalah **dokumentasi pemilihan variabel**. Di bank, dokumen seperti ini wajib ada dan diperiksa validator.

---

## Tahap 4 — `p4_policy.py`

**Memanggil:** `config.py`, `db.py`, `features.py`, `split.py`, `policy.py`, `calibration.py`
**Membaca:** tabel `silver_loans_clean`, `artifacts\model.pkl`, `artifacts\feature_meta.json`
**Menghasilkan:** `artifacts\policy.json`

Urutannya:

1. Muat model dan daftar fiturnya
2. Baca data, bagi per tahun
3. `policy.loss_parameters()` → LGD dan EAD dari data 2013
4. Hitung PD untuk 2014 dan 2015, lalu **koreksi** dengan penggeser dari `feature_meta.json`
5. `policy.sweep()` di data 2014 → coba semua garis batas
6. `policy.choose_cutoff()` → pilih yang paling untung di antara yang aman
7. Terapkan garis itu ke data 2015 dengan `policy.evaluate_cutoff()`
8. Kalau melewati batas, cetak penjelasan dan garis yang seharusnya dipakai
9. `policy.stress_test()` → uji ketahanan
10. Simpan `policy.json`

### Pemisahan memilih dan menilai

**Memilih** memakai data 2014. **Menilai** memakai data 2015 yang belum tersentuh.

Kalau keduanya di data yang sama, hasilnya pasti terlihat bagus — dan tidak membuktikan apa pun.

### Sisi kredit

Hasilnya: kebijakan yang dirancang di 2014 **melewati batas** di 2015 — 10,7% versus batas 10%.

Ini bukan kegagalan. Ini gambaran nyata tentang kenapa kebijakan kredit perlu ditinjau berkala. Penyebabnya bukan model rusak — urutannya masih baik. Yang terjadi: kualitas pemohon menurun.

**Waktu:** sekitar 30 detik.

---

# Artefak dan siapa yang membacanya

Lima file di `artifacts\`. Folder ini **tidak ikut ke GitHub** — isinya bisa dibuat ulang kapan saja dengan menjalankan pipeline.

| File | Dihasilkan | Dibaca sekarang | Nanti dibaca |
|---|---|---|---|
| `model.pkl` | p3 | p4 | API |
| `feature_meta.json` | p3 | p4 | API |
| `feature_selection.json` | p3 | — | Halaman model card |
| `metrics.json` | p3 | — | Halaman model card |
| `policy.json` | p4 | — | Halaman kebijakan kredit |

Inilah yang menghubungkan pekerjaan sejauh ini dengan aplikasi web nanti: **aplikasi tidak menyentuh database sama sekali.** Ia hanya membaca kelima file ini.

Itu sebabnya database bisa tetap di laptop sementara aplikasinya berjalan di server.

---

# Kalau ingin mengubah sesuatu, sentuh file mana

| Yang ingin diubah | File | Perlu jalankan ulang |
|---|---|---|
| Batas risiko dari 10% jadi 12% | `config.yaml` | p4 |
| Tahun latih, validasi, atau uji | `config.yaml` | p2, p3, p4 |
| Variabel yang boleh dipakai model | `config.yaml` | p3, p4 |
| Ambang IV atau korelasi | `config.yaml` | p3, p4 |
| Tujuan pinjaman yang dipertahankan | `config.yaml` | p2, p3, p4 |
| Cakupan produk, misalnya tenor | `config.yaml` **dan** `sql\02_silver.sql` | p2, p3, p4 |
| Cara membersihkan kolom | `src\preprocess.py` | p2, p3, p4 |
| Rumus LGD atau untung | `src\policy.py` | p4 |
| Jenis model | `src\model.py` | p3, p4 |

Perhatikan kolom kedua: **hampir semuanya cukup mengubah `config.yaml`**. Itu memang tujuannya.

---

# Istilah

| Istilah | Artinya |
|---|---|
| **Bronze** | Lapisan data mentah, apa adanya |
| **Silver** | Lapisan data bersih, siap dipakai |
| **Fitur / variabel** | Satu potong informasi tentang pemohon |
| **Target** | Yang ingin diprediksi — di sini gagal bayar atau tidak |
| **IV** | Seberapa kuat satu variabel membedakan yang lunas dan yang gagal |
| **Koefisien** | Besar pengaruh satu variabel. Negatif = makin aman |
| **AUC** | Dari 100 pasang pinjaman, berapa pasang yang urutannya benar |
| **Pipeline** | Rangkaian pengolahan yang dijalankan sebagai satu kesatuan |
| **PD** | Peluang gagal bayar |
| **EAD** | Sisa uang di tangan peminjam saat berhenti membayar |
| **LGD** | Dari sisa itu, berapa yang benar-benar hilang |
| **Diskriminasi** | Apakah urutan risikonya benar |
| **Kalibrasi** | Apakah angka PD-nya sesuai kenyataan |
| **Garis batas / cut-off** | Angka PD yang memisahkan diterima dan ditolak |
| **Risk appetite** | Batas risiko yang bersedia ditanggung |
| **Kontribusi** | Uang yang kembali dikurangi uang yang keluar |
| **Kebocoran data** | Model melihat informasi yang belum ada saat keputusan diambil |
| **COPY** | Perintah PostgreSQL untuk memuat data besar dengan cepat |
