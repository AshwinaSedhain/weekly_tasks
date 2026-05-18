-- Healthstream Data Warehouse Schema

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Dimension tables

CREATE TABLE IF NOT EXISTS patients (
    patient_id      VARCHAR(36) PRIMARY KEY,
    first_name      VARCHAR(100) NOT NULL,
    last_name       VARCHAR(100) NOT NULL,
    date_of_birth   DATE NOT NULL,
    gender          VARCHAR(10),
    state           VARCHAR(50),
    insurance_type  VARCHAR(50),
    risk_score      NUMERIC(5,2) DEFAULT 0.0,
    created_at      TIMESTAMP DEFAULT NOW(),
    updated_at      TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS hospitals (
    hospital_id         VARCHAR(36) PRIMARY KEY,
    hospital_name       VARCHAR(200) NOT NULL,
    state               VARCHAR(50),
    hospital_type       VARCHAR(50),
    bed_count           INTEGER,
    accreditation       VARCHAR(50),
    performance_score   NUMERIC(5,2) DEFAULT 0.0,
    created_at          TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS treatments (
    treatment_code  VARCHAR(20) PRIMARY KEY,
    treatment_name  VARCHAR(200) NOT NULL,
    category        VARCHAR(100),
    avg_cost        NUMERIC(12,2),
    description     TEXT
);

-- Fact tables

CREATE TABLE IF NOT EXISTS claims (
    claim_id            VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4()::text,
    patient_id          VARCHAR(36) REFERENCES patients(patient_id),
    hospital_id         VARCHAR(36) REFERENCES hospitals(hospital_id),
    treatment_code      VARCHAR(20) REFERENCES treatments(treatment_code),
    diagnosis_code      VARCHAR(20) NOT NULL,
    claim_amount        NUMERIC(12,2) NOT NULL,
    approved_amount     NUMERIC(12,2),
    insurance_status    VARCHAR(30),
    claim_date          TIMESTAMP NOT NULL,
    processed_date      TIMESTAMP,
    is_fraud            BOOLEAN DEFAULT FALSE,
    fraud_score         NUMERIC(5,4) DEFAULT 0.0,
    status              VARCHAR(20) DEFAULT 'PENDING',
    created_at          TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS fraud_alerts (
    alert_id        SERIAL PRIMARY KEY,
    claim_id        VARCHAR(36) REFERENCES claims(claim_id),
    patient_id      VARCHAR(36) REFERENCES patients(patient_id),
    hospital_id     VARCHAR(36) REFERENCES hospitals(hospital_id),
    fraud_score     NUMERIC(5,4) NOT NULL,
    alert_reason    TEXT,
    alert_type      VARCHAR(50),
    severity        VARCHAR(20),
    resolved        BOOLEAN DEFAULT FALSE,
    created_at      TIMESTAMP DEFAULT NOW(),
    resolved_at     TIMESTAMP
);

CREATE TABLE IF NOT EXISTS analytics_summary (
    summary_id          SERIAL PRIMARY KEY,
    summary_date        DATE NOT NULL,
    total_claims        INTEGER DEFAULT 0,
    total_amount        NUMERIC(15,2) DEFAULT 0.0,
    approved_claims     INTEGER DEFAULT 0,
    denied_claims       INTEGER DEFAULT 0,
    fraud_detected      INTEGER DEFAULT 0,
    avg_claim_amount    NUMERIC(12,2) DEFAULT 0.0,
    top_diagnosis       VARCHAR(20),
    top_hospital        VARCHAR(36),
    created_at          TIMESTAMP DEFAULT NOW(),
    UNIQUE(summary_date)
);

-- Indexes

CREATE INDEX IF NOT EXISTS idx_claims_patient    ON claims(patient_id);
CREATE INDEX IF NOT EXISTS idx_claims_hospital   ON claims(hospital_id);
CREATE INDEX IF NOT EXISTS idx_claims_date       ON claims(claim_date);
CREATE INDEX IF NOT EXISTS idx_claims_fraud      ON claims(is_fraud);
CREATE INDEX IF NOT EXISTS idx_claims_status     ON claims(status);
CREATE INDEX IF NOT EXISTS idx_fraud_claim       ON fraud_alerts(claim_id);
CREATE INDEX IF NOT EXISTS idx_fraud_severity    ON fraud_alerts(severity);
CREATE INDEX IF NOT EXISTS idx_fraud_resolved    ON fraud_alerts(resolved);
CREATE INDEX IF NOT EXISTS idx_analytics_date    ON analytics_summary(summary_date);

-- Seed reference treatment data

INSERT INTO treatments (treatment_code, treatment_name, category, avg_cost) VALUES
    ('T001', 'Cardiac Catheterization',     'Cardiology',       15000.00),
    ('T002', 'MRI Brain Scan',              'Radiology',         2500.00),
    ('T003', 'Hip Replacement Surgery',     'Orthopedics',      25000.00),
    ('T004', 'Chemotherapy Session',        'Oncology',          8000.00),
    ('T005', 'Emergency Room Visit',        'Emergency',         3500.00),
    ('T006', 'Appendectomy',                'Surgery',          12000.00),
    ('T007', 'Colonoscopy',                 'Gastroenterology',  1800.00),
    ('T008', 'Physical Therapy Session',    'Rehabilitation',     350.00),
    ('T009', 'Diabetes Management',         'Endocrinology',      500.00),
    ('T010', 'Knee Arthroscopy',            'Orthopedics',       9000.00),
    ('T011', 'CT Scan Chest',               'Radiology',         1200.00),
    ('T012', 'Cataract Surgery',            'Ophthalmology',     3800.00),
    ('T013', 'Psychiatric Evaluation',      'Psychiatry',         800.00),
    ('T014', 'Prenatal Care Visit',         'Obstetrics',         400.00),
    ('T015', 'Coronary Bypass Surgery',     'Cardiology',       75000.00)
ON CONFLICT (treatment_code) DO NOTHING;
