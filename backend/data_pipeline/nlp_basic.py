# backend/data_pipeline/nlp_basic.py

from __future__ import annotations

import re
import unicodedata
from typing import List

import pandas as pd

NEGATIVE_STRONG = [
    "scandale", "honte", "honteux", "nul", "nulle", "lamentable",
    "inadmissible", "inacceptable", "catastrophique", "merde",
    "arnaque", "vol", "voleur",
]

NEGATIVE_WEAK = [
    "problème", "probleme", "bug", "lent", "lente", "déçu", "decu",
    "décevant", "marche pas", "ne marche pas", "ne fonctionne pas",
    "fonctionne pas", "panne", "coupure", "instable",
]

PRAISE_KEYWORDS = [
    "merci", "bravo", "top", "super", "génial", "genial", "parfait", "au top", "nickel",
]

COMPLAINT_KEYWORDS = [
    "panne", "coupure", "incident", "bug", "debit", "débit", "connexion", "connection",
    "réseau", "reseau", "facture", "prélèvement", "prelevement", "surfacturation",
    "remboursement", "service client", "sav", "attente", "retard",
]

URGENCY_KEYWORDS = [
    "urgent", "urgence", "immédiatement", "immediatement", "tout de suite", "vite", "rapidement",
]

RESILIATION_KEYWORDS = [
    "résilier", "resilier", "résiliation", "resiliation", "me barre", "je me barre",
    "partir chez", "changer d'opérateur", "changer d’operateur",
]

TOPIC_FIBER = ["fibre", "ftth", "pon", "ont"]
TOPIC_MOBILE = ["4g", "5g", "mobile", "forfait", "sim", "carte sim"]
TOPIC_NETWORK = ["débit", "debit", "ping", "latence", "lag", "reseau", "réseau"]
TOPIC_TV = ["tv", "télé", "tele", "chaine", "chaîne", "replay", "vod"]
TOPIC_BILLING = ["facture", "prélèvement", "prelevement", "paiement", "tarif", "prix"]
TOPIC_CUSTOMER_SERVICE = ["service client", "sav", "hotline", "support", "conseiller"]
TOPIC_EQUIPMENT = ["box", "freebox", "modem", "routeur", "router", "décodeur", "decodeur"]


def normalize_for_lexical(text: str) -> str:
    if not isinstance(text, str):
        return ""
    t = text.lower()
    t = "".join(
        c for c in unicodedata.normalize("NFD", t)
        if unicodedata.category(c) != "Mn"
    )
    t = re.sub(r"\s+", " ", t).strip()
    return t


def contains_any(text: str, keywords: List[str]) -> bool:
    t = normalize_for_lexical(text)
    return any(kw in t for kw in keywords)


def basic_sentiment_score(text: str) -> int:
    t = normalize_for_lexical(text)
    score = 0
    for kw in NEGATIVE_STRONG:
        if kw in t:
            score += 2
    for kw in NEGATIVE_WEAK:
        if kw in t:
            score += 1
    for kw in PRAISE_KEYWORDS:
        if kw in t:
            score -= 1
    return score


def detect_topics(text: str) -> list[str]:
    t = normalize_for_lexical(text)
    topics: list[str] = []
    if any(kw in t for kw in TOPIC_FIBER):
        topics.append("fiber_issue")
    if any(kw in t for kw in TOPIC_MOBILE):
        topics.append("mobile_issue")
    if any(kw in t for kw in TOPIC_NETWORK):
        topics.append("network_issue")
    if any(kw in t for kw in TOPIC_TV):
        topics.append("tv_service_issue")
    if any(kw in t for kw in TOPIC_BILLING):
        topics.append("billing_issue")
    if any(kw in t for kw in TOPIC_CUSTOMER_SERVICE):
        topics.append("customer_service_issue")
    if any(kw in t for kw in TOPIC_EQUIPMENT):
        topics.append("equipment_issue")
    return topics


def basic_is_probable_complaint(text: str) -> bool:
    t = normalize_for_lexical(text)
    if contains_any(t, COMPLAINT_KEYWORDS):
        return True
    if basic_sentiment_score(t) >= 2:
        return True
    if "ne marche pas" in t or "marche pas" in t or "ne fonctionne pas" in t:
        return True
    return False


def basic_has_urgency(text: str) -> bool:
    return contains_any(text, URGENCY_KEYWORDS)


def basic_has_resiliation_risk(text: str) -> bool:
    return contains_any(text, RESILIATION_KEYWORDS)


def basic_sarcasm_hint(text: str) -> bool:
    t = normalize_for_lexical(text)
    if "merci" in t and ("..." in t or contains_any(t, NEGATIVE_STRONG)):
        return True
    if "bravo" in t and contains_any(t, NEGATIVE_STRONG):
        return True
    return False


def enrich_with_basic_nlp(df: pd.DataFrame, text_col: str = "text_clean") -> pd.DataFrame:
    if text_col not in df.columns:
        raise ValueError(f"Colonne texte '{text_col}' absente du DataFrame")

    df = df.copy()
    df["nlp_sentiment_score"] = df[text_col].apply(basic_sentiment_score)
    df["nlp_probable_complaint"] = df[text_col].apply(basic_is_probable_complaint)
    df["nlp_has_urgency"] = df[text_col].apply(basic_has_urgency)
    df["nlp_has_resiliation_risk"] = df[text_col].apply(basic_has_resiliation_risk)
    df["nlp_sarcasm_hint"] = df[text_col].apply(basic_sarcasm_hint)

    df["nlp_topics_list"] = df[text_col].apply(detect_topics)
    df["nlp_topics"] = df["nlp_topics_list"].apply(lambda lst: ",".join(lst) if lst else "")

    return df
