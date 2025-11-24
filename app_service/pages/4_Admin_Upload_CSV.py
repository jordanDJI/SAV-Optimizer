# app_service/pages/4_Admin_Upload_CSV.py

from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

import streamlit as st
import pandas as pd

from backend.auth.session_utils import require_auth
from backend.data_pipeline.enrichment_pipeline import run_full_pipeline
from backend.data_pipeline.storage import load_enriched_tweets
from backend.analytics.kpis_analyst import compute_kpis
from backend.analytics.report_builder import compute_detailed_stats, build_text_report

# ----------------- CONFIG -----------------
st.set_page_config(page_title="SAV Free - Admin", page_icon="🛠️", layout="wide")
require_auth(["admin"])

# ----------------- STYLE -----------------
st.markdown(
    """
    <style>
    .main-header {
        font-size: 1.6rem;
        font-weight: 700;
        margin-bottom: 0.25rem;
    }
    .main-subtitle {
        color: #9ca3af;
        margin-bottom: 1rem;
    }
    .card {
        padding: 0.9rem 1rem;
        border-radius: 0.75rem;
        background-color: #020617;
        border: 1px solid #1f2937;
        margin-bottom: 0.75rem;
    }
    .badge-ok {
        display:inline-block;
        padding: 0.15rem 0.5rem;
        border-radius: 999px;
        background-color: #16a34a33;
        color: #bbf7d0;
        font-size: 0.8rem;
    }
    .badge-ko {
        display:inline-block;
        padding: 0.15rem 0.5rem;
        border-radius: 999px;
        background-color: #b91c1c33;
        color: #fecaca;
        font-size: 0.8rem;
    }
    .section-title {
        font-size: 1.1rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
    }
    .small-label {
        font-size: 0.85rem;
        color: #9ca3af;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown("<div class='main-header'>🛠️ Espace Admin – Pilotage du pipeline</div>", unsafe_allow_html=True)
st.markdown(
    "<div class='main-subtitle'>Import du CSV, exécution du pipeline (nettoyage + NLP + LLM), "
    "synthèse rapide et accès aux espaces Agent / Manager / Analyste.</div>",
    unsafe_allow_html=True,
)

# ----------------- NAVIGATION RAPIDE -----------------
with st.container():
    st.markdown("<div class='section-title'>🔀 Navigation rapide</div>", unsafe_allow_html=True)
    col_nav1, col_nav2, col_nav3 = st.columns(3)

    with col_nav1:
        if st.button("📞 Espace Agent", use_container_width=True):
            st.switch_page("pages/1_Agent.py")
    with col_nav2:
        if st.button("📊 Espace Manager", use_container_width=True):
            st.switch_page("pages/2_Manager.py")
    with col_nav3:
        if st.button("🔎 Espace Analyste", use_container_width=True):
            st.switch_page("pages/3_Analyst.py")

st.markdown("---")

# ----------------- FICHIERS EXISTANTS -----------------
RAW_PATH = Path("data/raw/tweets.csv")
PREPARED_PATH = Path("data/processed/tweets_prepared.csv")
ENRICHED_PATH = Path("data/processed/tweets_enriched.csv")

raw_exists = RAW_PATH.exists()
prepared_exists = PREPARED_PATH.exists()
enriched_exists = ENRICHED_PATH.exists()

st.markdown("<div class='section-title'>📂 État des fichiers</div>", unsafe_allow_html=True)

c_files1, c_files2, c_files3 = st.columns(3)

with c_files1:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("**Fichier brut**", unsafe_allow_html=True)
    st.markdown(f"<div class='small-label'>{RAW_PATH}</div>", unsafe_allow_html=True)
    st.markdown(
        "<span class='badge-ok'>Présent</span>" if raw_exists else "<span class='badge-ko'>Manquant</span>",
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)

with c_files2:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("**Préparé (nettoyé)**", unsafe_allow_html=True)
    st.markdown(f"<div class='small-label'>{PREPARED_PATH}</div>", unsafe_allow_html=True)
    st.markdown(
        "<span class='badge-ok'>Présent</span>" if prepared_exists else "<span class='badge-ko'>Manquant</span>",
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)

with c_files3:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("**Enrichi (NLP + LLM)**", unsafe_allow_html=True)
    st.markdown(f"<div class='small-label'>{ENRICHED_PATH}</div>", unsafe_allow_html=True)
    st.markdown(
        "<span class='badge-ok'>Présent</span>" if enriched_exists else "<span class='badge-ko'>Manquant</span>",
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)

# ----------------- FONCTION D'AFFICHAGE KPIs + RAPPORT -----------------
def display_kpis_and_report_from_enriched():
    try:
        df_final = load_enriched_tweets(ENRICHED_PATH)
    except FileNotFoundError:
        st.error("Impossible de charger `tweets_enriched.csv`.")
        return

    if df_final.empty:
        st.info("Le fichier enrichi est vide.")
        return

    kpis = compute_kpis(df_final)
    gc = kpis["global_counts"]

    st.markdown("<div class='section-title'>📊 Synthèse rapide</div>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("**Tweets enrichis**", unsafe_allow_html=True)
        st.markdown(f"<div class='kpi-value'>{gc['total_tweets']}</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with c2:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("**Plaintes (finales)**", unsafe_allow_html=True)
        st.markdown(f"<div class='kpi-value'>{gc['complaints_final']}</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with c3:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("**Retenus pour analyse**", unsafe_allow_html=True)
        st.markdown(f"<div class='kpi-value'>{gc.get('kept_for_analysis', 'N/A')}</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    df_raw = pd.read_csv(RAW_PATH, dtype=str) if RAW_PATH.exists() else None
    df_prepared = pd.read_csv(PREPARED_PATH, dtype=str) if PREPARED_PATH.exists() else None

    stats = compute_detailed_stats(df_raw, df_prepared, df_final)
    report_text = build_text_report(stats)

    st.markdown("<div class='section-title'>📄 Rapport synthétique</div>", unsafe_allow_html=True)
    st.markdown(
        "Ce rapport résume l’ensemble des statistiques (volumes, réponses Free, filtres, intents, plaintes, "
        "priorités, sentiment…)."
    )

    st.markdown(report_text)

    report_bytes = report_text.encode("utf-8")
    st.download_button(
        label="💾 Télécharger le rapport complet (Markdown)",
        data=report_bytes,
        file_name="rapport_sav_free_tweets_admin.md",
        mime="text/markdown",
    )

# ----------------- LOGIQUE DES CAS -----------------
# Cas 1 : tout existe déjà
if raw_exists and prepared_exists and enriched_exists:
    st.success(
        "Les fichiers **tweets.csv**, **tweets_prepared.csv** et **tweets_enriched.csv** existent déjà. "
        "Aucun nouveau traitement n'est nécessaire pour la présentation."
    )
    display_kpis_and_report_from_enriched()

# Cas 2 : aucun fichier → upload obligatoire
elif not raw_exists and not prepared_exists and not enriched_exists:
    st.warning(
        "Aucun fichier n'est encore présent.\n\n"
        "Merci d'importer un CSV brut de tweets pour lancer le pipeline complet."
    )

    st.markdown("<div class='section-title'>📤 Import du CSV brut</div>", unsafe_allow_html=True)
    uploaded = st.file_uploader("Importer un fichier CSV de tweets", type=["csv"])

    if uploaded is not None:
        RAW_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(RAW_PATH, "wb") as f:
            f.write(uploaded.getvalue())
        st.success(f"Fichier uploadé enregistré sous : `{RAW_PATH}`")

        if st.button("🚀 Lancer le pipeline complet (prétraitement + NLP + LLM)"):
            with st.spinner("Traitement en cours..."):
                df_final, kpis = run_full_pipeline(RAW_PATH, limit_llm=None)
            st.success("Pipeline terminé ✅. Résultat dans `data/processed/tweets_enriched.csv`.")
            display_kpis_and_report_from_enriched()

# Cas 3 : brut présent mais pas enrichi
elif raw_exists and not enriched_exists:
    st.info(
        "Le fichier brut `tweets.csv` est présent, mais aucun résultat enrichi n'a été généré.\n\n"
        "Tu peux lancer le **pipeline complet** (nettoyage + NLP + LLM)."
    )

    if st.button("🚀 Lancer le pipeline complet à partir de tweets.csv"):
        with st.spinner("Traitement en cours (prétraitement + NLP + LLM)..."):
            df_final, kpis = run_full_pipeline(RAW_PATH, limit_llm=None)
        st.success("Pipeline terminé ✅. Résultat dans `data/processed/tweets_enriched.csv`.")
        display_kpis_and_report_from_enriched()

# Cas 4 : état intermédiaire (incomplet / incohérent)
else:
    st.warning(
        "État intermédiaire détecté (par exemple `tweets_prepared.csv` existe mais pas les autres).\n\n"
        "Par sécurité, importe à nouveau un CSV brut puis relance le pipeline complet."
    )

    st.markdown("<div class='section-title'>📤 Réimport d'un CSV propre</div>", unsafe_allow_html=True)
    uploaded = st.file_uploader("Importer un fichier CSV de tweets (pour refaire le pipeline)", type=["csv"])

    if uploaded is not None:
        RAW_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(RAW_PATH, "wb") as f:
            f.write(uploaded.getvalue())
        st.success(f"Nouveau fichier brut enregistré sous : `{RAW_PATH}`")

        if st.button("🚀 Relancer le pipeline complet"):
            with st.spinner("Traitement en cours..."):
                df_final, kpis = run_full_pipeline(RAW_PATH, limit_llm=None)
            st.success("Pipeline terminé ✅.")
            display_kpis_and_report_from_enriched()
