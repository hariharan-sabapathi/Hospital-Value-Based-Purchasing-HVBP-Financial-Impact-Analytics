# Power BI Dashboard - DAX Measures & Page Layout

> A `.pbix` is a proprietary binary Power BI Desktop must generate — it can't
> be authored as plain text. Import `hospital_scores_processed.csv` (or the
> `analysis_exports/` CSVs) using `powerbi_power_query.m`, add the measures
> below, then build the pages per this spec. Total setup time: ~20 minutes.

## Data model
Single table `hospital_scores` from `data/processed/hospital_scores_processed.csv`.
Optionally add `analysis_exports/state_averages.csv` as a second table related
on `state` for the map visual.

## DAX Measures

```dax
Avg Total Performance Score =
AVERAGE(hospital_scores[total_performance_score])

Hospitals At High Risk =
CALCULATE(
    COUNTROWS(hospital_scores),
    hospital_scores[reimbursement_risk] = "High Risk"
)

Top Performing Hospital =
CALCULATE(
    SELECTEDVALUE(hospital_scores[hospital_name]),
    TOPN(1, hospital_scores, hospital_scores[total_performance_score], DESC)
)

Total Projected Adjustment =
SUM(hospital_scores[projected_adjustment])

Total Revenue At Risk =
CALCULATE(
    SUM(hospital_scores[projected_adjustment]),
    hospital_scores[projected_adjustment] < 0
)

Total Revenue Upside =
CALCULATE(
    SUM(hospital_scores[projected_adjustment]),
    hospital_scores[projected_adjustment] > 0
)

Hospital Count =
COUNTROWS(hospital_scores)

% Hospitals High Risk =
DIVIDE([Hospitals At High Risk], [Hospital Count])
```

## Page 1 — Executive Summary
- **KPI cards:** `Avg Total Performance Score`, `Total Projected Adjustment`,
  `Hospitals At High Risk`, `Top Performing Hospital`
- **Filled map:** state (shape map or filled map visual) colored by
  average `total_performance_score`
- **Slicer:** `state`

## Page 2 — Performance Analysis
- **Bar chart:** Top 20 hospitals by `total_performance_score`
  (source: `analysis_exports/top_20_hospitals.csv`)
- **Bar chart:** Bottom 20 hospitals by `total_performance_score`
  (source: `analysis_exports/bottom_20_hospitals.csv`)
- **Scatter plot:** `clinical_score` (x) vs `total_performance_score` (y),
  sized by hospital count, colored by `reimbursement_risk`
- **Box-and-whisker (custom visual from AppSource):** score distribution
  by `reimbursement_risk`

## Page 3 — Financial Impact
- **Matrix visual:** `hospital_name`, `total_performance_score`,
  `reimbursement_risk`, `adjustment_rate`, `estimated_base_revenue`,
  `projected_adjustment` (source: `analysis_exports/financial_impact_matrix.csv`)
- **Waterfall chart:** `projected_adjustment` by `reimbursement_risk`
  category, showing cumulative revenue gain/loss
- **Slicers:** `state`, `hospital_name`, `reimbursement_risk`

## Notes on the financial model
The dollar figures on this dashboard use a documented, simplified
adjustment model (see `config/config.yaml -> financial_model`), not CMS's
actual VBP payment-adjustment formula. This is disclosed on the dashboard
and in the README so the assumption is transparent to any reviewer.
