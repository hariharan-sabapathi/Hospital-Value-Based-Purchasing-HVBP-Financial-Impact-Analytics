"""
settings.py

Centralized, type-hinted configuration loader. Every module resolves paths
and parameters through this module rather than hardcoding values, so the
pipeline can be retargeted (new data source, new DB, new thresholds) by
editing config/config.yaml only.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

# Project root is derived relative to this file's location, never hardcoded.
PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent
CONFIG_PATH: Path = PROJECT_ROOT / "config" / "config.yaml"


@dataclass(frozen=True)
class AdjustmentTier:
    min_score: float
    adjustment_rate: float
    label: str


@dataclass(frozen=True)
class Settings:
    raw_dir: Path
    processed_dir: Path
    logs_dir: Path
    sql_dir: Path

    hvbp_raw_path: Path
    hospital_info_raw_path: Path
    processed_path: Path
    validation_report_path: Path

    db_dialect: str
    db_connection_string: str
    db_target_table: str

    log_level: str
    log_file: Path
    log_max_bytes: int
    log_backup_count: int

    min_valid_score: float
    max_valid_score: float
    required_columns: list[str]

    assumed_base_medicare_revenue: float
    adjustment_tiers: list[AdjustmentTier] = field(default_factory=list)


def _resolve(base: Path, relative: str) -> Path:
    """Resolve a config-relative path against the project root."""
    return (base / relative).resolve()


def load_settings(config_path: Path = CONFIG_PATH) -> Settings:
    """Load and validate configuration from YAML into a typed Settings object."""
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found at {config_path}")

    with config_path.open("r", encoding="utf-8") as handle:
        raw: dict[str, Any] = yaml.safe_load(handle)

    paths = raw["paths"]
    database = raw["database"]
    logging_cfg = raw["logging"]
    validation = raw["validation"]
    financial = raw["financial_model"]

    raw_dir = _resolve(PROJECT_ROOT, paths["raw_dir"])
    processed_dir = _resolve(PROJECT_ROOT, paths["processed_dir"])
    logs_dir = _resolve(PROJECT_ROOT, paths["logs_dir"])
    sql_dir = _resolve(PROJECT_ROOT, paths["sql_dir"])

    tiers = [
        AdjustmentTier(
            min_score=float(t["min_score"]),
            adjustment_rate=float(t["adjustment_rate"]),
            label=str(t["label"]),
        )
        for t in financial["adjustment_tiers"]
    ]
    # Ensure tiers are evaluated highest-threshold-first.
    tiers.sort(key=lambda t: t.min_score, reverse=True)

    return Settings(
        raw_dir=raw_dir,
        processed_dir=processed_dir,
        logs_dir=logs_dir,
        sql_dir=sql_dir,
        hvbp_raw_path=raw_dir / paths["hvbp_raw_file"],
        hospital_info_raw_path=raw_dir / paths["hospital_info_raw_file"],
        processed_path=processed_dir / paths["processed_file"],
        validation_report_path=processed_dir / paths["validation_report_file"],
        db_dialect=database["dialect"],
        db_connection_string=database["connection_string"],
        db_target_table=database["target_table"],
        log_level=logging_cfg["level"],
        log_file=logs_dir / logging_cfg["log_file"],
        log_max_bytes=int(logging_cfg["max_bytes"]),
        log_backup_count=int(logging_cfg["backup_count"]),
        min_valid_score=float(validation["min_valid_score"]),
        max_valid_score=float(validation["max_valid_score"]),
        required_columns=list(validation["required_columns"]),
        assumed_base_medicare_revenue=float(financial["assumed_base_medicare_revenue"]),
        adjustment_tiers=tiers,
    )
