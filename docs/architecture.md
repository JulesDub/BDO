# Architecture et modèle de données

## Chaîne de traitement

Le point d'entrée est `python -m src.pipeline`. L'exécution suit cinq étapes :

1. `src/weather.py` demande à Open-Meteo un historique quotidien et sept jours de prévisions pour les coordonnées de Brest.
2. `src/sites.py` formule une requête Overpass pour récupérer des objets OpenStreetMap avec catégorie touristique, nom et coordonnées.
3. Les réponses sont converties en DataFrames pandas. `src/quality.py` vérifie les contrats de données avant chargement.
4. `src/warehouse.py` construit un nouveau fichier DuckDB, y charge les tables de référence puis exécute `sql/models.sql`.
5. `src/pipeline.py` exporte les résultats en CSV et écrit `manifest.json` en fin de traitement. `app.py` ne consomme que ces exports.

Les réponses JSON brutes sont conservées dans `data/raw/` pour inspection locale. La base DuckDB est enregistrée dans `data/local/observatory.duckdb`. Ces dossiers ne sont pas destinés à Git.

## Tables

| Table | Contenu | Granularité |
| --- | --- | --- |
| `fact_weather_daily` | Températures, pluie, vent et indice indicatif | Une date et un type de série (`history` / `forecast`) |
| `dim_site` | Nom, catégorie, coordonnées et identifiant OSM | Un objet OpenStreetMap |
| `dim_day` | Attributs calendaires | Une date |
| `mart_weather_monthly` | Moyennes et cumuls mensuels | Mois et type de série |
| `mart_sites_category` | Nombre de lieux et couverture des URL | Catégorie de lieu |
| `mart_forecast` | Prévisions quotidiennes et libellé de l'indice | Date de prévision |

Le modèle de données ne relie pas un site à sa propre météo : les mesures correspondent aux coordonnées de Brest.

## Choix techniques

DuckDB convient au traitement analytique local, sans serveur de base de données à administrer. Le pipeline matérialise les indicateurs en SQL pour éviter de recalculer toute la logique dans Streamlit. Les exports CSV rendent la couche de restitution indépendante de la base locale.

L'extraction ne se fait pas à l'ouverture de la page. Le dashboard peut donc fonctionner sans disponibilité immédiate d'Overpass ou d'Open-Meteo, à condition que des exports aient déjà été produits.

## Modules complémentaires

`src/snowflake_sync.py` présente un chargement facultatif vers Snowflake, avec configuration externe. `dags/brest_daily.py` contient un DAG Airflow et `airflow/` une configuration locale. Ces éléments sont séparés du pipeline principal et ne sont pas nécessaires pour utiliser le dashboard.
