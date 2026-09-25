/* Credit Policy Engine -- sisi tampilan.
 *
 * Tugas file ini cuma dua: meminta angka ke API, lalu menampilkannya.
 * Tidak ada perhitungan risiko di sini sama sekali. Semua hitungan
 * dilakukan di Python, supaya angka yang tampil di layar persis sama
 * dengan angka di artifacts/ -- tidak mungkin berbeda.
 *
 * Susunannya:
 *   1. Alat bantu       angka, persen, uang
 *   2. Hubungan ke API  satu fungsi untuk semua permintaan
 *   3. Halaman 1        penilaian satu pemohon
 *   4. Halaman 2        kebijakan kredit, dengan slider
 *   5. Halaman 3        model card
 *   6. Penggerak        pindah halaman, muat pertama kali
 */

/* ================= 1. Alat bantu ================= */

const angka = (n, d = 0) =>
  Number(n).toLocaleString('id-ID', { minimumFractionDigits: d, maximumFractionDigits: d });

const persen = (n, d = 1) => angka(n * 100, d) + '%';

const juta = (n) => '$' + angka(n / 1e6, 1) + ' jt';

const poin = (n) => (n >= 0 ? '+' : '') + angka(n, 2) + ' pp';

/** Angka biasa: besar dibulatkan, kecil dibiarkan berkoma. */
const nilai = (v) => {
  if (typeof v !== 'number') return v;
  if (Math.abs(v) >= 1000) return angka(v);
  return angka(v, Number.isInteger(v) ? 0 : 1);
};

const el = (id) => document.getElementById(id);

const escapeHtml = (s) => String(s).replace(/[&<>"]/g,
  (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));

/* ================= 2. Hubungan ke API ================= */

/** Satu pintu untuk semua permintaan ke API, termasuk penanganan error. */
async function api(path, body) {
  const opt = body
    ? { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) }
    : {};
  const res = await fetch(path, opt);
  if (!res.ok) {
    let pesan = res.statusText;
    try { pesan = (await res.json()).detail || pesan; } catch (e) { /* biarkan */ }
    throw new Error(pesan);
  }
  return res.json();
}

function tampilkanError(e) {
  el('err-box').innerHTML =
    `<div class="err"><b>Gagal memuat.</b> ${escapeHtml(e.message)}<br>
     Kalau berkas halaman baru saja diganti, tekan Ctrl+F5 untuk memuat ulang.</div>`;
}

/* ================= 3. Halaman 1: Penilaian aplikasi ================= */

let formFields = [];

/** Bangun formulir dari keterangan yang diberikan API. */
async function muatForm() {
  formFields = await api('/api/application/form');

  const isian = formFields.map((f) => {
    if (f.type === 'pilihan') {
      const opsi = f.options.map((o) =>
        `<option value="${escapeHtml(o.value)}"${o.value === f.default ? ' selected' : ''}>
           ${escapeHtml(o.label)}</option>`).join('');
      return `<div class="fld"><label>${escapeHtml(f.label)}</label>
              <select data-f="${f.name}">${opsi}</select></div>`;
    }
    // Rentang ditampilkan supaya pengguna tahu nilai yang wajar
    return `<div class="fld">
              <label>${escapeHtml(f.label)}
                <span class="hint">${nilai(f.p25)}-${nilai(f.p75)}</span></label>
              <input type="number" data-f="${f.name}" value="${f.default}" step="any">
            </div>`;
  }).join('');

  // Satu kolom, supaya semua kotak isian lurus sejajar ke bawah.
  el('p1-form').innerHTML = `<div class="fgrid">${isian}</div>`;

  el('p1-go').disabled = false;
  gambarStripKosong();
}

/** Papan keputusan dalam keadaan belum diisi.
 *  Ditampilkan sejak awal supaya tinggi halaman tidak melompat saat
 *  hasil pertama muncul. */
function gambarStripKosong() {
  el('p1-strip').innerHTML = `
    <div class="strip kosong">
      <div class="c"><div class="k">Keputusan</div>
        <div class="v">&mdash;</div><div class="s">Belum dinilai</div></div>
      <div class="c"><div class="k">Probability of default</div>
        <div class="v">&mdash;</div><div class="s">Isi formulir, lalu klik Nilai aplikasi</div></div>
    </div>`;
}

/** Kumpulkan isian formulir menjadi satu objek. */
function bacaForm() {
  const app = {};
  document.querySelectorAll('#p1-form [data-f]').forEach((input) => {
    const nama = input.dataset.f;
    app[nama] = input.type === 'number' ? Number(input.value) : input.value;
  });
  return app;
}

