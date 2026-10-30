-- Read-only SQLite checks; each violation query should return zero rows.
PRAGMA foreign_key_check;
SELECT district_code,COUNT(*) AS n FROM mart_district_pension_outreach GROUP BY district_code HAVING COUNT(*)<>1;
SELECT * FROM fact_district_demographics WHERE population<=0 OR total_households>population OR male_population+female_population<>population;
SELECT * FROM fact_pension_beneficiaries WHERE estimated_beneficiary_count<0 OR is_estimate<>1;
SELECT * FROM mart_district_pension_outreach WHERE pension_outreach_priority_score NOT BETWEEN 0 AND 100 OR elderly_share IS NOT NULL;
SELECT * FROM ml_district_features WHERE high_priority<>CASE WHEN priority_category='High' THEN 1 ELSE 0 END;
WITH totals AS (SELECT scheme,SUM(estimated_beneficiary_count) AS n FROM fact_pension_beneficiaries GROUP BY scheme)
SELECT * FROM totals WHERE n<>CASE scheme WHEN 'old_age' THEN 993567 WHEN 'widow' THEN 272108 WHEN 'disability' THEN 31286 END;
