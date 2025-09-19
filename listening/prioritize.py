from datetime import datetime, timedelta
import re
import os

# Liste de mots-clés par gravité
CRITICAL_KEYWORDS = ["urgent", "aucune connexion", "plus d’internet", "en panne", "bloqué", "bug", "rien ne marche"]
THREAT_KEYWORDS = ["inadmissible", "je vais résilier", "honteux", "inacceptable"]
SPAM_PATTERN = r"^[#\s🫠🤡🔥🌈💀😂❤️]*$"

# Seuils pour surcharge
MAX_PENDING_REQUESTS = 100  # au-delà = surcharge

def detect_critical_keywords(text: str, keywords: list[str]) -> bool:
    return any(kw.lower() in text.lower() for kw in keywords)

def is_spam(text: str) -> bool:
    return re.fullmatch(SPAM_PATTERN, text.strip()) is not None

def calculate_priority(message: dict, pending_volume: int = 0) -> str:
    """
    message = {
        'text': str,
        'sentiment': 'positif' | 'neutre' | 'négatif',
        'category': str,
        'created_at': datetime
    }
    """
    text = message.get("text", "")
    sentiment = message.get("sentiment")
    category = message.get("category")
    created_at = message.get("created_at", datetime.now())

    # Cas 1 : Message vide ou spam
    if not text.strip() or is_spam(text):
        return "aucune"

    # Cas 2 : Problème technique urgent
    if category == "problème technique":
        if detect_critical_keywords(text, CRITICAL_KEYWORDS):
            if datetime.now() - created_at > timedelta(hours=1):
                return "critique"
            return "élevée"

    # Cas 3 : Plainte émotionnelle
    if category == "plainte" and sentiment == "négatif":
        if detect_critical_keywords(text, THREAT_KEYWORDS):
            return "élevée"

    # Cas 4 : Suggestion ou remerciement
    if category == "suggestion" or sentiment == "positif":
        return "moyenne"

    # Cas 5 : Question simple ou neutre
    if category in ["question", "information"] or sentiment == "neutre":
        return "faible"

    # Cas 6 : Langue inconnue ou inclassifiable
    if category == "non classifiable":
        return "aucune"

    # Cas par défaut
    priority = "faible"

    # Cas 7 : Surcharge → Priorisation dynamique
    if pending_volume > MAX_PENDING_REQUESTS:
        if priority in ["faible", "moyenne"]:
            return "différée"
        return priority

    return priority



# Tests unitaires
from datetime import datetime, timedelta

message = {
    "text": "Plus d’internet depuis 4h, c’est inadmissible !!",
    "sentiment": "négatif",
    "category": "problème technique",
    "created_at": datetime.now() - timedelta(hours=4)
}

priority = calculate_priority(message, pending_volume=110)
print(f"Priorité : {priority}")  # ➜ Priorité : critique.
