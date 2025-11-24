# app_service/pages/2_Manager.py

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

# ----------------- CONFIG PAGE -----------------
st.set_page_config(page_title="SAV Free - Manager", page_icon="📊", layout="wide")
require_auth(["manager", "admin"])

# ----------------- STYLE -----------------
st.markdown(
    """
    <style>
    .kpi-card {
        padding: 0.8rem 1rem;
        border-radius: 0.75rem;
        background-color: #0b1120;
        border: 1px solid #1e293b;
    }
    .kpi-label {
        font-size: 0.85rem;
        color: #9ca3af;
    }
    .kpi-value {
        font-size: 1.4rem;
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

st.markdown("## 📊 Espace Manager SAV")

st.write(
    "Le manager dispose ici d'une **vision globale** du service client vu depuis Twitter : "
    "volumes, intentions, plaintes prioritaires, suggestions, feedbacks positifs et tendances."
)

# ----------------- CHARGEMENT -----------------
try:
    df = load_enriched_tweets()
except FileNotFoundError:
    st.error(
        "Le fichier `data/processed/tweets_enriched.csv` est introuvable.\n\n"
        "Va d'abord sur la page **Admin** pour lancer le pipeline."
    )
    st.stop()

if df.empty:
    st.info("Aucune donnée disponible.")
    st.stop()

for col, default in [
    ("final_intent", "other"),
    ("final_complaint_type", "none"),
    ("final_priority", "none"),
    ("final_sentiment", "neutral"),
    ("final_sarcasm", "False"),
    ("nlp_has_resiliation_risk", "False"),
]:
    if col not in df.columns:
        df[col] = default

if "created_at" in df.columns:
    df["created_at_parsed"] = pd.to_datetime(df["created_at"], errors="coerce")
else:
    df["created_at_parsed"] = pd.NaT

# ----------------- FILTRES -----------------
st.sidebar.header("🧰 Filtres Manager")

has_valid_dates = df["created_at_parsed"].notna().any() and is_datetime64_any_dtype(
    df["created_at_parsed"]
)

if has_valid_dates:
    min_date = df["created_at_parsed"].min().date()
    max_date = df["created_at_parsed"].max().date()
    start_date, end_date = st.sidebar.date_input(
        "Période d'analyse",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )
else:
    start_date, end_date = None, None

intent_values = sorted(df["final_intent"].dropna().unique().tolist())
selected_intents = st.sidebar.multiselect(
    "Intentions à inclure",
    intent_values,
    default=intent_values,
)

complaint_types = sorted(df["final_complaint_type"].dropna().unique().tolist())
selected_complaint_types = st.sidebar.multiselect(
    "Types de plainte (pour les plaintes uniquement)",
    complaint_types,
    default=complaint_types,
)

priority_values_default = ["critical", "high", "medium", "low", "none"]
priority_candidates = df["final_priority"].dropna().unique().tolist()
priority_values = [p for p in priority_values_default if p in priority_candidates] or priority_candidates
selected_priorities = st.sidebar.multiselect(
    "Priorités (pour les plaintes)",
    priority_values,
    default=priority_values,
)

sentiment_values = sorted(df["final_sentiment"].dropna().unique().tolist())
selected_sentiments = st.sidebar.multiselect(
    "Sentiments à inclure",
    sentiment_values,
    default=sentiment_values,
)

# ----------------- APPLICATION FILTRES -----------------
filtered = df.copy()

if start_date and end_date and has_valid_dates:
    filtered["created_at_parsed"] = pd.to_datetime(
        filtered["created_at_parsed"], errors="coerce"
    )
    date_mask = filtered["created_at_parsed"].notna()
    date_mask &= filtered["created_at_parsed"].dt.date >= start_date
    date_mask &= filtered["created_at_parsed"].dt.date <= end_date
    filtered = filtered[date_mask]

if selected_intents:
    filtered = filtered[filtered["final_intent"].isin(selected_intents)]

if selected_sentiments:
    filtered = filtered[filtered["final_sentiment"].isin(selected_sentiments)]

complaints = filtered[filtered["final_intent"] == "complaint"].copy()
if selected_complaint_types:
    complaints = complaints[complaints["final_complaint_type"].isin(selected_complaint_types)]
if selected_priorities:
    complaints = complaints[complaints["final_priority"].isin(selected_priorities)]

# ----------------- KPIs GLOBAUX -----------------
st.markdown("<div class='section-title'>📌 Indicateurs globaux</div>", unsafe_allow_html=True)

total_tweets = len(filtered)
nb_complaints = int((filtered["final_intent"] == "complaint").sum())
nb_suggestions = int((filtered["final_intent"] == "suggestion").sum())
nb_thanks = int((filtered["final_intent"].isin(["thanks", "praise"])).sum())
nb_high_crit = int(
    complaints["final_priority"].isin(["high", "critical"]).sum()
) if not complaints.empty else 0
nb_resiliation_risk = int(
    filtered["nlp_has_resiliation_risk"]
    .astype(str)
    .str.lower()
    .isin(["true", "1"])
    .sum()
)

sentiment_counts = filtered["final_sentiment"].value_counts()
nb_negative = int(sentiment_counts.get("negative", 0))
pct_negative = (nb_negative / total_tweets * 100) if total_tweets > 0 else 0

kc1, kc2, kc3, kc4 = st.columns(4)
with kc1:
    st.markdown("<div class='kpi-card'>", unsafe_allow_html=True)
    st.markdown("<div class='kpi-label'>Tweets analysés</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='kpi-value'>{total_tweets}</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

with kc2:
    st.markdown("<div class='kpi-card'>", unsafe_allow_html=True)
    st.markdown("<div class='kpi-label'>Plaintes</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='kpi-value'>{nb_complaints}</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

with kc3:
    st.markdown("<div class='kpi-card'>", unsafe_allow_html=True)
    st.markdown("<div class='kpi-label'>Plaintes high/critical</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='kpi-value'>{nb_high_crit}</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

with kc4:
    st.markdown("<div class='kpi-card'>", unsafe_allow_html=True)
    st.markdown("<div class='kpi-label'>Risque de résiliation détecté</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='kpi-value'>{nb_resiliation_risk}</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

kc5, kc6 = st.columns(2)
with kc5:
    st.markdown("<div class='kpi-card'>", unsafe_allow_html=True)
    st.markdown("<div class='kpi-label'>Suggestions</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='kpi-value'>{nb_suggestions}</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

with kc6:
    st.markdown("<div class='kpi-card'>", unsafe_allow_html=True)
    st.markdown("<div class='kpi-label'>Part de tweets négatifs</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='kpi-value'>{pct_negative:.1f}%</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("---")

# ----------------- INTENTS -----------------
st.markdown("<div class='section-title'>🎯 Répartition des intentions</div>", unsafe_allow_html=True)
intent_counts = filtered["final_intent"].value_counts().sort_values(ascending=False)
if not intent_counts.empty:
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
    st.info("Aucune donnée d'intention.")

st.markdown("---")

# ----------------- FOCUS PLAINTES -----------------
st.markdown("<div class='section-title'>🔥 Focus sur les plaintes</div>", unsafe_allow_html=True)

tab_ct, tab_cp, tab_table = st.tabs(
    ["Types de plaintes", "Priorités", "Tableau synthétique"]
)

if complaints.empty:
    for tb in (tab_ct, tab_cp, tab_table):
        with tb:
            st.info("Aucune plainte ne correspond aux filtres actuels.")
else:
    with tab_ct:
        st.write("Répartition des plaintes par type.")
        complaint_type_counts = complaints["final_complaint_type"].value_counts().sort_values(ascending=False)
        df_ct = complaint_type_counts.reset_index()
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

    with tab_cp:
        st.write("Répartition des priorités des plaintes.")
        priority_counts = complaints["final_priority"].value_counts()
        priority_counts = priority_counts.reindex(
            ["critical", "high", "medium", "low", "none"]
        ).dropna()
        df_cp = priority_counts.reset_index()
        df_cp.columns = ["priority", "count"]
        chart_cp = (
            alt.Chart(df_cp)
            .mark_bar()
            .encode(
                x=alt.X("priority:N", sort=["critical", "high", "medium", "low", "none"], title="Priorité"),
                y=alt.Y("count:Q", title="Nombre"),
                tooltip=["priority", "count"],
            )
            .properties(height=320)
        )
        st.altair_chart(chart_cp, use_container_width=True)

    with tab_table:
        st.write("Synthèse par type de plainte et priorité.")
        pivot = complaints.pivot_table(
            index="final_complaint_type",
            columns="final_priority",
            values="text_clean",
            aggfunc="count",
            fill_value=0,
        )
        st.dataframe(pivot, use_container_width=True)

st.markdown("---")

# ----------------- SUGGESTIONS & FEEDBACK POSITIF -----------------
st.markdown("<div class='section-title'>💡 Suggestions et feedbacks positifs</div>", unsafe_allow_html=True)

suggestions = filtered[filtered["final_intent"] == "suggestion"].copy()
positive_feedback = filtered[
    filtered["final_intent"].isin(["thanks", "praise"])
].copy()

col_s1, col_s2 = st.columns(2)

with col_s1:
    st.write("Suggestions récentes (extraits).")
    if suggestions.empty:
        st.info("Aucune suggestion dans le périmètre filtré.")
    else:
        cols = ["created_at", "screen_name", "text_clean"]
        cols = [c for c in cols if c in suggestions.columns]
        st.dataframe(suggestions[cols].head(20), use_container_width=True)

with col_s2:
    st.write("Tweets positifs (remerciements / compliments).")
    if positive_feedback.empty:
        st.info("Aucun feedback positif dans le périmètre filtré.")
    else:
        cols = ["created_at", "screen_name", "text_clean"]
        cols = [c for c in cols if c in positive_feedback.columns]
        st.dataframe(positive_feedback[cols].head(20), use_container_width=True)

st.markdown("---")

# ----------------- TENDANCES -----------------
st.markdown("<div class='section-title'>⏱️ Tendances dans le temps</div>", unsafe_allow_html=True)

if has_valid_dates:
    temp = filtered.copy()
    temp["created_at_parsed"] = pd.to_datetime(
        temp["created_at_parsed"], errors="coerce"
    )
    temp = temp[temp["created_at_parsed"].notna()]

    if not temp.empty:
        temp["date"] = temp["created_at_parsed"].dt.date

        daily_counts = (
            temp.groupby("date")["text_clean"].count().reset_index()
        )
        daily_counts.columns = ["date", "count"]

        chart_daily = (
            alt.Chart(daily_counts)
            .mark_line(point=True)
            .encode(
                x=alt.X("date:T", title="Date"),
                y=alt.Y("count:Q", title="Nombre de tweets"),
                tooltip=["date:T", "count:Q"],
            )
            .properties(height=320)
        )

        temp["is_negative"] = temp["final_sentiment"] == "negative"
        daily_neg = (
            temp.groupby("date")["is_negative"].mean().reset_index()
        )
        daily_neg["pct_negative"] = daily_neg["is_negative"] * 100

        chart_neg = (
            alt.Chart(daily_neg)
            .mark_line(point=True)
            .encode(
                x=alt.X("date:T", title="Date"),
                y=alt.Y("pct_negative:Q", title="% tweets négatifs"),
                tooltip=["date:T", "pct_negative:Q"],
            )
            .properties(height=320)
        )

        ctime1, ctime2 = st.columns(2)
        with ctime1:
            st.write("Volume de tweets par jour.")
            st.altair_chart(chart_daily, use_container_width=True)
        with ctime2:
            st.write("Pourcentage de tweets négatifs par jour.")
            st.altair_chart(chart_neg, use_container_width=True)
    else:
        st.info("Impossible de tracer les tendances temporelles avec les filtres actuels.")
else:
    st.info("Pas de colonne de date exploitable pour une analyse temporelle (`created_at`).")
