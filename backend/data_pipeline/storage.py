# backend/data_pipeline/storage.py

from __future__ import annotations

from pathlib import Path
import pandas as pd

DEFAULT_PREPARED_PATH = Path("data/processed/tweets_prepared.csv")
DEFAULT_ENRICHED_PATH = Path("data/processed/tweets_enriched.csv")


def save_prepared_tweets(df: pd.DataFrame, path: str | Path = DEFAULT_PREPARED_PATH) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, encoding="utf-8")
    return path


def save_enriched_tweets(df: pd.DataFrame, path: str | Path = DEFAULT_ENRICHED_PATH) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, encoding="utf-8")
    return path


def load_enriched_tweets(path: str | Path = DEFAULT_ENRICHED_PATH) -> pd.DataFrame:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Fichier enrichi introuvable : {path}")
    return pd.read_csv(path, dtype=str)
