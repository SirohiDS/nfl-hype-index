"""Unit tests for data/sentiment_engine.py"""

import pytest
import pandas as pd
from data.sentiment_engine import get_sentiment_data, add_refresh_noise, _generate_base_sentiment
from data.player_stats import get_player_stats


def test_sentiment_shape():
    df = get_sentiment_data()
    assert len(df) == 100


def test_sentiment_score_bounds():
    df = get_sentiment_data()
    assert df["sentiment_score"].between(-1.0, 1.0).all()


def test_buzz_score_bounds():
    df = get_sentiment_data()
    assert df["buzz_score"].between(0.0, 100.0).all()


def test_fan_score_bounds():
    df = get_sentiment_data()
    assert df["fan_score"].between(0.0, 1.0).all()


def test_trending_is_bool():
    df = get_sentiment_data()
    assert df["trending"].dtype == bool


def test_noise_changes_output():
    df0 = get_sentiment_data(refresh_tick=0)
    df5 = get_sentiment_data(refresh_tick=5)
    # At least some sentiment scores must differ after noise injection
    assert not (df0["sentiment_score"] == df5["sentiment_score"]).all()


def test_same_tick_is_deterministic():
    df_a = get_sentiment_data(refresh_tick=3)
    df_b = get_sentiment_data(refresh_tick=3)
    pd.testing.assert_frame_equal(df_a, df_b)


def test_no_nans():
    df = get_sentiment_data()
    assert df.isnull().sum().sum() == 0
