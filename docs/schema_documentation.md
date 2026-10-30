# Database schema and grain

SQLite 3.37+ STRICT; foreign_keys enabled per connection. Business tables hold the latest successful snapshot. All pension measures are estimates.

## data_quality_results

Grain: One run/check.

| Column | Type | Required | Primary key position |
|---|---|---|---|
| run_id | TEXT | True | 1 |
| check_id | TEXT | True | 2 |
| status | TEXT | True | 0 |
| expected_result | TEXT | True | 0 |
| actual_result | TEXT | True | 0 |
| severity | TEXT | True | 0 |
| affected_records | TEXT | True | 0 |
| recommended_resolution | TEXT | True | 0 |

Foreign keys: [{"id": 0, "seq": 0, "table": "etl_run_log", "from": "run_id", "to": "run_id", "on_update": "NO ACTION", "on_delete": "NO ACTION", "match": "NONE"}]

```sql
CREATE TABLE data_quality_results (
 run_id TEXT NOT NULL REFERENCES etl_run_log(run_id), check_id TEXT NOT NULL,
 status TEXT NOT NULL CHECK(status IN ('PASS','WARN','FAIL')),
 expected_result TEXT NOT NULL, actual_result TEXT NOT NULL, severity TEXT NOT NULL,
 affected_records TEXT NOT NULL, recommended_resolution TEXT NOT NULL,
 PRIMARY KEY(run_id,check_id)
) STRICT;
```

## dim_district

Grain: One Census district.

| Column | Type | Required | Primary key position |
|---|---|---|---|
| district_code | TEXT | True | 1 |
| district_name | TEXT | True | 0 |
| state_code | TEXT | True | 0 |
| state_name | TEXT | True | 0 |

Foreign keys: []

```sql
CREATE TABLE dim_district (
 district_code TEXT PRIMARY KEY, district_name TEXT NOT NULL UNIQUE,
 state_code TEXT NOT NULL CHECK(state_code='20'), state_name TEXT NOT NULL
) STRICT;
```

## district_name_mapping

Grain: One source/district.

| Column | Type | Required | Primary key position |
|---|---|---|---|
| source_name | TEXT | True | 1 |
| district_code | TEXT | True | 2 |
| raw_name | TEXT | True | 0 |
| standardized_name | TEXT | True | 0 |
| match_method | TEXT | True | 0 |

Foreign keys: [{"id": 0, "seq": 0, "table": "dim_district", "from": "district_code", "to": "district_code", "on_update": "NO ACTION", "on_delete": "NO ACTION", "match": "NONE"}]

```sql
CREATE TABLE district_name_mapping (
 source_name TEXT NOT NULL, district_code TEXT NOT NULL REFERENCES dim_district(district_code),
 raw_name TEXT NOT NULL, standardized_name TEXT NOT NULL, match_method TEXT NOT NULL,
 PRIMARY KEY(source_name,district_code)
) STRICT;
```

## etl_run_log

Grain: One execution attempt.

| Column | Type | Required | Primary key position |
|---|---|---|---|
| run_id | TEXT | True | 1 |
| logical_date | TEXT | True | 0 |
| started_at | TEXT | True | 0 |
| ended_at | TEXT | False | 0 |
| status | TEXT | True | 0 |
| error | TEXT | False | 0 |
| input_fingerprint | TEXT | False | 0 |
| config_sha256 | TEXT | True | 0 |
| code_sha256 | TEXT | True | 0 |
| output_path | TEXT | False | 0 |

Foreign keys: []

```sql
CREATE TABLE etl_run_log (
 run_id TEXT PRIMARY KEY, logical_date TEXT NOT NULL, started_at TEXT NOT NULL, ended_at TEXT,
 status TEXT NOT NULL CHECK(status IN ('RUNNING','SUCCEEDED','FAILED')), error TEXT,
 input_fingerprint TEXT, config_sha256 TEXT NOT NULL, code_sha256 TEXT NOT NULL,
 output_path TEXT
) STRICT;
```

## fact_district_demographics

Grain: One district/latest snapshot.

| Column | Type | Required | Primary key position |
|---|---|---|---|
| district_code | TEXT | True | 1 |
| census_year | INTEGER | True | 0 |
| population | INTEGER | True | 0 |
| male_population | INTEGER | True | 0 |
| female_population | INTEGER | True | 0 |
| literate_population | INTEGER | True | 0 |
| total_workers | INTEGER | True | 0 |
| sc_population | INTEGER | True | 0 |
| st_population | INTEGER | True | 0 |
| total_households | INTEGER | True | 0 |

Foreign keys: [{"id": 0, "seq": 0, "table": "dim_district", "from": "district_code", "to": "district_code", "on_update": "NO ACTION", "on_delete": "NO ACTION", "match": "NONE"}]

```sql
CREATE TABLE fact_district_demographics (
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
```

## fact_district_housing

Grain: One district/latest snapshot.

