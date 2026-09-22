-- =====================================================================
-- Lapisan SILVER: data bersih yang dipakai project.
--
-- Hanya berisi pinjaman dalam cakupan -- sudah selesai, perorangan,
-- tenor 36 bulan, tahun 2013 sampai 2015.
--
-- Satu tabel berisi fitur DAN hasil. Ini aman karena model memilih
-- kolomnya dari daftar di config.yaml, bukan mengambil "semua kolom
-- kecuali ...". Kolom yang tidak tercantum di daftar fitur tidak akan
-- pernah dilihat model.
-- =====================================================================

DROP TABLE IF EXISTS silver_loans_clean;

CREATE TABLE silver_loans_clean (
    -- pengenal dan waktu
    loan_id                                 TEXT PRIMARY KEY,
    issue_year                              INTEGER,

    -- FITUR: yang dilihat model
    loan_amnt                               DOUBLE PRECISION,
    emp_length                              DOUBLE PRECISION,
    home_ownership                          TEXT,
    annual_inc                              DOUBLE PRECISION,
    verification_status                     TEXT,
    purpose                                 TEXT,
    dti                                     DOUBLE PRECISION,
    fico_score                              DOUBLE PRECISION,
    credit_history_years                    DOUBLE PRECISION,
    delinq_2yrs                             DOUBLE PRECISION,
    inq_last_6mths                          DOUBLE PRECISION,
    mths_since_last_delinq                  DOUBLE PRECISION,
    mths_since_last_record                  DOUBLE PRECISION,
    open_acc                                DOUBLE PRECISION,
    pub_rec                                 DOUBLE PRECISION,
    revol_bal                               DOUBLE PRECISION,
    revol_util                              DOUBLE PRECISION,
    total_acc                               DOUBLE PRECISION,
    mort_acc                                DOUBLE PRECISION,
    pub_rec_bankruptcies                    DOUBLE PRECISION,
    collections_12_mths_ex_med              DOUBLE PRECISION,
    acc_now_delinq                          DOUBLE PRECISION,
    chargeoff_within_12_mths                DOUBLE PRECISION,
    delinq_amnt                             DOUBLE PRECISION,
    tax_liens                               DOUBLE PRECISION,
    mths_since_last_major_derog             DOUBLE PRECISION,
    tot_coll_amt                            DOUBLE PRECISION,
    tot_cur_bal                             DOUBLE PRECISION,
    total_rev_hi_lim                        DOUBLE PRECISION,
    acc_open_past_24mths                    DOUBLE PRECISION,
    avg_cur_bal                             DOUBLE PRECISION,
    bc_open_to_buy                          DOUBLE PRECISION,
    bc_util                                 DOUBLE PRECISION,
    mo_sin_old_il_acct                      DOUBLE PRECISION,
    mo_sin_old_rev_tl_op                    DOUBLE PRECISION,
    mo_sin_rcnt_rev_tl_op                   DOUBLE PRECISION,
    mo_sin_rcnt_tl                          DOUBLE PRECISION,
    mths_since_recent_bc                    DOUBLE PRECISION,
    mths_since_recent_bc_dlq                DOUBLE PRECISION,
    mths_since_recent_inq                   DOUBLE PRECISION,
    mths_since_recent_revol_delinq          DOUBLE PRECISION,
    num_accts_ever_120_pd                   DOUBLE PRECISION,
    num_actv_bc_tl                          DOUBLE PRECISION,
    num_actv_rev_tl                         DOUBLE PRECISION,
    num_bc_sats                             DOUBLE PRECISION,
    num_bc_tl                               DOUBLE PRECISION,
    num_il_tl                               DOUBLE PRECISION,
    num_op_rev_tl                           DOUBLE PRECISION,
    num_rev_accts                           DOUBLE PRECISION,
    num_rev_tl_bal_gt_0                     DOUBLE PRECISION,
    num_sats                                DOUBLE PRECISION,
    num_tl_120dpd_2m                        DOUBLE PRECISION,
    num_tl_30dpd                            DOUBLE PRECISION,
    num_tl_90g_dpd_24m                      DOUBLE PRECISION,
    num_tl_op_past_12m                      DOUBLE PRECISION,
    pct_tl_nvr_dlq                          DOUBLE PRECISION,
    percent_bc_gt_75                        DOUBLE PRECISION,
    tot_hi_cred_lim                         DOUBLE PRECISION,
    total_bal_ex_mort                       DOUBLE PRECISION,
    total_bc_limit                          DOUBLE PRECISION,
    total_il_high_credit_limit              DOUBLE PRECISION,
    emp_length_missing                      BOOLEAN,
    mths_since_last_delinq_missing          BOOLEAN,
    mths_since_last_record_missing          BOOLEAN,
    mths_since_last_major_derog_missing     BOOLEAN,
    mths_since_recent_bc_dlq_missing        BOOLEAN,
    mths_since_recent_revol_delinq_missing  BOOLEAN,

    -- PEMBANDING: penilaian Lending Club, tidak dilihat model utama
    grade                                   TEXT,
    sub_grade                               TEXT,
    int_rate                                DOUBLE PRECISION,
    installment                             DOUBLE PRECISION,

    -- HASIL: target, EAD, LGD, untung -- DILARANG menjadi fitur
    default_flag                            INTEGER,
    funded_amnt                             DOUBLE PRECISION,
    total_rec_prncp                         DOUBLE PRECISION,
    recoveries                              DOUBLE PRECISION,
    collection_recovery_fee                 DOUBLE PRECISION,
    total_pymnt                             DOUBLE PRECISION,
    total_rec_int                           DOUBLE PRECISION,
    ead                                     DOUBLE PRECISION,
    lgd                                     DOUBLE PRECISION,
    net_cash                                DOUBLE PRECISION
);

CREATE INDEX idx_silver_issue_year ON silver_loans_clean (issue_year);