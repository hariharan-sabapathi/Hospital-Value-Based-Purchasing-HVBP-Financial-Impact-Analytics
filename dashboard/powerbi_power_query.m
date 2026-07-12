// powerbi_power_query.m
//
// Power BI Desktop setup:
//   Home -> Get Data -> Blank Query -> Advanced Editor -> paste one of the
//   queries below -> update <PROJECT_ROOT> to your local path.
//
// This connects directly to the pipeline's CSV outputs. If you point
// config.yaml's database.connection_string at Postgres/Snowflake instead
// of SQLite, use Get Data -> Database connectors and skip this file -
// query sql/analysis.sql's named queries directly as native SQL queries.

// ---- Main fact table (loaded from the processed dataset) ----
let
    Source = Csv.Document(
        File.Contents("<PROJECT_ROOT>\data\processed\hospital_scores_processed.csv"),
        [Delimiter=",", Columns=13, Encoding=1252, QuoteStyle=QuoteStyle.Csv]
    ),
    PromotedHeaders = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    ChangedTypes = Table.TransformColumnTypes(PromotedHeaders,{
        {"provider_id", type text},
        {"clinical_score", type number},
        {"safety_score", type number},
        {"efficiency_score", type number},
        {"patient_experience_score", type number},
        {"total_performance_score", type number},
        {"hospital_name", type text},
        {"state", type text},
        {"city", type text},
        {"reimbursement_risk", type text},
        {"adjustment_rate", type number},
        {"estimated_base_revenue", type number},
        {"projected_adjustment", type number}
    })
in
    ChangedTypes

// ---- Financial impact matrix (pre-ranked export from analysis.sql) ----
// let
//     Source = Csv.Document(
//         File.Contents("<PROJECT_ROOT>\data\processed\analysis_exports\financial_impact_matrix.csv"),
//         [Delimiter=",", Columns=8, Encoding=1252, QuoteStyle=QuoteStyle.Csv]
//     ),
//     PromotedHeaders = Table.PromoteHeaders(Source, [PromoteAllScalars=true])
// in
//     PromotedHeaders

// ---- State averages (for the filled map on the Executive Summary page) ----
// let
//     Source = Csv.Document(
//         File.Contents("<PROJECT_ROOT>\data\processed\analysis_exports\state_averages.csv"),
//         [Delimiter=",", Columns=3, Encoding=1252, QuoteStyle=QuoteStyle.Csv]
//     ),
//     PromotedHeaders = Table.PromoteHeaders(Source, [PromoteAllScalars=true])
// in
//     PromotedHeaders
