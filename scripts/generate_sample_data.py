"""
generate_sample_data.py

DEV/DEMO UTILITY ONLY - not part of the production pipeline.

Generates synthetic data shaped exactly like the real CMS HVBP + Hospital
General Information datasets, so the pipeline (main.py) can be exercised
end-to-end without network access to data.cms.gov.

Replace the files this script writes to data/raw/ with the real CMS exports
for an actual production run:
  - Hospital VBP Total Performance Score:
    https://data.cms.gov/provider-data/dataset/hospital-value-based-purchasing-hvbp-total-performance-score
  - Hospital General Information:
    https://data.cms.gov/provider-data/dataset/xubh-q36u
"""

from __future__ import annotations

import random
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_ROOT / "data" / "raw"

STATES = ["NY", "CA", "TX", "FL", "PA", "OH", "IL", "GA", "NC", "MI"]
CITY_BY_STATE = {
    "NY": ["Buffalo", "Albany", "Rochester"],
    "CA": ["Los Angeles", "Sacramento", "Fresno"],
    "TX": ["Austin", "Dallas", "Houston"],
    "FL": ["Miami", "Orlando", "Tampa"],
    "PA": ["Pittsburgh", "Philadelphia", "Erie"],
    "OH": ["Columbus", "Cleveland", "Toledo"],
    "IL": ["Chicago", "Springfield", "Peoria"],
    "GA": ["Atlanta", "Savannah", "Macon"],
    "NC": ["Charlotte", "Raleigh", "Durham"],
    "MI": ["Detroit", "Lansing", "Flint"],
}


def generate(n_hospitals: int = 250, seed: int = 42) -> None:
    random.seed(seed)
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    hospital_rows = []
    hvbp_rows = []

    for i in range(1, n_hospitals + 1):
        provider_id = f"{100000 + i}"
        state = random.choice(STATES)
        city = random.choice(CITY_BY_STATE[state])
        facility_type = random.choice(
            ["General", "Regional", "Memorial", "Community", "University"]
        )
        hospital_name = f"{city} {facility_type} Hospital"

        hospital_rows.append(
            {
                "Facility ID": provider_id,
                "Facility Name": hospital_name,
                "State": state,
                "City": city,
            }
        )

        clinical = round(random.gauss(65, 15), 1)
        safety = round(random.gauss(65, 15), 1)
        efficiency = round(random.gauss(65, 15), 1)
        patient_exp = round(random.gauss(65, 15), 1)

        # A few intentionally messy rows to exercise the validation layer.
        if i % 47 == 0:
            total = None  # missing score
        elif i % 61 == 0:
            total = 137.0  # out-of-range anomaly
        else:
            total = round(
                sum(
                    max(0, min(100, v))
                    for v in (clinical, safety, efficiency, patient_exp)
                )
                / 4,
                1,
            )

        hvbp_rows.append(
            {
                "Provider ID": provider_id,
                "Clinical Outcomes Score": clinical,
                "Safety Score": safety,
                "Efficiency Score": efficiency,
                "Patient Experience Score": patient_exp,
                "Total Performance Score": total,
            }
        )

    # Inject one duplicate provider_id to exercise the duplicate check.
    hvbp_rows.append(hvbp_rows[0].copy())

    pd.DataFrame(hospital_rows).to_csv(RAW_DIR / "hospital_general_info.csv", index=False)
    pd.DataFrame(hvbp_rows).to_csv(RAW_DIR / "hvbp_total_performance.csv", index=False)

    print(f"Sample data written to {RAW_DIR}")
    print(f"  hospital_general_info.csv: {len(hospital_rows)} rows")
    print(f"  hvbp_total_performance.csv: {len(hvbp_rows)} rows")


if __name__ == "__main__":
    generate()
