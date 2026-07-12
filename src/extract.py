"""
extract.py

Handles ingestion of raw CMS Hospital Value-Based Purchasing (HVBP) data.

In production, `download_cms_datasets()` would pull directly from the CMS
Provider Data Catalog API (data.cms.gov). That endpoint is not reachable from
this environment, so the function is implemented as a documented stub -
swap in the real request without touching any downstream module.

Real source (public, no auth required):
  https://data.cms.gov/provider-data/dataset/hospital-value-based-purchasing-hvbp-total-performance-score
"""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

CMS_HVBP_DATASET_URL = (
    "https://data.cms.gov/provider-data/api/1/datastore/query/"
    "ypbt-wvdk/0"  # HVBP Total Performance Score dataset identifier
)
CMS_HOSPITAL_INFO_DATASET_URL = (
    "https://data.cms.gov/provider-data/api/1/datastore/query/"
    "xubh-q36u/0"  # Hospital General Information dataset identifier
)


def download_cms_datasets(raw_dir: Path, logger: logging.Logger) -> None:
    """
    Placeholder for production CMS API extraction.

    Not invoked by default (see main.py) because this sandbox has no network
    access to data.cms.gov. To activate in a production environment:

        import requests
        response = requests.get(CMS_HVBP_DATASET_URL, timeout=30)
        response.raise_for_status()
        pd.DataFrame(response.json()).to_csv(raw_dir / "hvbp_total_performance.csv")
    """
    logger.warning(
        "download_cms_datasets() is a stub in this environment. "
        "Place source CSVs manually in %s or implement the live API call.",
        raw_dir,
    )


def load_raw_csv(path: Path, logger: logging.Logger) -> pd.DataFrame:
    """Load a single raw CSV file into a DataFrame with basic error handling."""
    if not path.exists():
        raise FileNotFoundError(
            f"Expected raw data file not found: {path}. "
            "Run scripts/generate_sample_data.py for a demo dataset, or "
            "place the real CMS export at this path."
        )

    logger.info("Loading raw file: %s", path)
    df = pd.read_csv(path)
    logger.info("Loaded %d rows, %d columns from %s", len(df), len(df.columns), path.name)
    return df


def extract(
    hvbp_path: Path,
    hospital_info_path: Path,
    logger: logging.Logger,
) -> tuple[pd.DataFrame, pd.DataFrame | None]:
    """Extract HVBP scores, plus a hospital reference table if one exists.

    Real CMS HVBP exports are self-contained (hospital name/address/state
    are already columns in the same file), so the separate reference file
    is optional. If it isn't found, hospital_df is returned as None and
    clean.merge_datasets() treats the HVBP data as authoritative.
    """
    hvbp_df = load_raw_csv(hvbp_path, logger)

    if not hospital_info_path.exists():
        logger.info(
            "No separate hospital reference file at %s; assuming the HVBP "
            "file is self-contained.",
            hospital_info_path,
        )
        return hvbp_df, None

    hospital_df = load_raw_csv(hospital_info_path, logger)
    return hvbp_df, hospital_df
