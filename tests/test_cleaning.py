import pandas as pd
from backend.data_pipeline.cleaning_service import clean_tweets_dataframe


def test_cleaning_removes_urls_mentions_and_lowercase():
    df = pd.DataFrame({
        "full_text": [
            "Bonjour @Freebox voici un lien http://test.com 😀"
        ]
    })

    cleaned = clean_tweets_dataframe(df)

    assert "@" not in cleaned.loc[0, "clean_text"]
    assert "http" not in cleaned.loc[0, "clean_text"]
    assert cleaned.loc[0, "clean_text"].islower()


def test_cleaning_handles_missing_values():
    df = pd.DataFrame({
        "full_text": [None, "Test tweet"]
    })

    cleaned = clean_tweets_dataframe(df)

    assert cleaned.loc[0, "clean_text"] == ""
    assert cleaned.loc[1, "clean_text"] == "test tweet"


def test_cleaning_removes_excess_spaces():
    df = pd.DataFrame({
        "full_text": ["Ceci   est   un   test   Free    "]
    })

    cleaned = clean_tweets_dataframe(df)
    assert "  " not in cleaned.loc[0, "clean_text"]
