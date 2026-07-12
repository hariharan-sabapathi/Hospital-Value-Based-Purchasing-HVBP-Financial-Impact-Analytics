# Hospital Value-Based Purchasing (HVBP) Financial Impact Analytics

A production-inspired, configuration-driven healthcare analytics pipeline that processes CMS Hospital Value-Based Purchasing (HVBP) datasets to identify reimbursement risk, rank hospital performance, and estimate the financial impact of quality improvement initiatives through an interactive Power BI dashboard.

------------------------------------------------------------------------

## Project Overview

Hospitals participating in the CMS Hospital Value-Based Purchasing (HVBP) Program receive incentive payments based on clinical quality and operational performance.

This project automates the ingestion, validation, transformation, and analysis of CMS HVBP datasets to identify hospitals at risk of reimbursement reductions and estimate the potential financial impact of performance gaps.

------------------------------------------------------------------------

## Key Features

-   Automated Python ETL pipeline
-   Configuration-driven architecture
-   Automated data quality validation
-   SQL analytics using CTEs and window functions
-   Hospital performance ranking and cohort analysis
-   Financial impact modeling for reimbursement adjustments
-   Interactive Power BI dashboard
-   Modular, production-ready codebase

------------------------------------------------------------------------

## Technology Stack

-   Python
-   SQL (SQLite, configurable for PostgreSQL/Snowflake)
-   Power BI
-   YAML Configuration
-   Git

------------------------------------------------------------------------

## Project Architecture

``` text
CMS HVBP Dataset
        │
        ▼
Python ETL Pipeline
        │
        ▼
Data Cleaning & Validation
        │
        ▼
Financial Impact Modeling
        │
        ▼
SQL Analytics
(CTEs • Window Functions • Rankings)
        │
        ▼
Power BI Dashboard
```

------------------------------------------------------------------------

## Repository Structure

``` text
financial-reimbursement/
│
├── config/
│   └── config.yaml
│
├── data/
│   ├── raw/
│   ├── processed/
│   └── analysis_exports/
│
├── dashboard/
│   ├── Financial_Impact.pbix
│   ├── powerbi_power_query.m
│   └── dax_measures.md
│
├── logs/
│   └── pipeline.log
│
├── scripts/
│   └── generate_sample_data.py
│
├── sql/
│   ├── schema.sql
│   └── analysis.sql
│
├── src/
│   ├── settings.py
│   ├── extract.py
│   ├── clean.py
│   ├── validate.py
│   ├── transform.py
│   ├── load.py
│   └── utils/
│       └── logger.py
│
├── .gitignore
├── main.py
├── README.md
└── requirements.txt
```

------------------------------------------------------------------------

## Data Source

The project uses publicly available CMS Hospital Value-Based Purchasing (HVBP) datasets from the CMS Provider Data Catalog.

-   Hospital Value-Based Purchasing Total Performance Score
-   Hospital General Information

For local development without downloading CMS data, generate a synthetic dataset:

``` bash
python scripts/generate_sample_data.py
```

The pipeline supports both synthetic and real CMS datasets without requiring code changes.

------------------------------------------------------------------------

## Setup

``` bash
# Clone the repository
git clone https://github.com/<your-username>/financial-reimbursement.git

# Navigate to the project directory
cd financial-reimbursement

# Install project dependencies
pip install -r requirements.txt

# (Optional) Generate sample data
python scripts/generate_sample_data.py

# Run the pipeline
python main.py
```

------------------------------------------------------------------------

## Pipeline Workflow

### 1. Extract

-   Load CMS HVBP datasets
-   Read configuration from `config.yaml`
-   Initialize logging

### 2. Clean

-   Standardize column names
-   Convert data types
-   Remove duplicates
-   Merge hospital information

### 3. Validate

Automatically checks for: - Missing Provider IDs - Duplicate hospitals - Missing performance scores - Invalid score ranges - Required column validation

Validation reports are exported for auditing.

### 4. Transform

-   Classify reimbursement risk
-   Calculate projected reimbursement adjustments
-   Generate financial impact metrics

### 5. Load

-   Load processed data into SQLite using SQLAlchemy
-   Easily configurable for PostgreSQL or Snowflake

### 6. Analyze

Execute SQL analytics using: - Common Table Expressions (CTEs) - Window Functions - Hospital Rankings - Quartile Analysis - National Performance Comparisons. Results are exported for Power BI.

------------------------------------------------------------------------

## SQL Analytics

  Analysis                   SQL Technique
  -------------------------- ------------------
  State Rankings             `RANK()`
  Performance Quartiles      `NTILE()`
  National Percentiles       `PERCENT_RANK()`
  Below National Average     CTE
  Financial Impact Ranking   Window Functions

------------------------------------------------------------------------

## Power BI Dashboard

The dashboard consists of three pages:

### Executive Summary

-   Total Hospitals
-   Average Performance Score
-   Reimbursement Risk Distribution
-   Estimated Financial Impact

### Performance Analysis

-   State Rankings
-   Hospital Rankings
-   Performance Quartiles
-   National Benchmark Comparisons

### Financial Impact

-   Revenue Adjustment Matrix
-   High-Risk Hospitals
-   Estimated Incentive Changes
-   Performance Gap Analysis

------------------------------------------------------------------------

## Engineering Highlights

-   Configuration-driven architecture
-   Modular ETL design
-   Production-style logging
-   Type hints throughout the codebase
-   Relative path management
-   PEP 8 compliant
-   Reusable SQL analytics
-   Production-ready project structure
