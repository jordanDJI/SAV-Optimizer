# backend/data_pipeline/enrichment_pipeline.py

from __future__ import annotations

from pathlib import Path
import pandas as pd

from backend.data_pipeline.ingestion import load_raw_tweets
from backend.data_pipeline.cleaning import preprocess_tweets
from backend.data_pipeline.nlp_basic import enrich_with_basic_nlp
from backend.data_pipeline.classification import classify_tweets_df
from backend.data_pipeline.postprocessing import apply_llm_nlp_reconciliation
from backend.data_pipeline.storage import save_prepared_tweets, save_enriched_tweets
from backend.analytics.kpis_analyst import compute_kpis


def run_full_pipeline(
    raw_csv_path: str | Path,
    prepared_path: str | Path = "data/processed/tweets_prepared.csv",
    enriched_path: str | Path = "data/processed/tweets_enriched.csv",
    limit_llm: int | None = None,
) -> tuple[pd.DataFrame, dict]:
    raw_csv_path = Path(raw_csv_path)

    # 1) lecture brut
    df_raw = load_raw_tweets(raw_csv_path)

    # 2) nettoyage + keep_for_analysis
    df_prepared = preprocess_tweets(df_raw)

    # sauver la version préparée (nettoyée)
    save_prepared_tweets(df_prepared, prepared_path)

    # 3) NLP basique
    df_prepared = enrich_with_basic_nlp(df_prepared, text_col="text_clean")

    # 3b) limitation LLM (pour tests)
    if limit_llm is not None:
        mask_keep = df_prepared["keep_for_analysis"] == True
        idx_keep = df_prepared[mask_keep].index
        to_keep = idx_keep[:limit_llm]
        to_disable = idx_keep[limit_llm:]
        df_prepared.loc[to_disable, "keep_for_analysis"] = False

    # 4) LLM
    df_llm = classify_tweets_df(
        df_prepared,
        text_col="text_clean",
        keep_col="keep_for_analysis",
    )

    # 5) post-traitement
    df_final = apply_llm_nlp_reconciliation(df_llm)

    # 6) sauvegarde final
    save_enriched_tweets(df_final, enriched_path)

    # 7) KPIs
    kpis = compute_kpis(df_final)

    return df_final, kpis
