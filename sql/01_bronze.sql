-- Lapisan bronze: data mentah, apa adanya, tanpa transformasi.
-- Tujuannya agar kita selalu bisa kembali ke titik nol tanpa
-- mengunduh ulang dataset 100 MB.

DROP TABLE IF EXISTS bronze_loans_raw;

CREATE TABLE bronze_loans_raw (
    loan_amnt              NUMERIC,
    term                   TEXT,
    int_rate               NUMERIC,
    installment            NUMERIC,
    grade                  TEXT,
    sub_grade              TEXT,
    emp_title              TEXT,
    emp_length             TEXT,
    home_ownership         TEXT,
    annual_inc             NUMERIC,
    verification_status    TEXT,
    issue_d                TEXT,
    loan_status            TEXT,
    purpose                TEXT,
    title                  TEXT,
    dti                    NUMERIC,
    earliest_cr_line       TEXT,
    open_acc               NUMERIC,
    pub_rec                NUMERIC,
    revol_bal              NUMERIC,
    revol_util             NUMERIC,
    total_acc              NUMERIC,
    initial_list_status    TEXT,
    application_type       TEXT,
    mort_acc               NUMERIC,
    pub_rec_bankruptcies   NUMERIC,
    address                TEXT
);