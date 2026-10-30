-- SQLite: outputs are supplied ESTIMATES, never official district observations.
SELECT district_name,priority_rank,pension_outreach_priority_score,priority_category,old_age_estimated_beneficiaries,estimated_old_age_per_1000_population
FROM mart_district_pension_outreach ORDER BY priority_rank;
SELECT scheme,SUM(estimated_beneficiary_count) AS total_estimated_entries
FROM fact_pension_beneficiaries GROUP BY scheme;
WITH category_totals AS (
 SELECT priority_category,SUM(population) AS population,SUM(literate_population) AS literate
 FROM mart_district_pension_outreach GROUP BY priority_category
)
SELECT priority_category,100.0*literate/population AS crude_literacy_percent FROM category_totals;
SELECT district_name,priority_category,pension_outreach_priority_score,
 ROW_NUMBER() OVER(PARTITION BY priority_category ORDER BY pension_outreach_priority_score DESC,district_code) AS rank_within_category
FROM mart_district_pension_outreach;
SELECT status,COUNT(*) AS runs FROM etl_run_log GROUP BY status;
