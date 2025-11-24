# backend/data_pipeline/cleaning.py

from __future__ import annotations

import re
from typing import List

import pandas as pd

FREE_OFFICIAL_ACCOUNTS = [
    "Freebox",
    "free",
    "Free_1337",
]

# d’autres comptes "institutionnels" éventuellement à exclure plus tard si tu veux
OTHER_KNOWN_ACCOUNTS = [
    "GroupeIliad",
    "UniversFreebox",
]


def normalize_text_basic(text: str) -> str:
    if not isinstance(text, str):
        return ""
    t = text.strip()
    # enlever les URLs
    t = re.sub(r"http\S+|www\.\S+", "", t)
    # normaliser espaces
    t = re.sub(r"\s+", " ", t)
    return t.strip()


def detect_author_type(screen_name: str) -> str:
    if not isinstance(screen_name, str):
        return "customer"
    if screen_name in FREE_OFFICIAL_ACCOUNTS:
        return "official"
    return "customer"


def detect_tweet_type(row: pd.Series) -> str:
    """
    Heuristique simple basée sur les colonnes classiques Twitter.
    """
    # si on a un champ de type RT
    full_text = str(row.get("full_text", "") or "")
    if full_text.startswith("RT "):
        return "retweet"

    # reply si in_reply_to_status_id existe
    if pd.notna(row.get("in_reply_to_status_id")) and str(row.get("in_reply_to_status_id")).strip() != "":
        return "reply"

    # quote si on a un champ quoted_* explicite
    if "is_quote_status" in row and str(row["is_quote_status"]).lower() == "true":
        return "quote"

    return "original"


def is_about_free(text: str) -> bool:
    if not isinstance(text, str):
        return False
    t = text.lower()
    keywords = ["free", "freebox", "@free", "@freebox", "free mobile", "freebox delta", "free fibre", "free fiber"]
    return any(kw in t for kw in keywords)


def preprocess_tweets(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ajoute les colonnes de base :
    - text_clean
    - author_type
    - tweet_type
    - is_about_free
    - keep_for_analysis
    """
    df = df.copy()

    # Texte nettoyé
    text_col = "full_text" if "full_text" in df.columns else "text"
    df["text_clean"] = df[text_col].apply(normalize_text_basic)

    # auteur
    screen_col = "screen_name" if "screen_name" in df.columns else "user_screen_name"
    df["author_type"] = df[screen_col].apply(detect_author_type)

    # type de tweet
    df["tweet_type"] = df.apply(detect_tweet_type, axis=1)

    # parle de free ?
    df["is_about_free"] = df["text_clean"].apply(is_about_free)

    # logique keep_for_analysis :
    # - on garde seulement les clients (pas les officiels Free/Freebox)
    # - on exclut les retweets
    # - on garde seulement ceux qui parlent de Free
    df["keep_for_analysis"] = (
        (df["author_type"] == "customer")
        & (df["tweet_type"].isin(["original", "reply", "quote"]))
        & (df["is_about_free"] == True)
    )

    return df