| Column | Type | Required | Primary key position |
|---|---|---|---|
| district_code | TEXT | True | 1 |
| census_year | INTEGER | True | 0 |
| total_households | INTEGER | True | 0 |
| household_count_source | TEXT | True | 0 |
| dilapidated_pct | REAL | True | 0 |
| open_defecation_pct | REAL | True | 0 |

Foreign keys: [{"id": 0, "seq": 0, "table": "dim_district", "from": "district_code", "to": "district_code", "on_update": "NO ACTION", "on_delete": "NO ACTION", "match": "NONE"}]

```sql
CREATE TABLE fact_district_housing (
 district_code TEXT PRIMARY KEY REFERENCES dim_district(district_code), census_year INTEGER NOT NULL,
 total_households INTEGER NOT NULL CHECK(total_households>0), household_count_source TEXT NOT NULL,
 dilapidated_pct REAL NOT NULL CHECK(dilapidated_pct BETWEEN 0 AND 100),
 open_defecation_pct REAL NOT NULL CHECK(open_defecation_pct BETWEEN 0 AND 100)
) STRICT;
```

## fact_pension_beneficiaries

Grain: One district/scheme estimate.

| Column | Type | Required | Primary key position |
|---|---|---|---|
| district_code | TEXT | True | 1 |
| scheme | TEXT | True | 2 |
| estimated_beneficiary_count | INTEGER | True | 0 |
| reference_year | INTEGER | False | 0 |
| is_estimate | INTEGER | True | 0 |

Foreign keys: [{"id": 0, "seq": 0, "table": "dim_district", "from": "district_code", "to": "district_code", "on_update": "NO ACTION", "on_delete": "NO ACTION", "match": "NONE"}]

```sql
CREATE TABLE fact_pension_beneficiaries (
 district_code TEXT NOT NULL REFERENCES dim_district(district_code),
 scheme TEXT NOT NULL CHECK(scheme IN ('old_age','widow','disability')),
 estimated_beneficiary_count INTEGER NOT NULL CHECK(estimated_beneficiary_count>=0),
 reference_year INTEGER, is_estimate INTEGER NOT NULL CHECK(is_estimate=1),
 PRIMARY KEY(district_code,scheme)
) STRICT;
```

## mart_district_pension_outreach

Grain: One district.

| Column | Type | Required | Primary key position |
|---|---|---|---|
| district_code | TEXT | True | 1 |
| district_name | TEXT | True | 0 |
| census_year | INTEGER | True | 0 |
| pension_reference_year | INTEGER | False | 0 |
| population | INTEGER | True | 0 |
| male_population | INTEGER | True | 0 |
| female_population | INTEGER | True | 0 |
| literate_population | INTEGER | True | 0 |
| total_workers | INTEGER | True | 0 |
| sc_population | INTEGER | True | 0 |
| st_population | INTEGER | True | 0 |
| total_households | INTEGER | True | 0 |
| old_age_estimated_beneficiaries | INTEGER | True | 0 |
| widow_estimated_beneficiaries | INTEGER | True | 0 |
| disability_estimated_beneficiaries | INTEGER | True | 0 |
| crude_literacy_share | REAL | True | 0 |
| estimated_old_age_per_1000_population | REAL | True | 0 |
| estimated_widow_per_1000_population | REAL | True | 0 |
| estimated_disability_per_1000_population | REAL | True | 0 |
| estimated_old_age_widow_per_1000_households | REAL | True | 0 |
| estimated_all_scheme_entries_per_1000_households | REAL | True | 0 |
| elderly_share | REAL | False | 0 |
| old_age_eligible_coverage | REAL | False | 0 |
| widow_eligible_coverage | REAL | False | 0 |
| pension_values_estimated | INTEGER | True | 0 |
| dilapidated_pct | REAL | True | 0 |
| open_defecation_pct | REAL | True | 0 |
| normalized_dilapidated | REAL | True | 0 |
| normalized_open_defecation | REAL | True | 0 |
| normalized_low_literacy | REAL | True | 0 |
| normalized_low_old_age_rate | REAL | True | 0 |
| normalized_low_widow_rate | REAL | True | 0 |
| pension_outreach_priority_score | REAL | True | 0 |
| score_version | TEXT | True | 0 |
| priority_rank | INTEGER | True | 0 |
| priority_category | TEXT | True | 0 |

Foreign keys: [{"id": 0, "seq": 0, "table": "dim_district", "from": "district_code", "to": "district_code", "on_update": "NO ACTION", "on_delete": "NO ACTION", "match": "NONE"}]

```sql
CREATE TABLE mart_district_pension_outreach (
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
```

## ml_district_features

Grain: One district.

