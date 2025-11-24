from __future__ import annotations

import json
from pathlib import Path
from typing import Optional, Dict

BASE_CONNEXION_PATH = Path(__file__).parent / "base_connexion.json"


def load_users() -> Dict:
    """
    Charge le fichier JSON des utilisateurs.
    """
    if not BASE_CONNEXION_PATH.exists():
        raise FileNotFoundError(f"base_connexion.json introuvable à {BASE_CONNEXION_PATH}")
    with open(BASE_CONNEXION_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def authenticate(username: str, password: str) -> Optional[Dict]:
    """
    Vérifie username/password.
    Retourne un dict {"username": ..., "role": ...} si OK, sinon None.
    """
    data = load_users()
    for user in data.get("users", []):
        if user.get("username") == username and user.get("password") == password:
            return {"username": user["username"], "role": user["role"]}
    return None
