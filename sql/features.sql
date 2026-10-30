-- Spark SQL. This policy target does not establish an independent predictive outcome.
SELECT district_code,
 population*1.0/total_households AS population_per_household,
 female_population*1.0/population AS female_population_share,
 crude_literacy_share,
 total_workers*1.0/population AS work_participation_rate,
 sc_population*1.0/population AS sc_population_share,
 st_population*1.0/population AS st_population_share,
 estimated_old_age_per_1000_population,estimated_widow_per_1000_population,
 estimated_disability_per_1000_population,estimated_old_age_widow_per_1000_households,
 estimated_all_scheme_entries_per_1000_households,
 dilapidated_pct/100.0 AS dilapidated_share,open_defecation_pct/100.0 AS open_defecation_share,
 elderly_share,old_age_eligible_coverage,widow_eligible_coverage,
 pension_values_estimated,pension_outreach_priority_score,priority_category,
 CASE WHEN priority_category='High' THEN 1 ELSE 0 END AS high_priority,score_version
FROM mart_district_pension_outreach
