# app_service/pages/3_Analyst.py

from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

import streamlit as st
import pandas as pd
import altair as alt
from pandas.api.types import is_datetime64_any_dtype

from backend.auth.session_utils import require_auth
from backend.data_pipeline.storage import load_enriched_tweets
from backend.analytics.report_builder import compute_detailed_stats, build_text_report

# ----------------- CONFIG PAGE -----------------
st.set_page_config(page_title="SAV Free - Analyste", page_icon="🔎", layout="wide")
require_auth(["analyst", "admin"])

# ----------------- STYLE GLOBAL -----------------
st.markdown(
    """
    <style>
    .kpi-card {
        padding: 0.75rem 1rem;
        border-radius: 0.75rem;
        background-color: #0b1120;
        border: 1px solid #1e293b;
    }
    .kpi-label {
        font-size: 0.85rem;
        color: #9ca3af;
        margin-bottom: 0.1rem;
    }
    .kpi-value {
        font-size: 1.3rem;
        font-weight: 600;
        color: #e5e7eb;
    }
    .section-title {
        font-size: 1.1rem;
        font-weight: 600;
        margin-top: 1.5rem;
        margin-bottom: 0.5rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown("## 🔎 Espace Analyste – Vue détaillée")

st.write(
    "Cette vue fournit une analyse **complète** du flux Twitter : volumes, filtrage, "
    "intents, types de plaintes, priorités, sentiments, sarcasme et risque de résiliation."
)

# ----------------- CHARGEMENT DONNÉES -----------------
raw_path = Path("data/raw/tweets.csv")
prepared_path = Path("data/processed/tweets_prepared.csv")
enriched_path = Path("data/processed/tweets_enriched.csv")

df_raw = pd.read_csv(raw_path, dtype=str) if raw_path.exists() else None
df_prepared = pd.read_csv(prepared_path, dtype=str) if prepared_path.exists() else None

try:
    df_enriched = load_enriched_tweets(enriched_path)
except FileNotFoundError:
    st.error(
        "`data/processed/tweets_enriched.csv` introuvable.\n\n"
        "Va d'abord sur la page **Admin** pour lancer le pipeline."
    )
    st.stop()

if df_enriched.empty:
    st.info("Aucun tweet enrichi disponible.")
    st.stop()

stats = compute_detailed_stats(df_raw, df_prepared, df_enriched)
report_text = build_text_report(stats)

# ----------------- SECTION 1 : VOLUME GLOBAL -----------------
st.markdown("<div class='section-title'>📌 Volume global du pipeline</div>", unsafe_allow_html=True)

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown("<div class='kpi-card'>", unsafe_allow_html=True)
    st.markdown("<div class='kpi-label'>Tweets bruts</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='kpi-value'>{stats.get('total_raw', 0)}</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

with c2:
    st.markdown("<div class='kpi-card'>", unsafe_allow_html=True)
    st.markdown("<div class='kpi-label'>Tweets préparés</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='kpi-value'>{stats.get('total_prepared', 0)}</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

with c3:
    st.markdown("<div class='kpi-card'>", unsafe_allow_html=True)
    st.markdown("<div class='kpi-label'>Tweets enrichis</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='kpi-value'>{stats.get('total_enriched', 0)}</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

with c4:
    st.markdown("<div class='kpi-card'>", unsafe_allow_html=True)
    st.markdown("<div class='kpi-label'>Réponses Free (brut)</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='kpi-value'>{stats.get('replies_from_free_raw', 0)}</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("---")

# ----------------- SECTION 2 : FILTRAGE -----------------
st.markdown("<div class='section-title'>🧹 Filtrage et données exclues</div>", unsafe_allow_html=True)

fc1, fc2, fc3, fc4 = st.columns(4)
with fc1:
    st.markdown("<div class='kpi-card'>", unsafe_allow_html=True)
    st.markdown("<div class='kpi-label'>Retenus pour analyse</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='kpi-value'>{stats.get('kept_for_analysis', 'N/A')}</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

with fc2:
    st.markdown("<div class='kpi-card'>", unsafe_allow_html=True)
    st.markdown("<div class='kpi-label'>Écartés au total</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='kpi-value'>{stats.get('dropped_total', 'N/A')}</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

with fc3:
    st.markdown("<div class='kpi-card'>", unsafe_allow_html=True)
    st.markdown("<div class='kpi-label'>Auteurs officiels exclus</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='kpi-value'>{stats.get('dropped_official_author', 'N/A')}</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

with fc4:
    st.markdown("<div class='kpi-card'>", unsafe_allow_html=True)
    st.markdown("<div class='kpi-label'>Retweets exclus</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='kpi-value'>{stats.get('dropped_retweets', 'N/A')}</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("---")

# ----------------- SECTION 3 : INTENTS / PLAINTES / PRIORITÉS -----------------
intent_counts = stats.get("intent_counts")
complaints_by_type = stats.get("complaints_by_type")
complaints_by_priority = stats.get("complaints_by_priority")

tab_intents, tab_complaints, tab_priorities = st.tabs(
    ["🎯 Intents", "🔥 Types de plaintes", "⚠️ Priorités"]
)

with tab_intents:
    st.markdown("<div class='section-title'>Répartition des intentions</div>", unsafe_allow_html=True)
    if intent_counts is not None and not intent_counts.empty:
        df_intent = intent_counts.reset_index()
        df_intent.columns = ["intent", "count"]
        chart_intent = (
            alt.Chart(df_intent)
            .mark_bar()
            .encode(
                x=alt.X("intent:N", sort="-y", title="Intention"),
                y=alt.Y("count:Q", title="Nombre de tweets"),
                tooltip=["intent", "count"],
            )
            .properties(height=320)
        )
        st.altair_chart(chart_intent, use_container_width=True)
    else:
        st.info("Aucune information sur les intentions.")

with tab_complaints:
    st.markdown("<div class='section-title'>Types de plaintes</div>", unsafe_allow_html=True)
    if complaints_by_type is not None and not complaints_by_type.empty:
        df_ct = complaints_by_type.reset_index()
        df_ct.columns = ["complaint_type", "count"]
        chart_ct = (
            alt.Chart(df_ct)
            .mark_bar()
            .encode(
                x=alt.X("complaint_type:N", sort="-y", title="Type de plainte"),
                y=alt.Y("count:Q", title="Nombre"),
                tooltip=["complaint_type", "count"],
            )
            .properties(height=320)
        )
        st.altair_chart(chart_ct, use_container_width=True)
    else:
        st.info("Aucune plainte détectée ou colonne manquante.")

with tab_priorities:
    st.markdown("<div class='section-title'>Priorités des plaintes</div>", unsafe_allow_html=True)
    if complaints_by_priority is not None and not complaints_by_priority.empty:
        df_cp = complaints_by_priority.reset_index()
        df_cp.columns = ["priority", "count"]
        chart_cp = (
            alt.Chart(df_cp)
            .mark_bar()
            .encode(
                x=alt.X("priority:N", sort=["critical", "high", "medium", "low", "none"], title="Priorité"),
                y=alt.Y("count:Q", title="Nombre de plaintes"),
                tooltip=["priority", "count"],
            )
            .properties(height=320)
        )
        st.altair_chart(chart_cp, use_container_width=True)
    else:
        st.info("Aucune donnée sur les priorités.")

st.markdown("---")

# ----------------- SECTION 4 : SENTIMENT / SARCASME / RÉSILIATION -----------------
st.markdown("<div class='section-title'>💬 Sentiment, sarcasme, risque de résiliation</div>", unsafe_allow_html=True)

sentiment_counts = stats.get("sentiment_counts")
col_sent, col_stats = st.columns([2, 1])

with col_sent:
    if sentiment_counts is not None and not sentiment_counts.empty:
        df_sent = sentiment_counts.reset_index()
        df_sent.columns = ["sentiment", "count"]
        chart_sent = (
            alt.Chart(df_sent)
            .mark_bar()
            .encode(
                x=alt.X("sentiment:N", sort="-y", title="Sentiment"),
                y=alt.Y("count:Q", title="Nombre de tweets"),
                tooltip=["sentiment", "count"],
            )
            .properties(height=320)
        )
        st.altair_chart(chart_sent, use_container_width=True)
    else:
        st.info("Aucune donnée de sentiment.")

with col_stats:
    st.markdown("<div class='kpi-card'>", unsafe_allow_html=True)
    st.markdown("<div class='kpi-label'>Tweets sarcastiques détectés</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='kpi-value'>{stats.get('sarcasm_true', 'N/A')}</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='kpi-card' style='margin-top:0.75rem;'>", unsafe_allow_html=True)
    st.markdown("<div class='kpi-label'>Risque de résiliation détecté</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='kpi-value'>{stats.get('resiliation_risk_true', 'N/A')}</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("---")

# ----------------- SECTION 5 : VOLUME DANS LE TEMPS -----------------
st.markdown("<div class='section-title'>⏱️ Volume dans le temps</div>", unsafe_allow_html=True)

df_time = df_enriched.copy()
if "created_at" in df_time.columns:
    df_time["created_at_parsed"] = pd.to_datetime(df_time["created_at"], errors="coerce")
    if is_datetime64_any_dtype(df_time["created_at_parsed"]) and df_time["created_at_parsed"].notna().any():
        df_time["date"] = df_time["created_at_parsed"].dt.date
        daily_counts = (
            df_time.groupby("date")["text_clean"].count().reset_index()
        )
        daily_counts.columns = ["date", "count"]

        chart_time = (
            alt.Chart(daily_counts)
            .mark_line(point=True)
            .encode(
                x=alt.X("date:T", title="Date"),
                y=alt.Y("count:Q", title="Nombre de tweets"),
                tooltip=["date:T", "count:Q"],
            )
            .properties(height=320)
        )
        st.altair_chart(chart_time, use_container_width=True)
    else:
        st.info("Impossible d'exploiter `created_at` pour une analyse temporelle.")
else:
    st.info("Pas de colonne `created_at` dans le fichier enrichi.")

st.markdown("---")

# ----------------- SECTION 6 : RAPPORT -----------------
st.markdown("<div class='section-title'>📄 Rapport complet (texte)</div>", unsafe_allow_html=True)
st.markdown(
    "Ce rapport synthétise toutes les statistiques clés du pipeline (volumes, filtres, intents, plaintes, priorités, sentiment, sarcasme, résiliation)."
)

st.markdown(report_text)

report_bytes = report_text.encode("utf-8")
st.download_button(
    label="💾 Télécharger le rapport (Markdown)",
    data=report_bytes,
    file_name="rapport_sav_free_tweets.md",
    mime="text/markdown",
)
