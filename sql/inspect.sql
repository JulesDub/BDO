-- À exécuter avec DuckDB sur data/local/observatory.duckdb.
SELECT COUNT(*) AS weather_days FROM fact_weather_daily;
SELECT dataset, COUNT(*) AS rows FROM fact_weather_daily GROUP BY dataset;
SELECT * FROM mart_weather_monthly ORDER BY year_month DESC LIMIT 12;
SELECT * FROM mart_sites_category ORDER BY site_count DESC;
SELECT name, category, latitude, longitude FROM dim_site ORDER BY name LIMIT 20;
