"""
Hype Index Calculator.

Merges performance and sentiment data then computes the Hype Index:

    hype_index = sentiment_rank - performance_rank

A positive value means fans rank the player higher than their stats
justify (overhyped); a negative value means fans underrate them.
"""

import pandas as pd

from data.player_stats import get_player_stats
from data.sentiment_engine import get_sentiment_data

# 5-tier label configuration (override via settings.yaml if needed)
_DEFAULT_THRESHOLDS = {
    "significantly_overhyped": 20,
    "overhyped": 10,
    "underrated": -10,
    "significantly_underrated": -20,
}

_LABEL_MAP = {
    "Significantly Overhyped": "#E74C3C",
    "Overhyped": "#E67E22",
    "Fair Value": "#27AE60",
    "Underrated": "#2980B9",
    "Significantly Underrated": "#8E44AD",
}


def merge_player_data(stats_df: pd.DataFrame, sentiment_df: pd.DataFrame) -> pd.DataFrame:
    """Inner-join stats and sentiment on player_id."""
    return pd.merge(stats_df, sentiment_df, on="player_id", how="inner")


def compute_hype_index(merged_df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute Hype Index for each player.

    Steps:
        1. Rank players by fan_score descending  → sentiment_rank
        2. Rank players by performance_score descending → performance_rank
        3. hype_index = sentiment_rank - performance_rank
        4. Normalise to [-100, +100] for display
    """
    df = merged_df.copy()
    n = len(df)

    df["sentiment_rank"] = df["fan_score"].rank(ascending=False, method="first").astype(int)
    df["performance_rank"] = df["performance_score"].rank(ascending=False, method="first").astype(int)
    df["hype_index"] = df["sentiment_rank"] - df["performance_rank"]

    # Normalise: divide by max possible rank delta then scale to [-100, +100]
    max_delta = max(n - 1, 1)
    df["hype_index_normalized"] = ((df["hype_index"] / max_delta) * 100).round(1)

    return df


def apply_hype_labels(
    df: pd.DataFrame,
    thresholds: dict | None = None,
) -> pd.DataFrame:
    """Attach human-readable hype_label and hype_color columns."""
    t = thresholds or _DEFAULT_THRESHOLDS
    df = df.copy()

    def _label(hi: int) -> str:
        if hi >= t["significantly_overhyped"]:
            return "Significantly Overhyped"
        if hi >= t["overhyped"]:
            return "Overhyped"
        if hi <= t["significantly_underrated"]:
            return "Significantly Underrated"
        if hi <= t["underrated"]:
            return "Underrated"
        return "Fair Value"

    df["hype_label"] = df["hype_index"].apply(_label)
    df["hype_color"] = df["hype_label"].map(_LABEL_MAP)
    return df


def get_full_rankings(refresh_tick: int = 0, base_seed: int = 42) -> pd.DataFrame:
    """
    Top-level function returning a complete DataFrame ready for the dashboard.

    Columns returned:
        player_id, player_name, team, position,
        [all stat columns], performance_score,
        sentiment_score, buzz_score, trending, weekly_delta, fan_score,
        sentiment_rank, performance_rank,
        hype_index, hype_index_normalized, hype_label, hype_color
    """
    stats = get_player_stats(seed=base_seed)
    sentiment = get_sentiment_data(refresh_tick=refresh_tick, base_seed=base_seed)
    merged = merge_player_data(stats, sentiment)
    ranked = compute_hype_index(merged)
    labeled = apply_hype_labels(ranked)

    # Sort by performance rank for the default leaderboard view
    labeled = labeled.sort_values("performance_rank").reset_index(drop=True)
    labeled.insert(0, "display_rank", labeled["performance_rank"])
    return labeled
