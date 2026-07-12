"""
validate.py

Automated data-quality validation layer. Runs a set of documented checks
against the cleaned/merged dataset, logs any failures loudly, and writes a
validation_report.csv artifact for auditability. This module never silently
drops bad rows - it flags them so downstream consumers (and reviewers) can
see exactly what was found.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

import pandas as pd


@dataclass(frozen=True)
class ValidationResult:
    check_name: str
    passed: bool
    failure_count: int
    details: str


def check_required_columns(df: pd.DataFrame, required_columns: list[str]) -> ValidationResult:
    missing = [c for c in required_columns if c not in df.columns]
    return ValidationResult(
        check_name="required_columns_present",
        passed=len(missing) == 0,
        failure_count=len(missing),
        details=f"Missing columns: {missing}" if missing else "All required columns present",
    )


def check_missing_provider_ids(df: pd.DataFrame) -> ValidationResult:
    missing = int(df["provider_id"].isnull().sum()) if "provider_id" in df.columns else -1
    return ValidationResult(
        check_name="missing_provider_ids",
        passed=missing == 0,
        failure_count=max(missing, 0),
        details=f"{missing} rows with null provider_id",
    )


def check_duplicate_providers(df: pd.DataFrame) -> ValidationResult:
    dupes = int(df["provider_id"].duplicated().sum()) if "provider_id" in df.columns else -1
    return ValidationResult(
        check_name="duplicate_provider_ids",
        passed=dupes == 0,
        failure_count=max(dupes, 0),
        details=f"{dupes} duplicate provider_id rows",
    )


def check_null_scores(df: pd.DataFrame) -> ValidationResult:
    col = "total_performance_score"
    nulls = int(df[col].isnull().sum()) if col in df.columns else -1
    return ValidationResult(
        check_name="null_total_performance_scores",
        passed=nulls == 0,
        failure_count=max(nulls, 0),
        details=f"{nulls} rows with null total_performance_score",
    )


def check_score_range(
    df: pd.DataFrame, min_score: float, max_score: float
) -> ValidationResult:
    col = "total_performance_score"
    if col not in df.columns:
        return ValidationResult("score_within_valid_range", False, -1, "Column not found")

    out_of_range = df[(df[col] < min_score) | (df[col] > max_score)]
    return ValidationResult(
        check_name="score_within_valid_range",
        passed=len(out_of_range) == 0,
        failure_count=len(out_of_range),
        details=f"{len(out_of_range)} rows outside [{min_score}, {max_score}]",
    )


def run_validation_suite(
    df: pd.DataFrame,
    required_columns: list[str],
    min_score: float,
    max_score: float,
    logger: logging.Logger,
) -> list[ValidationResult]:
    """Run every check and log a summary. Does not raise on failure by default -
    callers can inspect results and decide whether to halt the pipeline."""
    checks = [
        check_required_columns(df, required_columns),
        check_missing_provider_ids(df),
        check_duplicate_providers(df),
        check_null_scores(df),
        check_score_range(df, min_score, max_score),
    ]

    for result in checks:
        if result.passed:
            logger.info("[PASS] %s - %s", result.check_name, result.details)
        else:
            logger.warning("[FAIL] %s - %s", result.check_name, result.details)

    return checks


def export_validation_report(
    df: pd.DataFrame,
    checks: list[ValidationResult],
    output_path: Path,
    logger: logging.Logger,
) -> None:
    """Write both a per-column null summary and the check outcomes to disk."""
    null_summary = pd.DataFrame(
        {"column": df.columns, "missing_count": df.isnull().sum().values}
    )

    check_summary = pd.DataFrame(
        [
            {
                "check_name": c.check_name,
                "passed": c.passed,
                "failure_count": c.failure_count,
                "details": c.details,
            }
            for c in checks
        ]
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        handle.write("# Column Null Summary\n")
        null_summary.to_csv(handle, index=False)
        handle.write("\n# Validation Check Summary\n")
        check_summary.to_csv(handle, index=False)

    logger.info("Validation report written to %s", output_path)
