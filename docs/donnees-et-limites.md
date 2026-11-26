# Données, qualité et limites

## Origine des données

Les données météorologiques proviennent des API historiques et prévisionnelles d'Open-Meteo pour les coordonnées de Brest. L'inventaire des lieux provient des objets OpenStreetMap portant un attribut `tourism` et un nom, situés dans un périmètre rectangulaire autour de Brest.

Les données collectées ne représentent ni la fréquentation touristique ni les réservations, la billetterie ou les recettes des établissements.

## Contrôles appliqués

`src/quality.py` vérifie notamment :

- la présence et l'ordre des colonnes attendues ;
- l'unicité de la paire `(day, dataset)` pour la météo ;
- la validité des dates et la cohérence entre températures minimale et maximale ;
- l'absence de précipitations ou vitesses de vent négatives ;
- l'unicité des identifiants OSM et la validité des coordonnées ;
- la présence des séries historiques et prévisionnelles.

Une mesure de complétude des valeurs météo et une mesure de couverture des sites avec URL sont consignées dans `manifest.json`. Les observations invalides ne sont pas remplacées arbitrairement. Les objets OSM incomplets sont filtrés durant la normalisation.

La base DuckDB est recréée dans un fichier temporaire puis remplacée. Le manifeste est écrit après les exports afin d'indiquer l'achèvement de leur publication ; ces opérations ne constituent toutefois pas une transaction atomique multi-fichiers.

## Limites

**Disponibilité** : la fiabilité de la collecte dépend de services externes, en particulier des serveurs Overpass publics.

**Couverture** : OpenStreetMap repose sur des contributions. Certains lieux peuvent être absents, mal renseignés ou représentés différemment (`node`, `way`, `relation`). Le rectangle sélectionné ne constitue pas une limite administrative.

**Météorologie** : les données portent sur un seul point géographique. L'historique Open-Meteo peut provenir de modèles ou de réanalyses, pas nécessairement d'une station locale.

**Indice extérieur** : le score de 0 à 100 est une heuristique calculée à partir de la température, de la pluie et du vent. Il n'a pas fait l'objet d'une validation scientifique ; il n'est ni un indicateur de sécurité ni une prévision d'affluence.

**Exploitation** : l'application constitue une démonstration technique. Elle ne fournit ni surveillance de production, ni accord de disponibilité, ni stratégie de reprise complète.

## Attribution

- OpenStreetMap contributors : [www.openstreetmap.org/copyright](https://www.openstreetmap.org/copyright), ODbL.
- Open-Meteo : [open-meteo.com](https://open-meteo.com/), licence et conditions propres aux API utilisées.

Toute réutilisation publique des données et des éventuels fonds de carte doit respecter les conditions des fournisseurs.
