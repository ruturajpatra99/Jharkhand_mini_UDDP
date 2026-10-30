-- Executed by Spark SQL after Silver views have been registered.
WITH pension_wide AS (
 SELECT district_code,
  MAX(CASE WHEN scheme='old_age' THEN estimated_beneficiary_count END) AS old_age_estimated_beneficiaries,
  MAX(CASE WHEN scheme='widow' THEN estimated_beneficiary_count END) AS widow_estimated_beneficiaries,
  MAX(CASE WHEN scheme='disability' THEN estimated_beneficiary_count END) AS disability_estimated_beneficiaries
 FROM fact_pension_beneficiaries GROUP BY district_code
)
SELECT d.district_code,d.district_name,f.census_year,
 CAST(NULL AS INT) AS pension_reference_year,
 f.population,f.male_population,f.female_population,f.literate_population,
 f.literate_population*1.0/f.population AS crude_literacy_share,
 f.total_workers,f.sc_population,f.st_population,f.total_households,
 p.old_age_estimated_beneficiaries,p.widow_estimated_beneficiaries,p.disability_estimated_beneficiaries,
 p.old_age_estimated_beneficiaries*1000.0/f.population AS estimated_old_age_per_1000_population,
 p.widow_estimated_beneficiaries*1000.0/f.population AS estimated_widow_per_1000_population,
 p.disability_estimated_beneficiaries*1000.0/f.population AS estimated_disability_per_1000_population,
 (p.old_age_estimated_beneficiaries+p.widow_estimated_beneficiaries)*1000.0/f.total_households AS estimated_old_age_widow_per_1000_households,
 (p.old_age_estimated_beneficiaries+p.widow_estimated_beneficiaries+p.disability_estimated_beneficiaries)*1000.0/f.total_households AS estimated_all_scheme_entries_per_1000_households,
 CAST(NULL AS DOUBLE) AS elderly_share,
 CAST(NULL AS DOUBLE) AS old_age_eligible_coverage,
 CAST(NULL AS DOUBLE) AS widow_eligible_coverage,
 1 AS pension_values_estimated,
 h.dilapidated_pct,h.open_defecation_pct
FROM dim_district d
INNER JOIN fact_district_demographics f ON d.district_code=f.district_code
INNER JOIN fact_district_housing h ON d.district_code=h.district_code
INNER JOIN pension_wide p ON d.district_code=p.district_code
