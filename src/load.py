"""
load.py

Loads the processed DataFrame into the configured SQL database and executes
the analysis queries defined in sql/analysis.sql.

Uses SQLAlchemy so the `dialect` / `connection_string` in config.yaml can be
swapped from SQLite (used here for a self-contained local demo) to
Postgres or Snowflake in production with no code changes.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine


def get_engine(connection_string: str) -> Engine:
    """Create a SQLAlchemy engine from a config-supplied connection string."""
    return create_engine(connection_string)


def execute_schema(engine: Engine, schema_path: Path, logger: logging.Logger) -> None:
    """Run the DDL in sql/schema.sql against the target database."""
    ddl = schema_path.read_text(encoding="utf-8")
    with engine.begin() as conn:
        for statement in filter(None, (s.strip() for s in ddl.split(";"))):
            conn.execute(text(statement))
    logger.info("Schema applied from %s", schema_path.name)


def load_dataframe(
    df: pd.DataFrame,
    engine: Engine,
    table_name: str,
    logger: logging.Logger,
) -> None:
    """Load the processed DataFrame into the target SQL table."""
    df.to_sql(table_name, engine, if_exists="replace", index=False)
    logger.info("Loaded %d rows into table '%s'", len(df), table_name)


def _split_named_queries(sql_text: str) -> dict[str, str]:
    """Split analysis.sql into named queries using '-- name: <label>' markers."""
    pattern = re.compile(r"--\s*name:\s*(\w+)\s*\n(.*?)(?=(--\s*name:)|\Z)", re.DOTALL)
    return {m.group(1): m.group(2).strip().rstrip(";") for m in pattern.finditer(sql_text)}


def run_named_queries(
    engine: Engine, analysis_sql_path: Path, logger: logging.Logger
) -> dict[str, pd.DataFrame]:
    """Execute every named query in analysis.sql and return results by name."""
    sql_text = analysis_sql_path.read_text(encoding="utf-8")
    queries = _split_named_queries(sql_text)

    results: dict[str, pd.DataFrame] = {}
    with engine.connect() as conn:
        for name, query in queries.items():
            logger.info("Running analysis query: %s", name)
            results[name] = pd.read_sql(text(query), conn)
    return results
