"""Unit tests for data/hype_calculator.py"""

import pytest
import pandas as pd
from data.hype_calculator import get_full_rankings, compute_hype_index, apply_hype_labels, merge_player_data
from data.player_stats import get_player_stats
from data.sentiment_engine import get_sentiment_data


def test_full_rankings_shape():
    df = get_full_rankings()
    assert len(df) == 100


def test_required_columns_present():
    df = get_full_rankings()
    required = [
        "player_id", "player_name", "team", "position",
        "performance_score", "sentiment_score", "buzz_score",
        "fan_score", "sentiment_rank", "performance_rank",
        "hype_index", "hype_index_normalized", "hype_label", "hype_color",
    ]
    for col in required:
        assert col in df.columns, f"Missing column: {col}"


def test_hype_index_formula():
    """Verify hype_index = sentiment_rank - performance_rank exactly."""
    df = get_full_rankings()
    computed = df["sentiment_rank"] - df["performance_rank"]
    pd.testing.assert_series_equal(df["hype_index"], computed, check_names=False)


def test_hype_index_normalized_range():
    df = get_full_rankings()
    assert df["hype_index_normalized"].between(-100.0, 100.0).all()


def test_ranks_are_unique():
    df = get_full_rankings()
    assert df["performance_rank"].nunique() == len(df)
    assert df["sentiment_rank"].nunique() == len(df)


def test_hype_labels_valid():
    valid_labels = {
        "Significantly Overhyped", "Overhyped", "Fair Value",
        "Underrated", "Significantly Underrated",
    }
    df = get_full_rankings()
    assert set(df["hype_label"].unique()).issubset(valid_labels)


def test_significantly_overhyped_threshold():
    df = get_full_rankings()
    sig_over = df[df["hype_label"] == "Significantly Overhyped"]
    assert (sig_over["hype_index"] >= 20).all()


def test_significantly_underrated_threshold():
    df = get_full_rankings()
    sig_under = df[df["hype_label"] == "Significantly Underrated"]
    assert (sig_under["hype_index"] <= -20).all()


def test_same_tick_deterministic():
    df1 = get_full_rankings(refresh_tick=7)
    df2 = get_full_rankings(refresh_tick=7)
    pd.testing.assert_frame_equal(df1.reset_index(drop=True), df2.reset_index(drop=True))
