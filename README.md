# Financial Reimbursement & Value-Based Purchasing Analytics

A config-driven data pipeline that identifies hospitals at risk of losing
CMS Hospital Value-Based Purchasing (HVBP) incentive payments, ranks
performance cohorts with SQL window functions, and maps quality gaps to a
projected dollar impact on a Power BI dashboard.

## Objective

Maximize federal incentive payouts by identifying clinical performance
metrics that fall below CMS reimbursement thresholds, using the CMS
Hospital VBP Total Performance Score datasets.

## Architecture

```
financial-reimbursement/
├── config/
│   └── config.yaml            # all paths, DB settings, thresholds — no hardcoding
├── data/
│   ├── raw/                   # source CSVs (CMS export or synthetic demo data)
│   └── processed/             # cleaned data, validation report, analysis exports
├── logs/                      # rotating pipeline logs
├── sql/
│   ├── schema.sql             # DDL for the target table
│   └── analysis.sql           # named window-function / CTE queries
├── src/
│   ├── settings.py            # typed config loader
│   ├── extract.py             # raw data ingestion
│   ├── clean.py                # standardization + merge
│   ├── validate.py             # automated data-quality checks
│   ├── transform.py            # risk classification + financial impact model
│   ├── load.py                  # SQL load + analysis query execution
│   └── utils/logger.py         # shared rotating-file logger
├── dashboard/
│   ├── powerbi_power_query.m           # Power Query (M) source for Power BI
│   └── dax_measures_and_layout.md      # DAX measures + page-by-page layout spec
├── scripts/
│   └── generate_sample_data.py  # DEV ONLY — synthetic HVBP-shaped dataset
├── main.py                      # pipeline orchestrator
└── requirements.txt
```

## Data source

Production data comes from CMS's public Provider Data Catalog:
- Hospital VBP Total Performance Score:
  `https://data.cms.gov/provider-data/dataset/hospital-value-based-purchasing-hvbp-total-performance-score`
- Hospital General Information:
  `https://data.cms.gov/provider-data/dataset/xubh-q36u`

Download both CSVs and place them at the paths configured in
`config/config.yaml` (`paths.hvbp_raw_file`, `paths.hospital_info_raw_file`
under `paths.raw_dir`). No code changes are required.

For local development without network access to CMS, run
`scripts/generate_sample_data.py` first — it writes a synthetic dataset with
the identical schema (and a few intentionally messy rows) so the full
pipeline, including the validation layer, is exercisable end to end.

**This repo has already been validated against a real CMS export**
(`hvbp_tps-P2.csv`, FY2026, 2,455 hospitals). Real CMS files are
self-contained — hospital name, address, city, and state are columns in the
same file as the scores, so no separate hospital-reference file is needed.
`src/extract.py` detects this automatically: if
`data/raw/hospital_general_info.csv` isn't present, it treats the HVBP file
as authoritative and `src/clean.py` skips the merge step. CMS also reports
missing domain scores as the literal string `"Not Available"` rather than a
blank cell; `clean._coerce_numeric()` maps that token to null before
converting to numeric, so the validation layer's null checks catch it
correctly.

**Threshold recalibration:** the demo dataset's scores cluster around 65,
but real CMS Total Performance Scores cluster much lower (FY2026 file: mean
≈ 31, 90th percentile ≈ 46.5). A fixed 60/80/90 cutoff — reasonable on a
0–100 grading-curve assumption — would misclassify nearly every real
hospital as "High Risk." `config/config.yaml -> financial_model.adjustment_tiers`
is set to the FY2026 file's 25th/75th/90th percentiles instead, so risk
tiers are relative to peer performance. When loading a new fiscal year's
file, recompute quantiles and update the tiers:

```python
import pandas as pd
df = pd.read_csv("data/processed/hospital_scores_processed.csv")
print(df["total_performance_score"].quantile([0.25, 0.75, 0.90]))
```

## Setup

```bash
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Demo data (skip this step once you have real CMS exports in data/raw/)
python scripts/generate_sample_data.py

python main.py
```

Optional flag: `python main.py --halt-on-validation-failure` aborts the run
if any data-quality check fails instead of logging a warning and continuing.

## What the pipeline does

1. **Extract** (`src/extract.py`) — loads the raw HVBP and hospital
   reference CSVs. `download_cms_datasets()` is a documented stub for the
   live CMS API call in environments with network access.
2. **Clean** (`src/clean.py`) — standardizes column names, coerces score
   columns to numeric, de-duplicates on `provider_id`, and left-merges the
   two source tables.
3. **Validate** (`src/validate.py`) — an automated data-quality layer
   that checks for missing required columns, null/duplicate provider IDs,
   null scores, and out-of-range scores. Every run writes
   `data/processed/validation_report.csv` for auditability; nothing is
   silently dropped.
4. **Transform** (`src/transform.py`) — classifies each hospital into a
   reimbursement-risk tier and computes a projected dollar adjustment
   using the tiers and assumed base revenue defined in `config.yaml`.
5. **Load** (`src/load.py`) — applies `sql/schema.sql` and loads the
   enriched dataset into a SQLite database at
   `data/processed/hospital_scores.db` via SQLAlchemy. Swapping to
   Postgres/Snowflake only requires changing `database.connection_string`
   in `config.yaml`.
6. **Analyze** — executes every named query in `sql/analysis.sql`
   (`RANK()`, `NTILE()`, `PERCENT_RANK()`, and CTEs) and exports each
   result to `data/processed/analysis_exports/` for the dashboard.

## SQL analyses (`sql/analysis.sql`)

| Query | Technique |
|---|---|
| `state_rank` | `RANK() OVER (PARTITION BY state ORDER BY ...)` |
| `performance_quartiles` | `NTILE(4) OVER (...)` |
| `rolling_state_percentile` | CTE + `PERCENT_RANK()` |
| `below_national_average` | CTE + `CROSS JOIN` |
| `financial_impact_matrix` | `RANK()` over projected dollar impact |

## Power BI dashboard

See `dashboard/dax_measures_and_layout.md` for the full DAX measure set and
a three-page layout spec (Executive Summary, Performance Analysis, Financial
Impact). Connect Power BI to `data/processed/hospital_scores_processed.csv`
or the individual `analysis_exports/*.csv` files using
`dashboard/powerbi_power_query.m` as a starting Power Query script.

## Assumptions used in the financial impact model

CMS's actual VBP payment-adjustment formula is proprietary to each
hospital's base DRG payments and is not published in a simple closed form.
This project uses a transparent, documented substitute so the *analytical
approach* — not the exact CMS dollar figures — is what's being demonstrated:

| Total Performance Score | Adjustment Rate | Assumed Base Revenue |
|---|---|---|
| ≥ 90 | +2.0% | $10,000,000 |
| 80–89 | +1.0% | $10,000,000 |
| 60–79 | 0.0% | $10,000,000 |
| < 60 | −1.0% | $10,000,000 |

Both the tiers and the base revenue figure are configurable in
`config/config.yaml -> financial_model` and are disclosed directly on the
dashboard.

## Engineering notes

- All paths are resolved relative to the project root in `src/settings.py`
  — nothing is hardcoded.
- Every module is type-hinted and independently testable.
- Logging is centralized through `src/utils/logger.py` with rotating file
  handlers, configurable via `config.yaml`.
- `sql/analysis.sql` queries are named (`-- name: <label>`) so `src/load.py`
  can run and export each independently without string-matching hacks.
