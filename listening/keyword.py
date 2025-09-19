# keywords.py

from typing import List, Dict
import re

# Dictionnaire multilingue de mots-clés par catégorie
KEYWORDS_DB: Dict[str, Dict[str, List[str]]] = {
    "fr": {
        "technique": ["panne", "bug", "erreur", "connexion", "bloqué", "plus d’internet", "ne marche pas"],
        "plainte": ["inadmissible", "nul", "je vais résilier", "inacceptable", "catastrophique", "marre", "colère"],
        "positif": ["merci", "top", "satisfait", "bravo", "bien joué", "super service"],
        "demande": ["comment", "où", "quand", "je veux", "je cherche", "je souhaite"],
        "spam": ["🔥", "😂", "lol", "#troll"]
    },
    "en": {
        "technique": ["no internet", "connection lost", "doesn’t work", "down", "broken", "bug"],
        "plainte": ["cancel", "not happy", "angry", "unacceptable", "ridiculous", "frustrated"],
        "positif": ["thank you", "great", "awesome", "good job", "nice service"],
        "demande": ["how", "where", "when", "i want", "can you"],
        "spam": ["🔥", "😂", "lol"]
    }
}

def detect_keywords(text: str, lang: str = "fr") -> Dict[str, List[str]]:
    """
    Détecte les mots-clés dans un message.
    Retourne un dictionnaire : catégorie → liste de mots trouvés
    """
    result = {}
    lang = lang if lang in KEYWORDS_DB else "fr"
    text_lower = text.lower()

    for category, words in KEYWORDS_DB[lang].items():
        found = [kw for kw in words if re.search(rf"\b{re.escape(kw)}\b", text_lower)]
        if found:
            result[category] = found

    return result

def get_main_category(keyword_result: Dict[str, List[str]]) -> str:
    """
    Retourne la catégorie dominante (si multiple) par priorité métier.
    """
    priority_order = ["technique", "plainte", "positif", "demande", "spam"]
    for cat in priority_order:
        if cat in keyword_result:
            return cat
    return "non classifiable"


# Test unitaires

message = "Plus d’internet depuis ce matin, c’est inadmissible !"
lang = "fr"

keywords_found = detect_keywords(message, lang)
print("Mots-clés trouvés :", keywords_found)

main_category = get_main_category(keywords_found)
print("Catégorie dominante :", main_category)

# Test unitaires

message = "I'm not happy with the service, I'm going to cancel my subscription."
lang = "en"

keywords_found = detect_keywords(message, lang)
print("Mots-clés trouvés :", keywords_found)

main_category = get_main_category(keywords_found)
print("Catégorie dominante :", main_category)