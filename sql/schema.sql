-- schema.sql
-- Target table for the processed HVBP + hospital reference dataset.
-- Compatible with SQLite (demo) and standard ANSI SQL engines
-- (Postgres/Snowflake) with minor type-name adjustments if needed.

DROP TABLE IF EXISTS hospital_scores;

CREATE TABLE hospital_scores (
    provider_id                 VARCHAR(20),
    hospital_name               TEXT,
    state                       VARCHAR(5),
    city                        TEXT,

    clinical_score              FLOAT,
    safety_score                FLOAT,
    efficiency_score            FLOAT,
    patient_experience_score    FLOAT,
    total_performance_score     FLOAT,

    reimbursement_risk          VARCHAR(20),
    adjustment_rate             FLOAT,
    estimated_base_revenue      FLOAT,
    projected_adjustment        FLOAT
);
