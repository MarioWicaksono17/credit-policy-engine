-- Lapisan silver: data bersih, tipe sudah benar, kolom target sudah ada.
-- Satu baris = satu aplikasi pinjaman.
--
-- Catatan: int_rate dan installment TETAP disimpan di sini meski
-- nantinya tidak dipakai model utama. Silver adalah data bersih,
-- bukan data terseleksi. Pemilihan variabel terjadi saat pelatihan,
-- bukan saat pembersihan.

DROP TABLE IF EXISTS silver_loans_clean;

CREATE TABLE silver_loans_clean (
    loan_id                SERIAL PRIMARY KEY,

    -- karakteristik pinjaman
    loan_amnt              NUMERIC,
    term_months            INTEGER,
    int_rate               NUMERIC,
    installment            NUMERIC,
    purpose                TEXT,

    -- karakteristik pemohon
    annual_inc             NUMERIC,
    emp_length_years       NUMERIC,
    home_ownership         TEXT,
    verification_status    TEXT,

    -- indikator kredit
    dti                    NUMERIC,
    credit_history_years   NUMERIC,
    open_acc               NUMERIC,
    total_acc              NUMERIC,
    revol_bal              NUMERIC,
    revol_util             NUMERIC,
    pub_rec                NUMERIC,
    pub_rec_bankruptcies   NUMERIC,
    mort_acc               NUMERIC,
    mort_acc_missing       BOOLEAN,
    initial_list_status    TEXT,

    -- kolom waktu: dipakai untuk membagi data, BUKAN sebagai fitur
    issue_year             INTEGER,

    -- target
    default_flag           INTEGER
);

CREATE INDEX idx_silver_issue_year ON silver_loans_clean (issue_year);