| Column | Type | Required | Primary key position |
|---|---|---|---|
| district_code | TEXT | True | 1 |
| population_per_household | REAL | True | 0 |
| female_population_share | REAL | True | 0 |
| crude_literacy_share | REAL | True | 0 |
| work_participation_rate | REAL | True | 0 |
| sc_population_share | REAL | True | 0 |
| st_population_share | REAL | True | 0 |
| dilapidated_share | REAL | True | 0 |
| open_defecation_share | REAL | True | 0 |
| estimated_old_age_per_1000_population | REAL | True | 0 |
| estimated_widow_per_1000_population | REAL | True | 0 |
| estimated_disability_per_1000_population | REAL | True | 0 |
| estimated_old_age_widow_per_1000_households | REAL | True | 0 |
| estimated_all_scheme_entries_per_1000_households | REAL | True | 0 |
| elderly_share | REAL | False | 0 |
| old_age_eligible_coverage | REAL | False | 0 |
| widow_eligible_coverage | REAL | False | 0 |
| pension_values_estimated | INTEGER | True | 0 |
| pension_outreach_priority_score | REAL | True | 0 |
| priority_category | TEXT | True | 0 |
| high_priority | INTEGER | True | 0 |
| score_version | TEXT | True | 0 |

Foreign keys: [{"id": 0, "seq": 0, "table": "dim_district", "from": "district_code", "to": "district_code", "on_update": "NO ACTION", "on_delete": "NO ACTION", "match": "NONE"}]

```sql
CREATE TABLE ml_district_features (
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
```

## pension_state_rollup

Grain: One state/scheme derived estimate total.

| Column | Type | Required | Primary key position |
|---|---|---|---|
| state_code | TEXT | True | 1 |
| scheme | TEXT | True | 2 |
| estimated_beneficiary_count | INTEGER | True | 0 |
| is_estimate | INTEGER | True | 0 |

Foreign keys: []

```sql
CREATE TABLE pension_state_rollup (
 state_code TEXT NOT NULL CHECK(state_code='20'), scheme TEXT NOT NULL,
 estimated_beneficiary_count INTEGER NOT NULL CHECK(estimated_beneficiary_count>=0),
 is_estimate INTEGER NOT NULL CHECK(is_estimate=1), PRIMARY KEY(state_code,scheme)
) STRICT;
```

## rejected_records

Grain: One run/source/logical record.

| Column | Type | Required | Primary key position |
|---|---|---|---|
| run_id | TEXT | True | 1 |
| source_name | TEXT | True | 2 |
| source_row | INTEGER | True | 3 |
| reason | TEXT | True | 0 |
| raw_record | TEXT | True | 0 |

Foreign keys: [{"id": 0, "seq": 0, "table": "etl_run_log", "from": "run_id", "to": "run_id", "on_update": "NO ACTION", "on_delete": "NO ACTION", "match": "NONE"}]

```sql
CREATE TABLE rejected_records (
 run_id TEXT NOT NULL REFERENCES etl_run_log(run_id), source_name TEXT NOT NULL,
 source_row INTEGER NOT NULL, reason TEXT NOT NULL, raw_record TEXT NOT NULL,
 PRIMARY KEY(run_id,source_name,source_row)
) STRICT;
```

## source_ingestion_manifest

Grain: One run/source.

| Column | Type | Required | Primary key position |
|---|---|---|---|
| run_id | TEXT | True | 1 |
| source_name | TEXT | True | 2 |
| filename | TEXT | True | 0 |
| source_url | TEXT | True | 0 |
| source_year | INTEGER | False | 0 |
| sha256 | TEXT | True | 0 |
| ingestion_timestamp | TEXT | True | 0 |
| raw_rows | INTEGER | True | 0 |
| bronze_path | TEXT | True | 0 |

Foreign keys: [{"id": 0, "seq": 0, "table": "etl_run_log", "from": "run_id", "to": "run_id", "on_update": "NO ACTION", "on_delete": "NO ACTION", "match": "NONE"}]

```sql
CREATE TABLE source_ingestion_manifest (
 run_id TEXT NOT NULL REFERENCES etl_run_log(run_id), source_name TEXT NOT NULL,
 filename TEXT NOT NULL, source_url TEXT NOT NULL, source_year INTEGER, sha256 TEXT NOT NULL,
 ingestion_timestamp TEXT NOT NULL, raw_rows INTEGER NOT NULL CHECK(raw_rows>=0), bronze_path TEXT NOT NULL,
 PRIMARY KEY(run_id,source_name)
) STRICT;
```

## Relationships and prevention of duplication

District dimension keys are parents of all district facts and the two derived tables. Pension keys are composite district/scheme; source mapping keys are source/district. Run IDs are parents of manifests, rejections and quality results. Gold has a unique priority_rank. A transactional derived-table refresh avoids transient rank collisions; stable Silver keys UPSERT. No cascaded deletes conceal missing districts. Before a load, all expected district sets and 72 pension facts are validated. See sql/analytics.sql for join/aggregate/CTE/window examples.

## Units and missing values

Population counts and supplied pension estimates are nonnegative integers. Census household counts are source-defined. Housing percentages use 0–100; ML shares use 0–1. Pension rates use entries per 1,000 total population or source households. Crude literacy uses all ages. Three unsupported metrics (elderly share and old-age/widow eligibility coverage) and pension reference year are NULL. Scheme totals need not represent distinct people. The score's 0–100 scale is not a probability or coverage percentage.
