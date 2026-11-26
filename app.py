"""Read-only public dashboard. Network ingestion never runs in the web process."""
from __future__ import annotations

from pathlib import Path
import pandas as pd
import plotly.express as px
import streamlit as st

from src.config import Paths
from src.storage import read_json

PATHS = Paths()
st.set_page_config(page_title="Observatoire des données | Brest", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
    .block-container {max-width: 1280px; padding-top: 2.2rem;}
    h1, h2, h3 {font-family: 'Segoe UI', Arial, sans-serif; letter-spacing: -0.025em;}
    h1 {font-weight: 650; font-size: 2.1rem;}
    [data-testid="stMetric"] {padding: 0 0 0.7rem 0; border-bottom: 1px solid #d7dde2;}
    [data-testid="stSidebar"] {border-right: 1px solid #d7dde2;}
    [data-testid="stMetricLabel"] {font-size: 0.88rem;}
    .data-note {font-size: 0.85rem; color: #596777;}
</style>
""", unsafe_allow_html=True)


@st.cache_data(ttl=300)
def load_public_data(root: str) -> tuple[dict, dict[str, pd.DataFrame]]:
    paths = Paths(Path(root))
    manifest = read_json(paths.published / "manifest.json")
    expected = ("weather_daily.csv", "sites.csv", "weather_monthly.csv", "sites_by_category.csv", "forecast.csv")
    missing = [name for name in expected if not (paths.published / name).is_file()]
    if not manifest or missing:
        raise FileNotFoundError("Fichiers publiés manquants : " + ", ".join(missing or ["manifest.json"]))
    tables = {name.removesuffix(".csv"): pd.read_csv(paths.published / name) for name in expected}
    if not manifest.get("run_id") or tables["weather_daily"].empty or tables["sites"].empty:
        raise ValueError("Snapshot incomplet : manifeste ou données vides")
    return manifest, tables


@st.cache_data(ttl=300)
def source_sql() -> str:
    return (PATHS.model_sql).read_text(encoding="utf-8")


def formatted_chart(fig, *, height: int = 335):
    fig.update_layout(
        template="plotly_white",
        font=dict(family="Segoe UI, Arial", size=12, color="#263746"),
        margin=dict(l=10, r=12, t=20, b=15),
        height=height,
        legend_title_text="",
        hovermode="x unified",
        paper_bgcolor="rgba(0,0,0,0)",
    )
    return fig


st.sidebar.markdown("### Observatoire des données")
st.sidebar.caption("Brest et environs")
st.sidebar.divider()

try:
    manifest, data = load_public_data(str(PATHS.root))
except (FileNotFoundError, ValueError) as exc:
    st.title("Observatoire des données")
    st.error("Le jeu de données public n'a pas encore été généré ou n'est pas complet.")
    st.code("python -m src.pipeline\npython -m streamlit run app.py", language="powershell")
    st.caption(f"Diagnostic : {exc}")
    st.stop()

weather = data["weather_daily"]
sites = data["sites"]
monthly = data["weather_monthly"]
by_category = data["sites_by_category"]
forecast = data["forecast"]
weather["day"] = pd.to_datetime(weather["day"], errors="coerce")
forecast["day"] = pd.to_datetime(forecast["day"], errors="coerce")

last_update = manifest.get("completed_at_utc", "inconnue")
st.sidebar.caption(f"Mise à jour des données : {last_update}")
if manifest.get("source", {}).get("sites_fallback"):
    st.sidebar.warning("Les sites proviennent de l'export précédent : source indisponible lors de la dernière ingestion.")
st.sidebar.markdown("**Origine des données**")
st.sidebar.markdown("[Open-Meteo](https://open-meteo.com/)  ·  [OpenStreetMap](https://www.openstreetmap.org/copyright)")
st.sidebar.divider()
st.sidebar.caption("Projet indépendant. Aucune affiliation avec Brest en vue.")

st.title("Observatoire des données brestoises")
st.write("Sites touristiques recensés et conditions météorologiques : des sources ouvertes à une lecture exploitable.")
st.caption("Périmètre géographique approximatif ; ni statistiques de fréquentation ni recommandations officielles.")

summary, sites_tab, weather_tab, audit_tab = st.tabs([
    "Vue d'ensemble", "Sites touristiques", "Météo et prévisions", "Données et qualité"
])

with summary:
    hist = weather[weather.dataset == "history"]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Sites recensés", f"{len(sites):,}".replace(",", " "))
    c2.metric("Catégories", f"{sites.category.nunique()}")
    c3.metric("Jours météo historiques", f"{len(hist)}")
    c4.metric("Jours de prévisions", f"{len(forecast)}")

    left, right = st.columns([1.2, 1])
    with left:
        st.subheader("Répartition des sites par catégorie")
        fig = px.bar(
            by_category.sort_values("site_count"),
            x="site_count", y="category", orientation="h",
            color_discrete_sequence=["#28566b"],
            labels={"category": "", "site_count": "Nombre de sites"},
            hover_data=["with_website", "website_coverage_pct"],
        )
        st.plotly_chart(formatted_chart(fig, height=380), use_container_width=True)
    with right:
        st.subheader("Prochains jours")
        next_days = forecast.sort_values("day")[["day", "temp_max_c", "rain_mm", "wind_kmh", "outdoor_score"]].copy()
        next_days["day"] = next_days["day"].dt.strftime("%d/%m/%Y")
        next_days.columns = ["Date", "T. max (°C)", "Pluie (mm)", "Vent (km/h)", "Score (0–100)"]
        st.dataframe(next_days, hide_index=True, use_container_width=True)
        st.caption("Le score est une formule pédagogique, non calibrée sur la fréquentation touristique.")

    st.subheader("Périmètre et démarche")
    st.write(
        "L'application combine deux familles de données qui ne mesurent pas la même chose : "
        "un inventaire géographique de lieux issu d'OpenStreetMap, et des séries météorologiques "
        "issues d'Open-Meteo. Elles sont transformées, contrôlées, stockées dans DuckDB, "
        "puis exportées pour le site et pour un outil de business intelligence."
    )

with sites_tab:
    st.subheader("Explorer les sites touristiques")
    categories = sorted(sites.category.dropna().unique().tolist())
    selected_categories = st.multiselect("Catégories", categories, default=categories)
    search = st.text_input("Rechercher un lieu", placeholder="Nom du lieu")
    selection = sites[sites.category.isin(selected_categories)].copy()
    if search.strip():
        selection = selection[selection.name.str.contains(search.strip(), case=False, na=False, regex=False)]
    st.caption(f"{len(selection)} sites correspondant aux filtres")
    if selection.empty:
        st.info("Aucun site ne correspond aux filtres actuels.")
    else:
        st.map(selection[["latitude", "longitude"]], latitude="latitude", longitude="longitude", zoom=9)
        show = selection[["name", "category", "website", "osm_url"]].copy()
        show.columns = ["Lieu", "Catégorie", "Site web", "Fiche OSM"]
        st.dataframe(
            show,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Site web": st.column_config.LinkColumn("Site web", display_text="Ouvrir"),
                "Fiche OSM": st.column_config.LinkColumn("Fiche OSM", display_text="Voir la source"),
            },
        )
    st.caption(
        "Un point correspond à un objet OSM nommé dans un périmètre rectangulaire autour de Brest. "
        "La liste n'est pas exhaustive et n'implique aucune validation par les gestionnaires des lieux."
    )

with weather_tab:
    st.subheader("Conditions météorologiques")
    hist = weather[weather.dataset == "history"].sort_values("day").copy()
    a, b = st.columns(2)
    with a:
        fig = px.line(
            hist, x="day", y=["temp_max_c", "temp_min_c"],
            labels={"day": "Date", "value": "Température (°C)", "variable": "Série"},
            color_discrete_sequence=["#26566b", "#9a7845"],
        )
        st.plotly_chart(formatted_chart(fig), use_container_width=True)
    with b:
        fig = px.bar(
            hist, x="day", y="rain_mm",
            labels={"day": "Date", "rain_mm": "Précipitations (mm)"},
            color_discrete_sequence=["#4c8299"],
        )
        st.plotly_chart(formatted_chart(fig), use_container_width=True)

    st.subheader("Prévisions et indice illustratif")
    threshold = st.slider("Seuil de lecture du score", min_value=0, max_value=100, value=65, step=5)
    future = forecast.dropna(subset=["outdoor_score"]).copy()
    if not future.empty:
        future["lecture"] = future.outdoor_score.apply(lambda score: "Au-dessus du seuil" if score >= threshold else "Sous le seuil")
        fig = px.bar(
            future, x="day", y="outdoor_score", color="lecture",
            color_discrete_map={"Au-dessus du seuil": "#28566b", "Sous le seuil": "#a28a67"},
            labels={"day": "Jour", "outdoor_score": "Score (0–100)"},
        )
        fig.add_hline(y=threshold, line_dash="dash", line_color="#526678")
        fig.update_yaxes(range=[0, 105])
        st.plotly_chart(formatted_chart(fig), use_container_width=True)
    st.caption(
        "L'indice pénalise la pluie, le vent et les températures éloignées de 20 °C. "
        "Il est arbitraire : un score élevé ne garantit ni confort, ni sécurité, ni affluence."
    )
    st.subheader("Agrégation mensuelle calculée en SQL")
    st.dataframe(monthly, hide_index=True, use_container_width=True)

with audit_tab:
    st.subheader("Qualité des données et traçabilité")
    quality = manifest.get("quality", {})
    check_weather = quality.get("weather", {})
    check_sites = quality.get("sites", {})
    left, right = st.columns(2)
    with left:
        st.markdown("**Météorologie**")
        st.metric("Complétude des mesures", f"{check_weather.get('measurement_completeness_pct', 0)} %")
        st.metric("Clés dupliquées", check_weather.get("duplicate_keys", "—"))
        st.json(check_weather)
    with right:
        st.markdown("**Lieux touristiques**")
        st.metric("Sites avec adresse web", f"{check_sites.get('website_pct', 0)} %")
        st.metric("Identifiants dupliqués", check_sites.get("duplicate_ids", "—"))
        st.json(check_sites)

    st.markdown("**Dernière exécution**")
    st.json({k: value for k, value in manifest.items() if k != "quality"})

    st.markdown("**Télécharger les tables publiées**")
    for name, label in (
        ("weather_daily", "Météo quotidienne"),
        ("sites", "Sites touristiques"),
        ("weather_monthly", "Indicateurs mensuels"),
        ("sites_by_category", "Sites par catégorie"),
    ):
        st.download_button(
            label,
            data=data[name].to_csv(index=False).encode("utf-8-sig"),
            file_name=name + ".csv", mime="text/csv", key="export_" + name,
        )
    with st.expander("Voir les transformations SQL"):
        st.code(source_sql(), language="sql")
    st.markdown("**Sources et droits**")
    st.markdown(
        "Données météo : [Open-Meteo](https://open-meteo.com/) (CC BY 4.0). "
        "Lieux : [contributeurs OpenStreetMap](https://www.openstreetmap.org/copyright) (ODbL). "
        "L'historique est issu de modèles/réanalyses, pas d'une station météo locale unique. "
        "Cette démonstration est indépendante de Brest en vue."
    )
