"""Unit tests for data/player_stats.py"""

import pytest
import pandas as pd
from data.player_stats import build_roster, generate_stats, compute_performance_score, get_player_stats


def test_roster_shape():
    df = build_roster()
    assert len(df) == 100
    assert set(["player_id", "player_name", "position", "team"]).issubset(df.columns)


def test_roster_positions():
    df = build_roster()
    counts = df["position"].value_counts()
    assert counts["QB"] == 10
    assert counts["RB"] == 22
    assert counts["WR"] == 32
    assert counts["TE"] == 14
    assert counts["DEF"] == 22


def test_roster_reproducibility():
    df1 = build_roster(seed=42)
    df2 = build_roster(seed=42)
    assert df1["player_name"].tolist() == df2["player_name"].tolist()


def test_stats_no_nans():
    df = get_player_stats()
    assert df.isnull().sum().sum() == 0


def test_performance_score_range():
    df = get_player_stats()
    assert df["performance_score"].between(0.0, 100.0).all()


def test_performance_score_has_variance():
    df = get_player_stats()
    assert df["performance_score"].std() > 1.0


def test_qb_no_sacks():
    df = get_player_stats()
    qbs = df[df["position"] == "QB"]
    assert (qbs["sacks_pg"] == 0.0).all()


def test_def_no_passing():
    df = get_player_stats()
    defs = df[df["position"] == "DEF"]
    assert (defs["passing_yards_pg"] == 0.0).all()
