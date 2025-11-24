import pandas as pd
from backend.analytics.kpis_analyst import compute_kpis


def test_kpis_compute_counts_correctly():
    df = pd.DataFrame({
        "tweet_type": ["post", "comment", "retweet", "quote"],
        "sentiment": ["negatif", "positif", "neutre", "negatif"],
        "category": ["plainte", "remerciement", "autre", "plainte"],
        "screen_name": ["client1", "Freebox", "client2", "client3"],
        "keep_for_analysis": [True, True, False, True]
    })

    kpis = compute_kpis(df)

    assert kpis["global"]["total"] == 4
    assert kpis["global"]["kept"] == 3

    assert kpis["structure"]["retweets"] == 1
    assert kpis["structure"]["quotes"] == 1

    assert kpis["sentiments"]["negatif"] == 2
    assert kpis["categories"]["plainte"] == 2


def test_kpis_exclude_non_kept():
    df = pd.DataFrame({
        "tweet_type": ["retweet", "post"],
        "keep_for_analysis": [False, True]
    })

    kpis = compute_kpis(df)

    assert kpis["global"]["kept"] == 1
