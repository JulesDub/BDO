# Brest Data Observatory

Application de collecte et d'exploration de données ouvertes sur Brest et ses environs. Le projet associe un inventaire de points d'intérêt issus d'OpenStreetMap et des séries météorologiques obtenues auprès d'Open-Meteo.

L'objectif est de disposer d'une chaîne de traitement reproductible, depuis les réponses API jusqu'à des tables SQL et un tableau de bord. Il s'agit d'un projet personnel, sans lien avec Brest en vue ni accès à ses données internes.

## Périmètre

- Collecte de l'historique et des prévisions météorologiques pour Brest via Open-Meteo.
- Extraction de points d'intérêt touristiques nommés via l'API Overpass d'OpenStreetMap.
- Normalisation des réponses JSON et contrôles de qualité avec Python et pandas.
- Stockage analytique avec DuckDB ; agrégations définies en SQL.
- Publication de fichiers CSV et d'un manifeste décrivant chaque exécution.
- Consultation des résultats dans une application Streamlit / Plotly.

Les exports ne contiennent ni statistiques de fréquentation, ni données de vente ou de réservation. L'indice météo affiché est une formule indicative et non une prévision de fréquentation.

## Architecture

```text
Open-Meteo -----> Python / pandas -----> Validation -----> DuckDB
OpenStreetMap -> Python / pandas -----> Validation          |
                                                          SQL
                                                           |
                                                CSV + manifest.json
                                                           |
                                                        Streamlit
```

Le pipeline de collecte et l'interface sont indépendants : Streamlit lit les exports préparés, sans appeler directement les API. Les réponses JSON et le fichier DuckDB restent locaux ; seuls les exports validés de `data/published/` peuvent être versionnés.

## Installation

Python 3.12 ou 3.13, accès Internet pour la collecte. Depuis la racine du projet, sous Windows :

```powershell
py -3.13 -m venv .venv313
.\.venv313\Scripts\python.exe -m pip install -r requirements.txt
.\.venv313\Scripts\python.exe -m pytest -q
.\.venv313\Scripts\python.exe -m src.pipeline
.\.venv313\Scripts\python.exe -m streamlit run app.py
```

Le tableau de bord est accessible sur `http://localhost:8501`. Pour Python 3.12, remplacer `-3.13` par `-3.12`. L'activation de l'environnement virtuel n'est pas nécessaire.

Les serveurs Overpass sont publics et peuvent être indisponibles. Si une extraction précédente a réussi, `python -m src.pipeline --allow-stale-sites` permet de réutiliser l'inventaire validé en signalant explicitement ce choix dans le manifeste. Sans extraction initiale, le pipeline ne produit pas de données de remplacement.

## Organisation du dépôt

| Chemin | Rôle |
| --- | --- |
| `src/pipeline.py` | Exécution de la collecte, des validations et des exports |
| `src/weather.py`, `src/sites.py` | Normalisation des deux sources |
| `src/quality.py` | Contrôles de structure et de cohérence |
| `src/warehouse.py` | Écriture des tables et exécution des modèles SQL |
| `sql/models.sql` | Agrégations et tables analytiques |
| `app.py` | Interface Streamlit sur données publiées |
| `tests/` | Tests unitaires et d'intégration à partir de données de test |
| `data/published/` | Exports destinés à la visualisation, lorsqu'ils ont été générés |
| `docs/` | Architecture, exploitation et limites |

## État du projet

La chaîne principale Python / pandas / DuckDB / Streamlit est implémentée. Son exécution de bout en bout nécessite que les deux API répondent et qu'un premier jeu d'exports soit produit. Les tests automatisés ne dépendent pas du réseau ; ils utilisent des données de test.

Des fichiers de démonstration sont également présents pour Snowflake et Airflow. Ils sont facultatifs et ne font pas partie du chemin d'exécution principal. Aucun rapport Power BI n'est livré.

## Documentation

- [Architecture et modèle de données](docs/architecture.md)
- [Installation, exécution et déploiement](docs/exploitation.md)
- [Qualité, sources et limites](docs/donnees-et-limites.md)

## Sources et licences

- [OpenStreetMap contributors](https://www.openstreetmap.org/copyright) : données ODbL ; les conditions d'attribution et de réutilisation restent applicables.
- [Open-Meteo](https://open-meteo.com/) : conditions de l'API et licence des données selon le service utilisé.

L'inventaire OpenStreetMap n'est pas exhaustif. Le périmètre d'extraction est un rectangle géographique et ne correspond pas aux limites administratives de Brest. Le point météo représente Brest, pas la situation exacte de chaque lieu.
