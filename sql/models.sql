-- Silver tables (fact_weather_daily, dim_site) are built from validated pandas frames.
-- Gold tables are materialised here to make exports deterministic and portable.
CREATE OR REPLACE TABLE dim_day AS
SELECT DISTINCT
    CAST(day AS DATE) AS day,
    year(CAST(day AS DATE)) AS year,
    month(CAST(day AS DATE)) AS month,
    strftime(CAST(day AS DATE), '%Y-%m') AS year_month
FROM fact_weather_daily;

CREATE OR REPLACE TABLE mart_weather_monthly AS
SELECT
    d.year_month,
    f.dataset,
    count(*) AS days,
    round(avg(f.temp_max_c), 1) AS avg_max_c,
    round(sum(f.rain_mm), 1) AS total_rain_mm,
    round(avg(f.outdoor_score), 1) AS avg_outdoor_score
FROM fact_weather_daily f
JOIN dim_day d ON d.day = f.day
GROUP BY 1, 2
ORDER BY 1, 2;

CREATE OR REPLACE TABLE mart_sites_category AS
SELECT
    category,
    count(*) AS site_count,
    count(*) FILTER (WHERE website <> '') AS with_website,
    round(count(*) FILTER (WHERE website <> '') * 100.0 / count(*), 1) AS website_coverage_pct
FROM dim_site
GROUP BY 1
ORDER BY site_count DESC, category;

CREATE OR REPLACE TABLE mart_forecast AS
SELECT
    day,
    temp_max_c,
    temp_min_c,
    rain_mm,
    wind_kmh,
    outdoor_score,
    CASE
        WHEN outdoor_score IS NULL THEN 'Non disponible'
        WHEN outdoor_score >= 65 THEN 'Favorable selon le score'
        ELSE 'À surveiller selon le score'
    END AS interpretation
FROM fact_weather_daily
WHERE dataset = 'forecast'
ORDER BY day;
