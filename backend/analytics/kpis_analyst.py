# backend/analytics/kpis_analyst.py

from __future__ import annotations

import pandas as pd


def global_counts(df: pd.DataFrame) -> dict:
    """
    KPIs globaux de base.
    """
    total = len(df)

    # On ne se complique pas la vie avec keep_for_analysis ici
    if "final_intent" in df.columns:
        nb_complaints = int((df["final_intent"] == "complaint").sum())
    else:
        nb_complaints = 0

    return {
        "total_tweets": total,
        "kept_for_analysis": None,  # on peut mettre None ou 0 si tu préfères
        "complaints_final": nb_complaints,
    }


def breakdown_by_intent(df: pd.DataFrame) -> pd.Series:
    if "final_intent" not in df.columns:
        return pd.Series(dtype=int)
    return df["final_intent"].value_counts()


def breakdown_complaints_by_type(df: pd.DataFrame) -> pd.Series:
    if "final_intent" not in df.columns or "final_complaint_type" not in df.columns:
        return pd.Series(dtype=int)
    mask = df["final_intent"] == "complaint"
    return df.loc[mask, "final_complaint_type"].value_counts()


def breakdown_complaints_by_priority(df: pd.DataFrame) -> pd.Series:
    if "final_intent" not in df.columns or "final_priority" not in df.columns:
        return pd.Series(dtype=int)
    mask = df["final_intent"] == "complaint"
    return df.loc[mask, "final_priority"].value_counts()


def complaint_matrix_intent_type(df: pd.DataFrame) -> pd.DataFrame:
    if "final_intent" not in df.columns or "final_complaint_type" not in df.columns:
        return pd.DataFrame()

    pivot = df.pivot_table(
        index="final_intent",
        columns="final_complaint_type",
        values="text_clean",
        aggfunc="count",
        fill_value=0,
    )
    return pivot


def compute_kpis(df: pd.DataFrame) -> dict:
    return {
        "global_counts": global_counts(df),
        "by_intent": breakdown_by_intent(df),
        "complaints_by_type": breakdown_complaints_by_type(df),
        "complaints_by_priority": breakdown_complaints_by_priority(df),
        "complaint_matrix": complaint_matrix_intent_type(df),
    }
