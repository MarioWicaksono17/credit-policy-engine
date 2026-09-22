-- =====================================================================
-- Lapisan BRONZE: data mentah, apa adanya.
--
-- Berisi SEMUA baris dari file CSV, tapi hanya 79 dari 151 kolom --
-- yaitu kolom yang terdaftar di config.yaml. Isinya tidak diubah sama
-- sekali: teks tetap teks ("Dec-2015", " 36 months"), angka tetap angka.
--
-- Semua baris disimpan, termasuk pinjaman 60 bulan dan yang masih
-- berjalan. Penyaringan baru terjadi saat membuat silver. Dengan begitu,
-- kalau nanti cakupan project berubah, data tidak perlu dimuat ulang
-- dari CSV 1,6 GB.
--
-- Angka memakai DOUBLE PRECISION, bukan NUMERIC. NUMERIC dibaca Python
-- sebagai objek Decimal yang tidak bisa diproses scikit-learn.
-- =====================================================================

DROP TABLE IF EXISTS bronze_loans_raw;

CREATE TABLE bronze_loans_raw (
    id                              TEXT,
    issue_d                         TEXT,
    loan_amnt                       DOUBLE PRECISION,
    emp_length                      TEXT,
    home_ownership                  TEXT,
    annual_inc                      DOUBLE PRECISION,
    verification_status             TEXT,
    purpose                         TEXT,
    dti                             DOUBLE PRECISION,
    fico_range_low                  DOUBLE PRECISION,
    fico_range_high                 DOUBLE PRECISION,
    earliest_cr_line                TEXT,
    delinq_2yrs                     DOUBLE PRECISION,
    inq_last_6mths                  DOUBLE PRECISION,
    mths_since_last_delinq          DOUBLE PRECISION,
    mths_since_last_record          DOUBLE PRECISION,
    open_acc                        DOUBLE PRECISION,
    pub_rec                         DOUBLE PRECISION,
    revol_bal                       DOUBLE PRECISION,
    revol_util                      DOUBLE PRECISION,
    total_acc                       DOUBLE PRECISION,
    mort_acc                        DOUBLE PRECISION,
    pub_rec_bankruptcies            DOUBLE PRECISION,
    collections_12_mths_ex_med      DOUBLE PRECISION,
    acc_now_delinq                  DOUBLE PRECISION,
    chargeoff_within_12_mths        DOUBLE PRECISION,
    delinq_amnt                     DOUBLE PRECISION,
    tax_liens                       DOUBLE PRECISION,
    mths_since_last_major_derog     DOUBLE PRECISION,
    tot_coll_amt                    DOUBLE PRECISION,
    tot_cur_bal                     DOUBLE PRECISION,
    total_rev_hi_lim                DOUBLE PRECISION,
    acc_open_past_24mths            DOUBLE PRECISION,
    avg_cur_bal                     DOUBLE PRECISION,
    bc_open_to_buy                  DOUBLE PRECISION,
    bc_util                         DOUBLE PRECISION,
    mo_sin_old_il_acct              DOUBLE PRECISION,
    mo_sin_old_rev_tl_op            DOUBLE PRECISION,
    mo_sin_rcnt_rev_tl_op           DOUBLE PRECISION,
    mo_sin_rcnt_tl                  DOUBLE PRECISION,
    mths_since_recent_bc            DOUBLE PRECISION,
    mths_since_recent_bc_dlq        DOUBLE PRECISION,
    mths_since_recent_inq           DOUBLE PRECISION,
    mths_since_recent_revol_delinq  DOUBLE PRECISION,
    num_accts_ever_120_pd           DOUBLE PRECISION,
    num_actv_bc_tl                  DOUBLE PRECISION,
    num_actv_rev_tl                 DOUBLE PRECISION,
    num_bc_sats                     DOUBLE PRECISION,
    num_bc_tl                       DOUBLE PRECISION,
    num_il_tl                       DOUBLE PRECISION,
    num_op_rev_tl                   DOUBLE PRECISION,
    num_rev_accts                   DOUBLE PRECISION,
    num_rev_tl_bal_gt_0             DOUBLE PRECISION,
    num_sats                        DOUBLE PRECISION,
    num_tl_120dpd_2m                DOUBLE PRECISION,
    num_tl_30dpd                    DOUBLE PRECISION,
    num_tl_90g_dpd_24m              DOUBLE PRECISION,
    num_tl_op_past_12m              DOUBLE PRECISION,
    pct_tl_nvr_dlq                  DOUBLE PRECISION,
    percent_bc_gt_75                DOUBLE PRECISION,
    tot_hi_cred_lim                 DOUBLE PRECISION,
    total_bal_ex_mort               DOUBLE PRECISION,
    total_bc_limit                  DOUBLE PRECISION,
    total_il_high_credit_limit      DOUBLE PRECISION,
    grade                           TEXT,
    sub_grade                       TEXT,
    int_rate                        DOUBLE PRECISION,
    installment                     DOUBLE PRECISION,
    loan_status                     TEXT,
    funded_amnt                     DOUBLE PRECISION,
    total_rec_prncp                 DOUBLE PRECISION,
    recoveries                      DOUBLE PRECISION,
    collection_recovery_fee         DOUBLE PRECISION,
    total_pymnt                     DOUBLE PRECISION,
    total_rec_int                   DOUBLE PRECISION,
    out_prncp                       DOUBLE PRECISION,
    last_pymnt_d                    TEXT,
    application_type                TEXT,
    term                            TEXT
);