async function nilaiPemohon() {
  const tombol = el('p1-go');
  tombol.disabled = true;
  tombol.textContent = 'Menghitung...';

  try {
    const r = await api('/api/application/score', { application: bacaForm() });
    gambarHasil(r);
  } catch (e) {
    tampilkanError(e);
  } finally {
    tombol.disabled = false;
    tombol.textContent = 'Nilai aplikasi';
  }
}

function gambarHasil(r) {
  // --- papan keputusan
  el('p1-strip').innerHTML = `
    <div class="strip">
      <div class="c">
        <div class="k">Keputusan</div>
        <div class="v${r.approved ? '' : ' alert'}">${r.decision}</div>
        <div class="s">Batas PD ${persen(r.cutoff, 0)}</div>
      </div>
      <div class="c">
        <div class="k">Probability of default</div>
        <div class="v">${persen(r.pd)}</div>
        <div class="s">Sebelum koreksi kalibrasi: ${persen(r.pd_uncalibrated)}</div>
      </div>
    </div>`;

  // --- faktor penentu: empat alasan diberi kode, sisanya tetap ditampilkan
  const kode = {};
  r.reason_codes.forEach((x) => { kode[x.feature] = x.code; });
  const maks = Math.max(...r.contributions.map((c) => Math.abs(c.contribution)), 0.01);

  // Hanya sepuluh faktor terbesar yang ditampilkan. Sisanya pengaruhnya
  // kecil dan cuma memanjangkan tabel; jumlahnya tetap disebut di bawah.
  const BATAS = 8;
  const urut = [...r.contributions].sort(
    (a, b) => Math.abs(b.contribution) - Math.abs(a.contribution));
  const tampil = urut.slice(0, BATAS);
  const sisa = urut.slice(BATAS);
  const sisaTotal = sisa.reduce((t, c) => t + c.contribution, 0);

  const baris = tampil.map((c) => {
    const lebar = (Math.abs(c.contribution) / maks) * 50;
    const bar = c.contribution >= 0
      ? `<i class="p" style="width:${lebar}%"></i>`
      : `<i class="m" style="left:${50 - lebar}%;width:${lebar}%"></i>`;
    return `<tr>
      <td style="width:38px">${kode[c.feature]
        ? `<span class="rc">${kode[c.feature]}</span>`
        : '<span class="rc off">&ndash;</span>'}</td>
      <td>${escapeHtml(c.reason)}</td>
      <td class="num fig" style="width:92px">${nilai(c.value)}</td>
      <td style="width:96px"><div class="kb"><div class="ax"></div>${bar}</div></td>
      <td class="num fig" style="width:58px">${c.contribution >= 0 ? '+' : ''}${angka(c.contribution, 2)}</td>
    </tr>`;
  }).join('');

  el('p1-factors').innerHTML = `
    <table><thead><tr>
      <th>Kode</th><th>Faktor</th><th class="num">Nilai</th>
      <th></th><th class="num">Pengaruh</th>
    </tr></thead><tbody>${baris}</tbody></table>
    <p class="fn">${r.reason_codes.length
      ? `Kode RC1&ndash;RC${r.reason_codes.length} adalah alasan penolakan yang
         disampaikan kepada pemohon.`
      : `Pemohon disetujui, sehingga tidak ada alasan penolakan. Tabel ini
         memperlihatkan rincian perhitungan PD.`}
    Nilai positif berarti faktor tersebut menaikkan risiko dibandingkan pemohon
    rata-rata.${sisa.length
      ? ` Ditampilkan ${BATAS} faktor dengan pengaruh terbesar dari ${urut.length};
         gabungan ${sisa.length} faktor lainnya sebesar
         ${sisaTotal >= 0 ? '+' : ''}${angka(sisaTotal, 2)}.`
      : ''}</p>`;

  // --- skenario alternatif
  const sc = r.scenarios.map((s) => `
    <tr>
      <td>${escapeHtml(s.name)}${s.affects_model ? ''
        : ' <span class="muted">(tidak mengubah PD)</span>'}</td>
      <td class="num fig" style="width:74px">${persen(s.pd)}</td>
      <td class="num" style="width:74px">
        <span class="tag ${s.approved ? 't-ok' : 't-no'}">${s.decision}</span></td>
    </tr>`).join('');
  el('p1-scenarios').innerHTML = `<table><tbody>${sc}</tbody></table>`;
}

