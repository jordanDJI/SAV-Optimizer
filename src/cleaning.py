import re
import pandas as pd
from typing import Optional
import logging

logger = logging.getLogger(__name__)


def clean_text(text: str):

    if pd.isna(text) or not isinstance(text, str):
        return ""
    # Supprimer les URLs
    text = re.sub(r'http\S+|www\.\S+', '', text)
    # Supprimer les mentions @
    text = re.sub(r'@\w+', '', text)
    # Supprimer les hashtags (garder le texte)
    text = re.sub(r'#(\w+)', r'\1', text)
    # Normaliser les espaces multiples
    text = re.sub(r'\s+', ' ', text)
    # Supprimer les espaces en début/fin
    text = text.strip()
    
    return text


def remove_duplicates(df: pd.DataFrame, column: str = "full_text"):

    initial_count = len(df)
    df_clean = df.drop_duplicates(subset=[column], keep='first')
    removed = initial_count - len(df_clean)
    
    if removed > 0:
        logger.info(f"Suppression de {removed} doublons basés sur '{column}'")
    
    return df_clean


def filter_empty_text(df: pd.DataFrame, column: str = "full_text"):

    initial_count = len(df)
    df_clean = df[df[column].notna() & (df[column].str.strip() != "")]
    removed = initial_count - len(df_clean)
    
    if removed > 0:
        logger.info(f"Suppression de {removed} lignes avec texte vide")
    
    return df_clean


def clean_dataframe(df: pd.DataFrame, text_column: str = "full_text") -> pd.DataFrame:

    logger.info(f"Nettoyage du DataFrame: {len(df)} lignes initiales")
    
    df_clean = df.copy()
    

    if text_column in df_clean.columns:
        df_clean[text_column] = df_clean[text_column].apply(clean_text)
    
    df_clean = filter_empty_text(df_clean, text_column)
    
    df_clean = remove_duplicates(df_clean, text_column)
    
    logger.info(f"DataFrame nettoyé: {len(df_clean)} lignes finales")
    return df_clean

