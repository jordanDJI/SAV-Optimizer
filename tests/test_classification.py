import pandas as pd
from unittest.mock import patch
from backend.data_pipeline.classification_service import classify_tweets_df


def mock_llm_response(text):
    if "merci free pour la coupure" in text.lower():
        return {
            "sentiment": "negatif",
            "category": "plainte",
            "complaint_type": "panne réseau",
            "irony": True,
            "priority": "élevée"
        }
    return {
        "sentiment": "neutre",
        "category": "autre",
        "complaint_type": None,
        "irony": False,
        "priority": "faible"
    }


@patch("backend.data_pipeline.classification_service.process_with_llm", side_effect=mock_llm_response)
def test_classification_detects_irony(mock_llm):
    df = pd.DataFrame({
        "clean_text": ["Merci Free pour la coupure internet depuis 2 jours, au top 🙃"]
    })

    classified = classify_tweets_df(df)
    row = classified.iloc[0]

    assert row["category"] == "plainte"
    assert row["irony"] is True
    assert row["priority"] == "élevée"


@patch("backend.data_pipeline.classification_service.process_with_llm", side_effect=mock_llm_response)
def test_classification_default_other(mock_llm):
    df = pd.DataFrame({
        "clean_text": ["Bonjour tout le monde"]
    })

    classified = classify_tweets_df(df)

    assert classified.iloc[0]["category"] == "autre"