/* ================= 4. Halaman 2: Kebijakan kredit ================= */

let sweep = null;      // seluruh tabel garis batas
let ringkas = null;    // kebijakan yang berlaku

async function muatKebijakan() {
  [sweep, ringkas] = await Promise.all([
    api('/api/policy/sweep'),
    api('/api/policy/summary'),
  ]);

  const rows = sweep.rows;
  const s = el('p2-slider');
  s.max = rows.length - 1;
  s.disabled = false;

  // Slider dimulai dari garis batas yang berlaku
  const awal = rows.findIndex((r) => Math.abs(r.cutoff - sweep.chosen_cutoff) < 1e-9);
  s.value = awal >= 0 ? awal : Math.floor(rows.length / 2);

  el('p2-hint').textContent =
    `${angka(sweep.n_total)} pemohon, diurutkan dari PD terendah`;
  el('p2-vs').textContent = `vs batas berlaku ${persen(sweep.chosen_cutoff, 0)}`;

  s.oninput = () => gambarKebijakan(rows[Number(s.value)]);
  // Penjelasan dipindahkan ke ikon di samping label, supaya tidak memakan
  // ruang tinggi halaman yang sudah sempit.
  el('p2-tip').innerHTML =
    `Ambang untuk satu pemohon: jika PD-nya di atas angka ini, pengajuannya ` +
    `ditolak. Berbeda dengan <b>batas risiko</b>, yang menilai hasil keseluruhan: ` +
    `dari seluruh pemohon yang disetujui, paling banyak ` +
    `${persen(sweep.risk_appetite, 0)} boleh gagal bayar.`;
  gambarKebijakan(rows[Number(s.value)]);
}

