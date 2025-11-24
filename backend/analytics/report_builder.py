# backend/analytics/report_builder.py

from __future__ import annotations

from typing import Optional, Dict, Any
import pandas as pd

# mêmes comptes que dans ton cleaning
OFFICIAL_ACCOUNTS = {"Freebox", "free", "Free_1337"}


def _safe_len(df: Optional[pd.DataFrame]) -> int:
    return int(len(df)) if df is not None else 0


def compute_detailed_stats(
    df_raw: Optional[pd.DataFrame] = None,
    df_prepared: Optional[pd.DataFrame] = None,
    df_enriched: Optional[pd.DataFrame] = None,
) -> Dict[str, Any]:
    """
    Calcule un maximum de stats pour l'analyste / admin.
    On est robuste aux colonnes manquantes.
    """

    stats: Dict[str, Any] = {}

    # ----------------- 1) VOL GLOBAL -----------------
    stats["total_raw"] = _safe_len(df_raw)
    stats["total_prepared"] = _safe_len(df_prepared)
    stats["total_enriched"] = _safe_len(df_enriched)

    # ----------------- 2) TWEETS FREE (comptes officiels) -----------------
    def count_official(df: Optional[pd.DataFrame]) -> int:
        if df is None or "screen_name" not in df.columns:
            return 0
        return int(df["screen_name"].isin(OFFICIAL_ACCOUNTS).sum())

    stats["tweets_from_free_raw"] = count_official(df_raw)
    stats["tweets_from_free_prepared"] = count_official(df_prepared)
    stats["tweets_from_free_enriched"] = count_official(df_enriched)

    def count_replies_from_free(df: Optional[pd.DataFrame]) -> int:
        if df is None:
            return 0
        if "screen_name" not in df.columns or "in_reply_to" not in df.columns:
            return 0
        mask_official = df["screen_name"].isin(OFFICIAL_ACCOUNTS)
        mask_reply = df["in_reply_to"].astype(str).str.strip().ne("")
        return int((mask_official & mask_reply).sum())

    stats["replies_from_free_raw"] = count_replies_from_free(df_raw)

    # ----------------- 3) TYPE DE TWEET / RT / QUOTES / REPLIES -----------------
    def count_retweets(df_r: Optional[pd.DataFrame], df_p: Optional[pd.DataFrame]) -> int:
        if df_p is not None and "tweet_type" in df_p.columns:
            return int((df_p["tweet_type"] == "retweet").sum())
        if df_r is not None and "retweeted_status" in df_r.columns:
            return int(df_r["retweeted_status"].astype(str).str.strip().ne("").sum())
        return 0

    def count_replies(df_r: Optional[pd.DataFrame], df_p: Optional[pd.DataFrame]) -> int:
        if df_p is not None and "tweet_type" in df_p.columns:
            return int((df_p["tweet_type"] == "reply").sum())
        if df_r is not None and "in_reply_to" in df_r.columns:
            return int(df_r["in_reply_to"].astype(str).str.strip().ne("").sum())
        return 0

    def count_quotes(df_r: Optional[pd.DataFrame], df_p: Optional[pd.DataFrame]) -> int:
        if df_p is not None and "tweet_type" in df_p.columns:
            return int((df_p["tweet_type"] == "quote").sum())
        if df_r is not None and "quoted_status" in df_r.columns:
            return int(df_r["quoted_status"].astype(str).str.strip().ne("").sum())
        return 0

    stats["retweets_total"] = count_retweets(df_raw, df_prepared)
    stats["replies_total"] = count_replies(df_raw, df_prepared)
    stats["quotes_total"] = count_quotes(df_raw, df_prepared)

    # ----------------- 4) FILTRAGES (données "supprimées") -----------------
    # Sur df_prepared : keep_for_analysis, author_type, tweet_type, is_about_free
    if df_prepared is not None:
        total_p = len(df_prepared)
        if "keep_for_analysis" in df_prepared.columns:
            s = df_prepared["keep_for_analysis"].astype(str).str.strip().str.lower()
            keep_bool = s.isin(["true", "1", "yes", "y"])
            stats["kept_for_analysis"] = int(keep_bool.sum())
            stats["dropped_total"] = int(total_p - keep_bool.sum())
        else:
            stats["kept_for_analysis"] = None
            stats["dropped_total"] = None

        # raisons principales si colonnes présentes
        if "author_type" in df_prepared.columns:
            stats["dropped_official_author"] = int(
                (df_prepared["author_type"] == "official").sum()
            )
        else:
            stats["dropped_official_author"] = None

        if "tweet_type" in df_prepared.columns:
            stats["dropped_retweets"] = int(
                (df_prepared["tweet_type"] == "retweet").sum()
            )
        else:
            stats["dropped_retweets"] = None

        if "is_about_free" in df_prepared.columns:
            s2 = df_prepared["is_about_free"].astype(str).str.strip().str.lower()
            about_bool = s2.isin(["true", "1", "yes", "y"])
            stats["not_about_free"] = int((~about_bool).sum())
        else:
            stats["not_about_free"] = None
    else:
        stats["kept_for_analysis"] = None
        stats["dropped_total"] = None
        stats["dropped_official_author"] = None
        stats["dropped_retweets"] = None
        stats["not_about_free"] = None

    # ----------------- 5) ANALYSE LLM / FINAL (df_enriched) -----------------
    if df_enriched is not None:
        # intent
        if "final_intent" in df_enriched.columns:
            stats["intent_counts"] = df_enriched["final_intent"].value_counts()
        else:
            stats["intent_counts"] = pd.Series(dtype=int)

        # plaintes uniquement
        if (
            "final_intent" in df_enriched.columns
            and "final_complaint_type" in df_enriched.columns
        ):
            complaints = df_enriched[df_enriched["final_intent"] == "complaint"].copy()
            stats["complaints_by_type"] = complaints[
                "final_complaint_type"
            ].value_counts()
            if "final_priority" in complaints.columns:
                stats["complaints_by_priority"] = complaints["final_priority"].value_counts()
            else:
                stats["complaints_by_priority"] = pd.Series(dtype=int)
        else:
            stats["complaints_by_type"] = pd.Series(dtype=int)
            stats["complaints_by_priority"] = pd.Series(dtype=int)

        # sentiment
        if "final_sentiment" in df_enriched.columns:
            stats["sentiment_counts"] = df_enriched["final_sentiment"].value_counts()
        else:
            stats["sentiment_counts"] = pd.Series(dtype=int)

        # sarcasme
        if "final_sarcasm" in df_enriched.columns:
            s_sarc = df_enriched["final_sarcasm"].astype(str).str.strip().str.lower()
            stats["sarcasm_true"] = int(s_sarc.isin(["true", "1"]).sum())
        else:
            stats["sarcasm_true"] = None

        # risque résiliation
        if "nlp_has_resiliation_risk" in df_enriched.columns:
            s_res = (
                df_enriched["nlp_has_resiliation_risk"]
                .astype(str)
                .str.strip()
                .str.lower()
            )
            stats["resiliation_risk_true"] = int(s_res.isin(["true", "1"]).sum())
        else:
            stats["resiliation_risk_true"] = None
    else:
        stats["intent_counts"] = pd.Series(dtype=int)
        stats["complaints_by_type"] = pd.Series(dtype=int)
        stats["complaints_by_priority"] = pd.Series(dtype=int)
        stats["sentiment_counts"] = pd.Series(dtype=int)
        stats["sarcasm_true"] = None
        stats["resiliation_risk_true"] = None

    return stats


