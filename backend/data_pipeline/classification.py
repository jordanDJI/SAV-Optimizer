# backend/data_pipeline/classification.py

from __future__ import annotations

import time
from typing import Optional

import pandas as pd

from backend.data_pipeline.llm_client import get_llm_client


def classify_single_tweet(text: str) -> dict:
    client = get_llm_client()
    return client.classify_tweet(text)


def classify_tweets_df(
    df: pd.DataFrame,
    text_col: str = "text_clean",
    keep_col: str = "keep_for_analysis",
    sleep_between_calls: Optional[float] = 0.0,
) -> pd.DataFrame:
    df = df.copy()

    # colonnes de sortie
    df["intent"] = "unknown"
    df["complaint_type"] = "none"
    df["sentiment"] = "neutral"
    df["sarcasm"] = False
    df["priority"] = "none"
    df["llm_explanation"] = ""

    mask = df[keep_col] == True
    idx_to_process = df[mask].index

    for idx in idx_to_process:
        text = df.at[idx, text_col]
        try:
            result = classify_single_tweet(text)
            df.at[idx, "intent"] = result.get("intent", "other")
            df.at[idx, "complaint_type"] = result.get("complaint_type", "none")
            df.at[idx, "sentiment"] = result.get("sentiment", "neutral")
            df.at[idx, "sarcasm"] = result.get("sarcasm", False)
            df.at[idx, "priority"] = result.get("priority", "none")
            df.at[idx, "llm_explanation"] = result.get("explanation", "")
        except Exception as e:
            df.at[idx, "intent"] = "other"
            df.at[idx, "complaint_type"] = "none"
            df.at[idx, "sentiment"] = "neutral"
            df.at[idx, "sarcasm"] = False
            df.at[idx, "priority"] = "none"
            df.at[idx, "llm_explanation"] = f"Erreur LLM : {e}"

        if sleep_between_calls and sleep_between_calls > 0:
            time.sleep(sleep_between_calls)

    return df
