# Data quality report

{'PASS': 37, 'WARN': 4, 'FAIL': 0}

| Check | Expected | Actual | Status | Severity | Resolution |
|---|---|---|---|---|---|
| demographics_row_reconciliation | 640 | 640 | PASS | ERROR | None |
| demographics_expected_districts | 24 | 24 | PASS | ERROR | None |
| demographics_valid_records | 0 | 0 | PASS | ERROR | None |
| demographics_exact_duplicates | 0 | 0 | PASS | WARNING | None |
| housing_row_reconciliation | 640 | 640 | PASS | ERROR | None |
| housing_expected_districts | 24 | 24 | PASS | ERROR | None |
| housing_valid_records | 0 | 0 | PASS | ERROR | None |
| housing_exact_duplicates | 0 | 0 | PASS | WARNING | None |
| pensions_row_reconciliation | 24 | 24 | PASS | ERROR | None |
| pensions_expected_districts | 24 | 24 | PASS | ERROR | None |
| pensions_valid_records | 0 | 0 | PASS | ERROR | None |
| pensions_exact_duplicates | 0 | 0 | PASS | WARNING | None |
| district_matching | 0 | 0 | PASS | ERROR | None |
| dim_district_unique_key | 0 | 0 | PASS | ERROR | None |
| fact_district_demographics_unique_key | 0 | 0 | PASS | ERROR | None |
| fact_district_housing_unique_key | 0 | 0 | PASS | ERROR | None |
| fact_pension_beneficiaries_unique_key | 0 | 0 | PASS | ERROR | None |
| district_name_mapping_unique_key | 0 | 0 | PASS | ERROR | None |
| pension_state_rollup_unique_key | 0 | 0 | PASS | ERROR | None |
| district_names_unique | 0 | 0 | PASS | ERROR | None |
| pension_total_old_age | 993567 | 993567 | PASS | ERROR | None |
| pension_total_widow | 272108 | 272108 | PASS | ERROR | None |
| pension_total_disability | 31286 | 31286 | PASS | ERROR | None |
| demographics_ingestion_freshness | 0..24 hours | 0.0278969775 | PASS | ERROR | None |
| housing_ingestion_freshness | 0..24 hours | 0.027883149722222222 | PASS | ERROR | None |
| pensions_ingestion_freshness | 0..24 hours | 0.027883149722222222 | PASS | ERROR | None |
| observation_currency | Current aligned observation periods | Census 2011; pension period unknown | WARN | WARNING | Obtain documented current reference periods before operational use. |
| pension_estimation | Observed district beneficiary counts | Supplied estimates preserved | WARN | WARNING | Validate against official district observations when authorized. |
| eligibility_denominators | Verified elderly and widow eligible populations | Unavailable; corresponding fields NULL | WARN | WARNING | Obtain eligible-population denominators before claiming scheme coverage. |
| household_universe | Verified comparable household universe | Demographic Households count; housing percentages separate | WARN | WARNING | Reconcile official household definitions before interpreting cross-source totals. |
| gold_cardinality | 24 rows and 24 keys | 24 rows / 24 keys | PASS | ERROR | None |
| ml_cardinality | 24 rows and 24 keys | 24 rows / 24 keys | PASS | ERROR | None |
| score_range | 0 | 0 | PASS | ERROR | None |
| priority_thirds | 8 / 8 / 8 | {'High': 8, 'Medium': 8, 'Low': 8} | PASS | ERROR | None |
| target_consistency | 0 | 0 | PASS | ERROR | None |
| old_age_rate_calculation | 0 | 0 | PASS | ERROR | None |
| feature_share_calculation | 0 | 0 | PASS | ERROR | None |
| required_feature_columns | none missing | [] | PASS | ERROR | None |
| sqlite_foreign_keys | 0 | 0 | PASS | ERROR | None |
| sqlite_gold_count | 24 | 24 | PASS | ERROR | None |
| pipeline_completion | All stages succeeded | Spark validated and SQLite transaction ready | PASS | ERROR | None |

Affected record identifiers and rejection details are retained in the JSON/CSV reports.
