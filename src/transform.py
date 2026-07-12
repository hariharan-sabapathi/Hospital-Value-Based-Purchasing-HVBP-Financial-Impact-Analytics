"""
transform.py

Applies the reimbursement-risk classification and financial impact model
on top of the cleaned, validated dataset. The adjustment tiers and the
assumed base revenue are entirely config-driven (config.yaml), never
hardcoded here.
"""

from __future__ import annotations

import logging

import pandas as pd

from src.settings import AdjustmentTier


def classify_risk(score: float, tiers: list[AdjustmentTier]) -> tuple[str, float]:
    """Return (risk_label, adjustment_rate) for a given score using the
    configured tiers. Tiers must be pre-sorted descending by min_score."""
    if pd.isna(score):
        return "Unknown", 0.0
    for tier in tiers:
        if score >= tier.min_score:
            return tier.label, tier.adjustment_rate
    return tiers[-1].label, tiers[-1].adjustment_rate


def apply_financial_model(
    df: pd.DataFrame,
    tiers: list[AdjustmentTier],
    base_revenue: float,
    logger: logging.Logger,
) -> pd.DataFrame:
    """Add reimbursement_risk, adjustment_rate, and projected_adjustment columns."""
    df = df.copy()

    classifications = df["total_performance_score"].apply(lambda s: classify_risk(s, tiers))
    df["reimbursement_risk"] = classifications.apply(lambda t: t[0])
    df["adjustment_rate"] = classifications.apply(lambda t: t[1])

    df["estimated_base_revenue"] = base_revenue
    df["projected_adjustment"] = df["estimated_base_revenue"] * df["adjustment_rate"]

    risk_counts = df["reimbursement_risk"].value_counts().to_dict()
    logger.info("Reimbursement risk distribution: %s", risk_counts)

    total_at_risk = df.loc[df["projected_adjustment"] < 0, "projected_adjustment"].sum()
    logger.info("Total projected revenue at risk: $%.2f", total_at_risk)

    return df
