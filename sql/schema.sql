-- SQLite >=3.37 (STRICT tables); foreign_keys must be enabled per connection.
CREATE TABLE IF NOT EXISTS dim_district (
 district_code TEXT PRIMARY KEY, district_name TEXT NOT NULL UNIQUE,
 state_code TEXT NOT NULL CHECK(state_code='20'), state_name TEXT NOT NULL
) STRICT;
CREATE TABLE IF NOT EXISTS fact_district_demographics (
 district_code TEXT PRIMARY KEY REFERENCES dim_district(district_code),
 census_year INTEGER NOT NULL, population INTEGER NOT NULL CHECK(population>0),
 male_population INTEGER NOT NULL CHECK(male_population>=0),
 female_population INTEGER NOT NULL CHECK(female_population>=0),
 literate_population INTEGER NOT NULL CHECK(literate_population BETWEEN 0 AND population),
 total_workers INTEGER NOT NULL CHECK(total_workers BETWEEN 0 AND population),
 sc_population INTEGER NOT NULL CHECK(sc_population BETWEEN 0 AND population),
 st_population INTEGER NOT NULL CHECK(st_population BETWEEN 0 AND population),
 total_households INTEGER NOT NULL CHECK(total_households BETWEEN 1 AND population),
 CHECK(male_population+female_population=population), CHECK(sc_population+st_population<=population)
) STRICT;
CREATE TABLE IF NOT EXISTS fact_district_housing (
 district_code TEXT PRIMARY KEY REFERENCES dim_district(district_code), census_year INTEGER NOT NULL,
 total_households INTEGER NOT NULL CHECK(total_households>0), household_count_source TEXT NOT NULL,
 dilapidated_pct REAL NOT NULL CHECK(dilapidated_pct BETWEEN 0 AND 100),
 open_defecation_pct REAL NOT NULL CHECK(open_defecation_pct BETWEEN 0 AND 100)
) STRICT;
CREATE TABLE IF NOT EXISTS fact_pension_beneficiaries (
 district_code TEXT NOT NULL REFERENCES dim_district(district_code),
 scheme TEXT NOT NULL CHECK(scheme IN ('old_age','widow','disability')),
 estimated_beneficiary_count INTEGER NOT NULL CHECK(estimated_beneficiary_count>=0),
 reference_year INTEGER, is_estimate INTEGER NOT NULL CHECK(is_estimate=1),
 PRIMARY KEY(district_code,scheme)
) STRICT;
CREATE TABLE IF NOT EXISTS pension_state_rollup (
 state_code TEXT NOT NULL CHECK(state_code='20'), scheme TEXT NOT NULL,
 estimated_beneficiary_count INTEGER NOT NULL CHECK(estimated_beneficiary_count>=0),
 is_estimate INTEGER NOT NULL CHECK(is_estimate=1), PRIMARY KEY(state_code,scheme)
) STRICT;
CREATE TABLE IF NOT EXISTS district_name_mapping (
 source_name TEXT NOT NULL, district_code TEXT NOT NULL REFERENCES dim_district(district_code),
 raw_name TEXT NOT NULL, standardized_name TEXT NOT NULL, match_method TEXT NOT NULL,
 PRIMARY KEY(source_name,district_code)
) STRICT;
CREATE TABLE IF NOT EXISTS mart_district_pension_outreach (
 district_code TEXT PRIMARY KEY REFERENCES dim_district(district_code),
 district_name TEXT NOT NULL,
 census_year INTEGER NOT NULL,
 pension_reference_year INTEGER,
 population INTEGER NOT NULL CHECK(population>0),
 male_population INTEGER NOT NULL CHECK(male_population>=0),
 female_population INTEGER NOT NULL CHECK(female_population>=0),
 literate_population INTEGER NOT NULL CHECK(literate_population>=0),
 total_workers INTEGER NOT NULL CHECK(total_workers>=0),
 sc_population INTEGER NOT NULL CHECK(sc_population>=0),
 st_population INTEGER NOT NULL CHECK(st_population>=0),
 total_households INTEGER NOT NULL CHECK(total_households>0),
 old_age_estimated_beneficiaries INTEGER NOT NULL CHECK(old_age_estimated_beneficiaries>=0),
 widow_estimated_beneficiaries INTEGER NOT NULL CHECK(widow_estimated_beneficiaries>=0),
 disability_estimated_beneficiaries INTEGER NOT NULL CHECK(disability_estimated_beneficiaries>=0),
 crude_literacy_share REAL NOT NULL CHECK(crude_literacy_share BETWEEN 0 AND 1),
 estimated_old_age_per_1000_population REAL NOT NULL CHECK(estimated_old_age_per_1000_population>=0),
 estimated_widow_per_1000_population REAL NOT NULL CHECK(estimated_widow_per_1000_population>=0),
 estimated_disability_per_1000_population REAL NOT NULL CHECK(estimated_disability_per_1000_population>=0),
 estimated_old_age_widow_per_1000_households REAL NOT NULL CHECK(estimated_old_age_widow_per_1000_households>=0),
 estimated_all_scheme_entries_per_1000_households REAL NOT NULL CHECK(estimated_all_scheme_entries_per_1000_households>=0),
 elderly_share REAL CHECK(elderly_share IS NULL),
 old_age_eligible_coverage REAL CHECK(old_age_eligible_coverage IS NULL),
 widow_eligible_coverage REAL CHECK(widow_eligible_coverage IS NULL),
 pension_values_estimated INTEGER NOT NULL CHECK(pension_values_estimated=1),
 dilapidated_pct REAL NOT NULL CHECK(dilapidated_pct BETWEEN 0 AND 100),
 open_defecation_pct REAL NOT NULL CHECK(open_defecation_pct BETWEEN 0 AND 100),
 normalized_dilapidated REAL NOT NULL CHECK(normalized_dilapidated BETWEEN 0 AND 1),
 normalized_open_defecation REAL NOT NULL CHECK(normalized_open_defecation BETWEEN 0 AND 1),
 normalized_low_literacy REAL NOT NULL CHECK(normalized_low_literacy BETWEEN 0 AND 1),
 normalized_low_old_age_rate REAL NOT NULL CHECK(normalized_low_old_age_rate BETWEEN 0 AND 1),
 normalized_low_widow_rate REAL NOT NULL CHECK(normalized_low_widow_rate BETWEEN 0 AND 1),
 pension_outreach_priority_score REAL NOT NULL CHECK(pension_outreach_priority_score BETWEEN 0 AND 100),
 score_version TEXT NOT NULL,
 priority_rank INTEGER NOT NULL UNIQUE,
 priority_category TEXT NOT NULL CHECK(priority_category IN ('High','Medium','Low'))
) STRICT;
CREATE TABLE IF NOT EXISTS ml_district_features (
 district_code TEXT PRIMARY KEY REFERENCES dim_district(district_code),
 population_per_household REAL NOT NULL CHECK(population_per_household>0),
 female_population_share REAL NOT NULL CHECK(female_population_share BETWEEN 0 AND 1),
 crude_literacy_share REAL NOT NULL CHECK(crude_literacy_share BETWEEN 0 AND 1),
 work_participation_rate REAL NOT NULL CHECK(work_participation_rate BETWEEN 0 AND 1),
 sc_population_share REAL NOT NULL CHECK(sc_population_share BETWEEN 0 AND 1),
 st_population_share REAL NOT NULL CHECK(st_population_share BETWEEN 0 AND 1),
 dilapidated_share REAL NOT NULL CHECK(dilapidated_share BETWEEN 0 AND 1),
 open_defecation_share REAL NOT NULL CHECK(open_defecation_share BETWEEN 0 AND 1),
 estimated_old_age_per_1000_population REAL NOT NULL CHECK(estimated_old_age_per_1000_population>=0),
 estimated_widow_per_1000_population REAL NOT NULL CHECK(estimated_widow_per_1000_population>=0),
 estimated_disability_per_1000_population REAL NOT NULL CHECK(estimated_disability_per_1000_population>=0),
 estimated_old_age_widow_per_1000_households REAL NOT NULL CHECK(estimated_old_age_widow_per_1000_households>=0),
 estimated_all_scheme_entries_per_1000_households REAL NOT NULL CHECK(estimated_all_scheme_entries_per_1000_households>=0),
 elderly_share REAL CHECK(elderly_share IS NULL),
 old_age_eligible_coverage REAL CHECK(old_age_eligible_coverage IS NULL),
 widow_eligible_coverage REAL CHECK(widow_eligible_coverage IS NULL),
 pension_values_estimated INTEGER NOT NULL CHECK(pension_values_estimated=1),
 pension_outreach_priority_score REAL NOT NULL,
 priority_category TEXT NOT NULL,
 high_priority INTEGER NOT NULL CHECK(high_priority IN (0,1)),
 score_version TEXT NOT NULL
) STRICT;
CREATE TABLE IF NOT EXISTS etl_run_log (
 run_id TEXT PRIMARY KEY, logical_date TEXT NOT NULL, started_at TEXT NOT NULL, ended_at TEXT,
 status TEXT NOT NULL CHECK(status IN ('RUNNING','SUCCEEDED','FAILED')), error TEXT,
 input_fingerprint TEXT, config_sha256 TEXT NOT NULL, code_sha256 TEXT NOT NULL,
 output_path TEXT
) STRICT;
CREATE TABLE IF NOT EXISTS source_ingestion_manifest (
 run_id TEXT NOT NULL REFERENCES etl_run_log(run_id), source_name TEXT NOT NULL,
 filename TEXT NOT NULL, source_url TEXT NOT NULL, source_year INTEGER, sha256 TEXT NOT NULL,
 ingestion_timestamp TEXT NOT NULL, raw_rows INTEGER NOT NULL CHECK(raw_rows>=0), bronze_path TEXT NOT NULL,
 PRIMARY KEY(run_id,source_name)
) STRICT;
CREATE TABLE IF NOT EXISTS rejected_records (
 run_id TEXT NOT NULL REFERENCES etl_run_log(run_id), source_name TEXT NOT NULL,
 source_row INTEGER NOT NULL, reason TEXT NOT NULL, raw_record TEXT NOT NULL,
 PRIMARY KEY(run_id,source_name,source_row)
) STRICT;
CREATE TABLE IF NOT EXISTS data_quality_results (
 run_id TEXT NOT NULL REFERENCES etl_run_log(run_id), check_id TEXT NOT NULL,
 status TEXT NOT NULL CHECK(status IN ('PASS','WARN','FAIL')),
 expected_result TEXT NOT NULL, actual_result TEXT NOT NULL, severity TEXT NOT NULL,
 affected_records TEXT NOT NULL, recommended_resolution TEXT NOT NULL,
 PRIMARY KEY(run_id,check_id)
) STRICT;
