"""
main.py

Entry point for the Financial Reimbursement & Value-Based Purchasing
Analytics pipeline. Orchestrates extract -> clean -> validate -> transform
-> load -> analyze in a single, config-driven run.

Usage:
    python main.py
    python main.py --config config/config.yaml
    python main.py --skip-validation-halt   # log validation failures but continue
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from src import clean, extract, load, transform, validate
from src.settings import CONFIG_PATH, load_settings
from src.utils.logger import get_logger


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the HVBP financial reimbursement analytics pipeline."
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=CONFIG_PATH,
        help="Path to config.yaml (default: config/config.yaml)",
    )
    parser.add_argument(
        "--halt-on-validation-failure",
        action="store_true",
        help="Abort the pipeline if any validation check fails.",
    )
    return parser.parse_args()


def run_pipeline(config_path: Path, halt_on_validation_failure: bool) -> int:
    settings = load_settings(config_path)
    logger = get_logger(
        name="hvbp_pipeline",
        log_file=settings.log_file,
        level=settings.log_level,
        max_bytes=settings.log_max_bytes,
        backup_count=settings.log_backup_count,
    )

    logger.info("=== Pipeline run started ===")

    # 1. Extract
    hvbp_raw, hospital_raw = extract.extract(
        settings.hvbp_raw_path, settings.hospital_info_raw_path, logger
    )

    # 2. Clean
    hvbp_clean = clean.clean_hvbp(hvbp_raw, logger)
    hospital_clean = (
        clean.clean_hospital_info(hospital_raw, logger) if hospital_raw is not None else None
    )
    merged = clean.merge_datasets(hvbp_clean, hospital_clean, logger)

    # 3. Validate
    checks = validate.run_validation_suite(
        merged,
        required_columns=settings.required_columns,
        min_score=settings.min_valid_score,
        max_score=settings.max_valid_score,
        logger=logger,
    )
    validate.export_validation_report(merged, checks, settings.validation_report_path, logger)

    any_failed = any(not c.passed for c in checks)
    if any_failed:
        logger.warning("One or more validation checks failed. See validation report.")
        if halt_on_validation_failure:
            logger.error(
                "Halting pipeline due to validation failures (--halt-on-validation-failure)."
            )
            return 1

    # 4. Transform (risk classification + financial impact model)
    enriched = transform.apply_financial_model(
        merged,
        tiers=settings.adjustment_tiers,
        base_revenue=settings.assumed_base_medicare_revenue,
        logger=logger,
    )

    settings.processed_path.parent.mkdir(parents=True, exist_ok=True)
    enriched.to_csv(settings.processed_path, index=False)
    logger.info("Processed dataset written to %s", settings.processed_path)

    # 5. Load into SQL
    engine = load.get_engine(settings.db_connection_string)
    load.execute_schema(engine, settings.sql_dir / "schema.sql", logger)
    load.load_dataframe(enriched, engine, settings.db_target_table, logger)

    # 6. Run analysis queries (powers the Power BI dashboard exports)
    results = load.run_named_queries(engine, settings.sql_dir / "analysis.sql", logger)
    export_dir = settings.processed_dir / "analysis_exports"
    export_dir.mkdir(parents=True, exist_ok=True)
    for name, df in results.items():
        out_path = export_dir / f"{name}.csv"
        df.to_csv(out_path, index=False)
        logger.info("Exported analysis result '%s' -> %s (%d rows)", name, out_path, len(df))

    logger.info("=== Pipeline run completed successfully ===")
    return 0


def main() -> None:
    args = parse_args()
    exit_code = run_pipeline(args.config, args.halt_on_validation_failure)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
