"""
clean.py

Cleans, standardizes, and merges the raw HVBP and hospital reference tables
into a single analysis-ready DataFrame.
"""

from __future__ import annotations

import logging

import pandas as pd

# Canonical column names used downstream (SQL load, validation, dashboard).
# Includes both the simplified demo schema and the real CMS HVBP export
# headers (e.g. hvbp_tps-*.csv from data.cms.gov), which report each domain
# as an "Unweighted" and a "Weighted" score. The weighted score is what
# actually rolls up into Total Performance Score, so it maps to our
# canonical *_score fields; the unweighted variant is kept for reference.
CANONICAL_COLUMNS = {
    "provider id": "provider_id",
    "facility id": "provider_id",
    "hospital name": "hospital_name",
    "facility name": "hospital_name",
    "state": "state",
    "city": "city",
    "city/town": "city",
    "address": "address",
    "zip code": "zip_code",
    "county/parish": "county",
    "fiscal year": "fiscal_year",
    "clinical outcomes score": "clinical_score",
    "clinical score": "clinical_score",
    "weighted normalized clinical outcomes domain score": "clinical_score",
    "unweighted normalized clinical outcomes domain score": "clinical_score_unweighted",
    "safety score": "safety_score",
    "weighted safety domain score": "safety_score",
    "unweighted normalized safety domain score": "safety_score_unweighted",
    "efficiency score": "efficiency_score",
    "weighted efficiency and cost reduction domain score": "efficiency_score",
    "unweighted normalized efficiency and cost reduction domain score": (
        "efficiency_score_unweighted"
    ),
    "patient experience score": "patient_experience_score",
    "hcahps score": "patient_experience_score",
    "weighted person and community engagement domain score": "patient_experience_score",
    "unweighted person and community engagement domain score": (
        "patient_experience_score_unweighted"
    ),
    "total performance score": "total_performance_score",
}

# CMS represents missing domain scores with the literal string below rather
# than an empty cell. Treated as NaN during numeric coercion.
CMS_MISSING_VALUE_TOKEN = "Not Available"


def _standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Lowercase, strip, and map raw column names to canonical snake_case names."""
    df = df.copy()
    df.columns = [c.strip().lower() for c in df.columns]
    df = df.rename(columns={k: v for k, v in CANONICAL_COLUMNS.items() if k in df.columns})
    return df


def _coerce_numeric(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    """Force listed columns to numeric, turning unparseable values (including
    CMS's literal 'Not Available' token) into NaN rather than raising."""
    df = df.copy()
    for col in columns:
        if col in df.columns:
            df[col] = df[col].replace(CMS_MISSING_VALUE_TOKEN, pd.NA)
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def clean_hvbp(df: pd.DataFrame, logger: logging.Logger) -> pd.DataFrame:
    """Standardize and de-duplicate the HVBP performance-score table."""
    df = _standardize_columns(df)

    before = len(df)
    df = df.drop_duplicates(subset=["provider_id"])
    logger.info("Dropped %d duplicate provider rows from HVBP data", before - len(df))

    score_cols = [
        "clinical_score",
        "clinical_score_unweighted",
        "safety_score",
        "safety_score_unweighted",
        "efficiency_score",
        "efficiency_score_unweighted",
        "patient_experience_score",
        "patient_experience_score_unweighted",
        "total_performance_score",
    ]
    df = _coerce_numeric(df, score_cols)

    if "provider_id" in df.columns:
        df["provider_id"] = df["provider_id"].astype(str).str.strip()

    for col in ("state", "city", "hospital_name"):
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()

    return df


def is_self_contained(df: pd.DataFrame) -> bool:
    """Return True if the HVBP file already carries hospital reference fields
    (name/state), as the real CMS export does — meaning no separate hospital
    reference table needs to be merged in."""
    return "hospital_name" in df.columns and "state" in df.columns


def clean_hospital_info(df: pd.DataFrame, logger: logging.Logger) -> pd.DataFrame:
    """Standardize the hospital reference/general-information table."""
    df = _standardize_columns(df)

    if "provider_id" in df.columns:
        df["provider_id"] = df["provider_id"].astype(str).str.strip()

    for col in ("state", "city", "hospital_name"):
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()

    logger.info("Cleaned hospital reference data: %d rows", len(df))
    return df


def merge_datasets(
    hvbp_df: pd.DataFrame,
    hospital_df: pd.DataFrame | None,
    logger: logging.Logger,
) -> pd.DataFrame:
    """Left-merge HVBP scores onto hospital reference data by provider_id.

    If the HVBP file is already self-contained (real CMS exports include
    hospital name/state directly), no separate reference table exists and
    this is a no-op passthrough.
    """
    if hospital_df is None or is_self_contained(hvbp_df):
        logger.info(
            "HVBP file is self-contained (hospital fields already present); "
            "skipping reference-table merge."
        )
        return hvbp_df

    merged = hvbp_df.merge(
        hospital_df,
        on="provider_id",
        how="left",
        suffixes=("", "_ref"),
    )
    logger.info("Merged dataset shape: %d rows, %d columns", *merged.shape)
    return merged
