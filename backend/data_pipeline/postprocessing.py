# backend/data_pipeline/postprocessing.py

from __future__ import annotations

from typing import List

import pandas as pd

PRIORITY_ORDER: List[str] = ["none", "low", "medium", "high", "critical"]


def _bump_priority(current: str, steps: int = 1) -> str:
    if current not in PRIORITY_ORDER:
        current = "none"
    idx = PRIORITY_ORDER.index(current)
    new_idx = min(idx + steps, len(PRIORITY_ORDER) - 1)
    return PRIORITY_ORDER[new_idx]


def apply_llm_nlp_reconciliation(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    df["final_intent"] = df.get("intent", "other")
    df["final_complaint_type"] = df.get("complaint_type", "none")
    df["final_priority"] = df.get("priority", "none")
    df["final_sentiment"] = df.get("sentiment", "neutral")
    df["final_sarcasm"] = df.get("sarcasm", False)

    for idx, row in df.iterrows():
        intent = row.get("intent", "other")
        complaint_type = row.get("complaint_type", "none")
        sentiment = row.get("sentiment", "neutral")
        sarcasm = bool(row.get("sarcasm", False))
        priority = row.get("priority", "none")

        nlp_score = row.get("nlp_sentiment_score", 0)
        nlp_prob_complaint = bool(row.get("nlp_probable_complaint", False))
        nlp_urgency = bool(row.get("nlp_has_urgency", False))
        nlp_resiliation = bool(row.get("nlp_has_resiliation_risk", False))
        nlp_topics = row.get("nlp_topics", "") or ""
        nlp_sarcasm_hint = bool(row.get("nlp_sarcasm_hint", False))

        # 1) Intent final
        final_intent = intent
        if intent != "complaint" and nlp_prob_complaint and nlp_score >= 2:
            final_intent = "complaint"
        if intent == "other" and nlp_score >= 2:
            final_intent = "complaint"

        # 2) Type de plainte final
        final_complaint_type = complaint_type
        if final_intent != "complaint":
            final_complaint_type = "none"
        else:
            if complaint_type in ("none", "other_complaint") and nlp_topics:
                first_topic = nlp_topics.split(",")[0]
                final_complaint_type = first_topic

        # 3) Sarcasme + sentiment
        final_sarcasm = sarcasm or nlp_sarcasm_hint
        final_sentiment = sentiment
        if final_sarcasm and sentiment == "positive":
            final_sentiment = "negative"

        # 4) Priorité finale
        base_priority = priority if priority in PRIORITY_ORDER else "none"
        if final_intent != "complaint":
            final_priority = "none"
        else:
            if nlp_resiliation:
                if base_priority in ("none", "low", "medium"):
                    base_priority = "high"
            if nlp_urgency:
                base_priority = _bump_priority(base_priority, 1)
            if isinstance(nlp_score, (int, float)) and nlp_score >= 3:
                base_priority = _bump_priority(base_priority, 1)
            final_priority = base_priority

        df.at[idx, "final_intent"] = final_intent
        df.at[idx, "final_complaint_type"] = final_complaint_type
        df.at[idx, "final_priority"] = final_priority
        df.at[idx, "final_sentiment"] = final_sentiment
        df.at[idx, "final_sarcasm"] = final_sarcasm

    return df
