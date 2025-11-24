# backend/config.py

from __future__ import annotations

import os
from pathlib import Path
from dotenv import load_dotenv

# Racine du projet : solution_Sav_Free/
BASE_DIR = Path(__file__).resolve().parents[1]

# Chargement du .env à la racine
ENV_PATH = BASE_DIR / ".env"
if ENV_PATH.exists():
    load_dotenv(ENV_PATH)

# Clé et modèle Mistral
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
MISTRAL_MODEL = os.getenv("MISTRAL_MODEL", "mistral-small-latest")

if not MISTRAL_API_KEY:
    # Tu peux commenter ça pour dev, mais en prod c'est bien
    raise RuntimeError("MISTRAL_API_KEY n'est pas définie dans le .env")

# Chemins data (optionnels mais propres)
RAW_DATA_PATH = os.getenv("RAW_DATA_PATH", "data/raw")
PROCESSED_DATA_PATH = os.getenv("PROCESSED_DATA_PATH", "data/processed")