def build_text_report(stats: Dict[str, Any]) -> str:
    """
    Construit un rapport texte (Markdown simple) à partir des stats.
    """

    lines = []
    lines.append("# Rapport d'analyse SAV Free (Tweets)")
    lines.append("")

    # Section 1
    lines.append("## 1. Volume global")
    lines.append(f"- Tweets bruts (CSV raw) : **{stats.get('total_raw', 0)}**")
    lines.append(f"- Tweets après préparation : **{stats.get('total_prepared', 0)}**")
    lines.append(f"- Tweets enrichis (NLP + LLM) : **{stats.get('total_enriched', 0)}**")
    lines.append("")

    # Section 2
    lines.append("## 2. Activité des comptes Free (officiels)")
    lines.append(
        f"- Tweets provenant de comptes Free (ensemble brut) : **{stats.get('tweets_from_free_raw', 0)}**"
    )
    lines.append(
        f"- Réponses de comptes Free à des clients (ensemble brut) : **{stats.get('replies_from_free_raw', 0)}**"
    )
    lines.append("")

    # Section 3
    lines.append("## 3. Structure du flux Twitter")
    lines.append(f"- Nombre de retweets : **{stats.get('retweets_total', 0)}**")
    lines.append(f"- Nombre de réponses : **{stats.get('replies_total', 0)}**")
    lines.append(f"- Nombre de citations (quotes) : **{stats.get('quotes_total', 0)}**")
    lines.append("")

    # Section 4
    lines.append("## 4. Filtrage et données exclues")
    lines.append(f"- Tweets retenus pour analyse (keep_for_analysis=True) : **{stats.get('kept_for_analysis', 'N/A')}**")
    lines.append(f"- Tweets écartés au total : **{stats.get('dropped_total', 'N/A')}**")
    lines.append(
        f"- Dont tweets écartés car auteur officiel (Free/Freebox) : **{stats.get('dropped_official_author', 'N/A')}**"
    )
    lines.append(
        f"- Dont retweets écartés : **{stats.get('dropped_retweets', 'N/A')}**"
    )
    lines.append(
        f"- Dont tweets ne parlant pas de Free : **{stats.get('not_about_free', 'N/A')}**"
    )
    lines.append("")

    # Section 5
    lines.append("## 5. Résultats NLP + LLM (intents, plaintes, priorités)")
    intent_counts = stats.get("intent_counts", None)
    if intent_counts is not None and not intent_counts.empty:
        lines.append("### 5.1 Répartition des intentions (final_intent)")
        for intent, count in intent_counts.items():
            lines.append(f"- {intent} : **{int(count)}**")
        lines.append("")

    complaints_by_type = stats.get("complaints_by_type", None)
    if complaints_by_type is not None and not complaints_by_type.empty:
        lines.append("### 5.2 Types de plaintes (final_complaint_type)")
        for t, count in complaints_by_type.items():
            lines.append(f"- {t} : **{int(count)}**")
        lines.append("")

    complaints_by_priority = stats.get("complaints_by_priority", None)
    if complaints_by_priority is not None and not complaints_by_priority.empty:
        lines.append("### 5.3 Priorités des plaintes (final_priority)")
        for p, count in complaints_by_priority.items():
            lines.append(f"- {p} : **{int(count)}**")
        lines.append("")

    # Section 6
    lines.append("## 6. Sentiment, sarcasme et risque de résiliation")
    sentiment_counts = stats.get("sentiment_counts", None)
    if sentiment_counts is not None and not sentiment_counts.empty:
        lines.append("### 6.1 Répartition des sentiments (final_sentiment)")
        for s, count in sentiment_counts.items():
            lines.append(f"- {s} : **{int(count)}**")
        lines.append("")

    lines.append(
        f"- Tweets avec sarcasme détecté : **{stats.get('sarcasm_true', 'N/A')}**"
    )
    lines.append(
        f"- Tweets avec risque de résiliation détecté : **{stats.get('resiliation_risk_true', 'N/A')}**"
    )
    lines.append("")

    lines.append("Rapport généré automatiquement à partir des données `tweets.csv`, `tweets_prepared.csv` et `tweets_enriched.csv`.")

    return "\n".join(lines)
