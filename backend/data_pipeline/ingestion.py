# backend/data_pipeline/ingestion.py

from __future__ import annotations

from pathlib import Path
import pandas as pd


def load_raw_tweets(csv_path: str | Path) -> pd.DataFrame:
    """
    Charge le CSV brut, garde tout en string, nettoie les noms de colonnes.
    """
    csv_path = Path(csv_path)
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV brut introuvable : {csv_path}")

    df = pd.read_csv(csv_path, dtype=str)
    df.columns = [c.strip() for c in df.columns]
    return df
