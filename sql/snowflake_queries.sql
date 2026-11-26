-- Run these statements after `python -m src.snowflake_sync` succeeded.
-- Schema is already selected through the connection config.

SELECT DATASET, COUNT(*) AS NB_LIGNES,
       ROUND(AVG(TEMP_MAX_C), 1) AS TEMP_MAX_MOYENNE
FROM BREST_WEATHER_DAILY
GROUP BY DATASET
ORDER BY DATASET;

SELECT CATEGORY, COUNT(*) AS NB_SITES
FROM BREST_TOURISM_SITES
GROUP BY CATEGORY
ORDER BY NB_SITES DESC;

-- Avoid using a running virtual warehouse when not needed:
-- ALTER WAREHOUSE <YOUR_WAREHOUSE> SUSPEND;