function gambarKebijakan(r) {
  const total = sweep.n_total;
  el('p2-out').textContent = persen(r.cutoff, 0);

  // --- batang distribusi: empat kotak hasil
  const bagian = [
    { n: r.approved_good, c: 'g1' },
    { n: r.approved_bad, c: 'g2' },
    { n: r.rejected_good, c: 'g3' },
    { n: r.rejected_bad, c: 'g4' },
  ];
  const batang = bagian.map((b) => {
    const p = b.n / total;
    // Angka hanya ditulis kalau kotaknya cukup lebar
    return `<div class="${b.c}" style="width:${p * 100}%">${p > 0.11 ? persen(p) : ''}</div>`;
  }).join('');

  const setuju = (r.approved_good + r.approved_bad) / total;
  const legenda = [
    ['k1', 'Disetujui,<br>membayar lunas', r.approved_good],
    ['k2', 'Disetujui,<br>gagal bayar', r.approved_bad],
    ['k3', 'Ditolak,<br>padahal akan lunas', r.rejected_good],
    ['k4', 'Ditolak,<br>memang gagal bayar', r.rejected_bad],
  ].map(([c, t, n]) =>
    `<div class="k ${c}"><div class="t">${t}</div><div class="n">${angka(n)}</div></div>`).join('');

  el('p2-dist').innerHTML = `
    <div class="splits">
      <div>Disetujui <b>${persen(setuju)}</b></div>
      <div>Ditolak <b>${persen(1 - setuju)}</b></div>
    </div>
    <div class="pbar">${batang}</div>
    <div class="pax"><span>PD terendah</span><span>PD tertinggi</span></div>
    <div class="keys grid4">${legenda}</div>`;

  // --- dampak portfolio dibanding garis batas yang berlaku
  const dasar = sweep.rows.find((x) => Math.abs(x.cutoff - sweep.chosen_cutoff) < 1e-9);
  const baris = [
    ['Exposure', juta(dasar.exposure), juta(r.exposure),
      juta(r.exposure - dasar.exposure)],
    ['Default rate', persen(dasar.default_rate), persen(r.default_rate),
      poin((r.default_rate - dasar.default_rate) * 100)],
    ['Kerugian sebenarnya', juta(dasar.realized_loss), juta(r.realized_loss),
      juta(r.realized_loss - dasar.realized_loss)],
    ['Kontribusi kredit', juta(dasar.contribution), juta(r.contribution),
      juta(r.contribution - dasar.contribution)],
    ['Ditolak, padahal akan lunas', angka(dasar.rejected_good), angka(r.rejected_good),
      angka(r.rejected_good - dasar.rejected_good)],
  ].map(([nama, a, b, d]) => `
    <tr><td>${nama}</td>
      <td class="num fig" style="width:130px">${a}</td>
      <td class="num fig" style="width:130px">${b}</td>
      <td class="num fig muted" style="width:130px">${d}</td></tr>`).join('');

  el('p2-impact').innerHTML = `
    <table><thead><tr><th></th>
      <th class="num">Berlaku</th><th class="num">Simulasi</th><th class="num">Selisih</th>
    </tr></thead><tbody>${baris}</tbody></table>`;

  // --- kesimpulan
  const batas = sweep.risk_appetite;
  const lewat = r.default_rate > batas;

  // Pembandingnya adalah kontribusi tertinggi DI ANTARA GARIS YANG AMAN.
  // Sebelumnya dibandingkan dengan tertinggi di seluruh tabel -- padahal
  // yang tertinggi selalu melewati batas risiko, sehingga tidak pernah
  // ada garis yang dinilai baik.
  const aman = sweep.rows.filter((x) => x.default_rate !== null && x.default_rate <= batas);
  const puncak = aman.length ? Math.max(...aman.map((x) => x.contribution)) : 0;
  let jenis, teks;

  if (lewat) {
    jenis = 'bad';
    const terlonggar = aman.length ? Math.max(...aman.map((x) => x.cutoff)) : null;
    teks = `<b>Melewati batas risiko.</b> Dengan batas PD ${persen(r.cutoff, 0)},
      sebanyak ${angka(r.n_approved)} pemohon disetujui dan ${persen(r.default_rate)}
      di antaranya gagal bayar &mdash; lebih tinggi daripada batas ${persen(batas, 0)}.
      ${terlonggar !== null ? `Batas PD paling longgar yang masih memenuhi batas risiko
      adalah ${persen(terlonggar, 0)}.` : ''}`;
  } else if (r.contribution >= puncak * 0.85) {
    jenis = 'ok';
    teks = `<b>Titik yang baik.</b> Dengan batas PD ${persen(r.cutoff, 0)},
      ${persen(r.default_rate)} pemohon yang disetujui gagal bayar &mdash; masih di
      bawah batas ${persen(batas, 0)} &mdash; dan kontribusinya mendekati yang tertinggi
      di antara batas PD yang aman.`;
  } else {
    jenis = 'warn';
    teks = `<b>Terlalu ketat.</b> Dengan batas PD ${persen(r.cutoff, 0)},
      hanya ${persen(r.default_rate)} pemohon yang disetujui gagal bayar &mdash; jauh
      di bawah batas ${persen(batas, 0)} &mdash; tetapi ${angka(r.rejected_good)} pemohon
      yang sebenarnya akan membayar lunas ikut ditolak.`;
  }

  el('p2-verdict').innerHTML = `<div class="callout ${jenis}">${teks}</div>`;
}

/* ================= 5. Halaman 3: Model card ================= */

