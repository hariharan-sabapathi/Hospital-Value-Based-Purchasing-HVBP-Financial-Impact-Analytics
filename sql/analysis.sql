-- analysis.sql
-- Each query is labeled with `-- name: <label>` so load.py can execute them
-- individually and hand results back by name (used for the dashboard exports).

-- name: top_20_hospitals
SELECT
    hospital_name,
    state,
    total_performance_score
FROM hospital_scores
ORDER BY total_performance_score DESC
LIMIT 20;

-- name: bottom_20_hospitals
SELECT
    hospital_name,
    state,
    total_performance_score
FROM hospital_scores
ORDER BY total_performance_score ASC
LIMIT 20;

-- name: state_rank
SELECT
    hospital_name,
    state,
    total_performance_score,
    RANK() OVER (
        PARTITION BY state
        ORDER BY total_performance_score DESC
    ) AS state_rank
FROM hospital_scores;

-- name: performance_quartiles
SELECT
    hospital_name,
    state,
    total_performance_score,
    NTILE(4) OVER (
        ORDER BY total_performance_score DESC
    ) AS performance_quartile
FROM hospital_scores;

-- name: state_averages
SELECT
    state,
    ROUND(AVG(total_performance_score), 2) AS avg_score,
    COUNT(*) AS hospital_count
FROM hospital_scores
GROUP BY state
ORDER BY avg_score DESC;

-- name: below_national_average
WITH national_avg AS (
    SELECT AVG(total_performance_score) AS avg_score
    FROM hospital_scores
)
SELECT
    hs.hospital_name,
    hs.state,
    hs.total_performance_score,
    na.avg_score AS national_average
FROM hospital_scores hs
CROSS JOIN national_avg na
WHERE hs.total_performance_score < na.avg_score
ORDER BY hs.total_performance_score ASC;

-- name: reimbursement_risk_summary
SELECT
    reimbursement_risk,
    COUNT(*) AS hospital_count,
    ROUND(AVG(total_performance_score), 2) AS avg_score,
    ROUND(SUM(projected_adjustment), 2) AS total_projected_adjustment
FROM hospital_scores
GROUP BY reimbursement_risk
ORDER BY total_projected_adjustment ASC;

-- name: financial_impact_matrix
SELECT
    hospital_name,
    state,
    total_performance_score,
    reimbursement_risk,
    adjustment_rate,
    estimated_base_revenue,
    projected_adjustment,
    RANK() OVER (
        ORDER BY projected_adjustment ASC
    ) AS risk_rank
FROM hospital_scores
ORDER BY projected_adjustment ASC;

-- name: rolling_state_percentile
-- Percentile rank of each hospital's score within its state (CTE + window fn)
WITH scored AS (
    SELECT
        hospital_name,
        state,
        total_performance_score,
        PERCENT_RANK() OVER (
            PARTITION BY state
            ORDER BY total_performance_score
        ) AS state_percentile
    FROM hospital_scores
)
SELECT *
FROM scored
ORDER BY state, state_percentile DESC;