async function muatModelCard() {
  const m = await api('/api/model/card');
  const id = m.identity, v = m.validation;

  // --- identitas
  el('p3-identity').innerHTML = [
    ['Jenis model', id.type],
    ['Metode', 'Logistic Regression'],
    ['Produk', id.product],
    ['Definisi gagal bayar', id.default_definition],
    ['Jangka penilaian', id.horizon],
    // Tanda pisah ditulis sebagai karakter langsung, bukan sebagai kode HTML.
    // Nilai di baris-baris ini diamankan dulu sebelum ditampilkan, dan
    // pengamanan itu memperlakukan kode HTML sebagai tulisan biasa -- jadi
    // kodenya akan tampil apa adanya, bukan berubah jadi tanda pisah.
    ['Data pelatihan', `${id.train_years.join(', ')} — ${angka(id.n_train)} pinjaman`],
    ['Data validasi', `${id.validation_years.join(', ')} — memilih model dan batas PD`],
    ['Data pengujian', `${id.test_years.join(', ')} — dinilai sekali di akhir`],
  ].map(([k, val]) =>
    `<div class="idr"><span>${k}</span><b>${escapeHtml(String(val))}</b></div>`).join('');

  // --- hasil validasi, ditulis sebagai kalimat
  const auc = Math.round(v.discrimination.auc * 100);
  const perkiraan = Math.round(v.calibration.mean_predicted * 1000);
  const kenyataan = Math.round(v.calibration.actual_rate * 1000);
  const tagKal = Math.abs(v.calibration.gap_pp_after) < 1 ? 't-ok' : 't-wa';

  el('p3-validation').innerHTML = `
    <table><tbody>
      <tr>
        <td style="width:120px"><span class="nw">Diskriminasi<span
          class="tt" tabindex="0">!<span class="tip">Kemampuan model membedakan yang
          akan gagal bayar dari yang akan lunas &mdash; apakah urutan risikonya benar.
          Cukup untuk keputusan terima-tolak.</span></span></span></td>
        <td>Dari 100 pasang pinjaman, model menempatkan yang gagal bayar lebih
          berisiko pada <b>${auc}</b> pasang.</td>
        <td class="num" style="width:104px"><span class="tag t-ok">memadai</span></td>
      </tr>
      <tr>
        <td><span class="nw">Kalibrasi<span class="tt" tabindex="0">!<span
          class="tip">Apakah angka PD-nya sesuai kenyataan. Dibutuhkan ketika PD
          dikalikan dengan uang, misalnya untuk menghitung cadangan
          kerugian.</span></span></span></td>
        <td>Dari 1.000 pinjaman, model memperkirakan <b>${perkiraan}</b> akan gagal
          bayar; kenyataannya <b>${kenyataan}</b>.</td>
        <td class="num"><span class="tag ${tagKal}">${poin(v.calibration.gap_pp_after)}</span></td>
      </tr>
      <tr>
        <td><span class="nw">Koreksi<span class="tt" tabindex="0">!<span
          class="tip">Model selalu memperkirakan terlalu rendah, dan melesetnya searah
          di semua tingkat risiko. Itu berarti levelnya yang bergeser, bukan urutannya
          yang salah &mdash; sehingga bisa diperbaiki dengan menggeser seluruh angka PD
          sebesar satu angka yang sama.</span></span></span></td>
        <td>Seluruh angka PD digeser dengan satu angka yang sama, dihitung dari data
          validasi. Selisihnya membaik dari ${poin(v.calibration.gap_pp_before)} menjadi
          ${poin(v.calibration.gap_pp_after)}, sementara urutan risikonya tidak berubah
          sama sekali.</td>
        <td class="num"><span class="tag t-ok">urutan tetap</span></td>
      </tr>
    </tbody></table>
    <p class="fn">Bila diuji dengan pembagian acak, selisihnya hanya
      ${v.random_split_benchmark ? poin(v.random_split_benchmark.calibration_gap_pp) : '-'}.
      Angka itu menyesatkan, karena data latih dan data uji berasal dari periode yang
      sama sehingga perubahan antarwaktu tidak terlihat.</p>`;

  el('p3-valhint').textContent = `Data pengujian ${id.test_years.join(', ')}`;

  // --- variabel: yang dipakai dan yang dibuang
  const maks = Math.max(...m.features.used.slice(0, 10).map((b) => Math.abs(b.coef)));
  // Dibatasi dua belas terbesar. Tabel dua puluh lebih baris membuat panel
  // ini jauh lebih tinggi dari panel di sebelahnya.
  const BATAS_VAR = 10;
  const semuaVar = m.features.used;
  const dipakai = semuaVar.slice(0, BATAS_VAR).map((b) => `
    <tr>
      <td>${escapeHtml(b.label)}<span class="sub">${b.base || b.feature}</span></td>
      <td class="num" style="width:38px">
        <span class="dir ${b.coef > 0 ? 'u' : 'd'}">${b.coef > 0 ? '&uarr;' : '&darr;'}</span></td>
      <td style="width:76px"><div class="str">
        <i class="${b.coef > 0 ? 'u' : 'd'}" style="width:${Math.abs(b.coef) / maks * 100}%"></i>
      </div></td>
      <td class="num fig" style="width:52px">${angka(b.coef, 2)}</td>
    </tr>`).join('');

  const dibuang = Object.entries(m.features.dropped).map(([alasan, daftar]) => `
    <div class="exc">
      <div class="h">${escapeHtml(alasan)}</div>
      <div class="c">${daftar.length} variabel</div>
      <div class="r">${daftar.slice(0, 4).map((x) => escapeHtml(x.label)).join(', ')}${
        daftar.length > 4 ? `, dan ${daftar.length - 4} lainnya` : ''}</div>
    </div>`).join('');

  const harga = m.features.excluded_by_design;
  el('p3-features').innerHTML = `
    <div class="grid2" style="align-items:start">
      <div>
        <table><thead><tr>
          <th>Variabel yang dipakai</th><th class="num">Arah</th>
          <th>Kekuatan</th><th class="num">Koefisien</th>
        </tr></thead><tbody>${dipakai}</tbody></table>
        ${semuaVar.length > BATAS_VAR
          ? `<p class="fn">Ditampilkan ${BATAS_VAR} baris teratas dari
             ${semuaVar.length}, diurutkan menurut Information Value &mdash; ukuran
             seberapa kuat sebuah variabel membedakan pemohon yang lunas dan yang gagal
             bayar. Variabel kategori dipecah menjadi satu baris untuk setiap pilihan,
             sehingga barisnya lebih banyak daripada jumlah variabel.</p>` : ''}
      </div>
      <div>
        <div class="exc">
          <div class="h">Variabel harga dan grade</div>
          <div class="c">${harga.pricing.join(', ')}</div>
          <div class="r">${escapeHtml(harga.reason)}</div>
        </div>
        ${dibuang}
      </div>
    </div>`;

  el('p3-varhint').textContent =
    `${m.features.n_selected} dipilih dari ${m.features.n_candidates} kandidat`;

  // --- batas penggunaan
  const kolom = (kelas, judul, isi) =>
    `<div class="sc ${kelas}"><h3>${judul}</h3><ul>${
      isi.map((t) => `<li>${escapeHtml(t)}</li>`).join('')}</ul></div>`;

  el('p3-limits').innerHTML = `<div class="grid3">
    ${kolom('y', 'Boleh dipakai untuk', m.limitations.can_be_used_for)}
    ${kolom('n', 'Tidak boleh dipakai untuk', m.limitations.cannot_be_used_for)}
    ${kolom('l', 'Keterbatasan data', m.limitations.data_limitations)}
  </div>
  ${m.limitations.policy_review_needed ? `<div class="callout warn" style="margin-top:14px">
    <b>Kebijakan perlu ditinjau.</b> Batas PD yang dipilih menggunakan data validasi
    ternyata tidak lagi memenuhi batas risiko ketika diterapkan pada data pengujian.
    Penyebabnya bukan model yang rusak &mdash; urutan risikonya masih baik &mdash;
    melainkan kualitas pemohon yang menurun dari tahun ke tahun.
  </div>` : ''}`;
}

/* ================= 6. Penggerak ================= */

const JUDUL = {
  p1: 'Penilaian aplikasi',
  p2: 'Kebijakan kredit',
  p3: 'Model card',
};

function pindahHalaman(id) {
  document.querySelectorAll('.page').forEach((p) => p.classList.toggle('on', p.id === id));
  document.querySelectorAll('.nav button').forEach((b) =>
    b.classList.toggle('on', b.dataset.p === id));
  el('page-title').textContent = JUDUL[id];
}

async function mulai() {
  document.querySelectorAll('.nav button').forEach((b) => {
    b.onclick = () => pindahHalaman(b.dataset.p);
  });
  el('p1-go').onclick = nilaiPemohon;

  try {
    // Keterangan di bilah samping diambil dari model card
    const card = await api('/api/model/card');
    const id = card.identity;
    el('brand-sub').innerHTML =
      `${angka(id.n_train)} pinjaman untuk pelatihan<br>Tenor 36 bulan`;
    el('side-foot').innerHTML =
      `Model ${id.version} &middot; Logistic Regression<br>` +
      `Data latih ${id.train_years.join(',')} &middot; Data uji ${id.test_years.join(',')}`;
    el('page-meta').textContent = `model ${id.version}`;

    // Ketiga halaman dimuat sekaligus supaya perpindahan halaman seketika.
    // Masing-masing ditangani sendiri: kalau satu halaman gagal, dua
    // halaman lainnya tetap bisa dipakai, dan pesan errornya menyebut
    // halaman mana yang bermasalah.
    const hasil = await Promise.allSettled([muatForm(), muatKebijakan(), muatModelCard()]);
    const nama = ['Penilaian aplikasi', 'Kebijakan kredit', 'Model card'];
    const gagal = hasil
      .map((h, i) => (h.status === 'rejected' ? `${nama[i]}: ${h.reason.message}` : null))
      .filter(Boolean);
    if (gagal.length) {
      el('err-box').innerHTML =
        `<div class="err"><b>Sebagian halaman gagal dimuat.</b>
         ${escapeHtml(gagal.join(' | '))}<br>
         Coba tekan Ctrl+F5 untuk memuat ulang berkas halaman.</div>`;
    }
  } catch (e) {
    tampilkanError(e);
  }
}

mulai();