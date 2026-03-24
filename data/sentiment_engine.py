"""
Fan Sentiment Engine.

Simulates fan sentiment for NFL players using seeded random generation.
A stable base state is computed once; small noise is injected on every
30-second refresh tick to simulate live shifts in fan opinion.
"""

import numpy as np
import pandas as pd

from data.player_stats import get_player_stats


def _generate_base_sentiment(player_ids: pd.Index, seed: int = 42) -> pd.DataFrame:
    """
    Generate stable ground-truth sentiment for each player.

    Returns a DataFrame with columns:
        player_id, sentiment_score, buzz_score, weekly_delta
    """
    rng = np.random.default_rng(seed)
    n = len(player_ids)

    # Sentiment: slight positive fan bias, clipped to [-1, 1]
    sentiment_score = np.clip(rng.normal(0.1, 0.4, n), -1.0, 1.0)

    # Buzz: half-normal so most players have low buzz, stars have high
    buzz_raw = np.abs(rng.normal(0, 30, n))
    buzz_score = np.clip(buzz_raw, 0.0, 100.0)

    # Weekly delta: momentum indicator
    weekly_delta = np.clip(rng.normal(0.0, 0.1, n), -0.3, 0.3)

    return pd.DataFrame({
        "player_id": player_ids,
        "sentiment_score": sentiment_score.round(4),
        "buzz_score": buzz_score.round(2),
        "weekly_delta": weekly_delta.round(4),
    })


def add_refresh_noise(base_df: pd.DataFrame, noise_seed: int) -> pd.DataFrame:
    """
    Apply small perturbations to simulate a live sentiment update.

    noise_seed increments each 30-second tick, ensuring deterministic
    but distinct output on each refresh.
    """
    rng = np.random.default_rng(noise_seed)
    df = base_df.copy()
    n = len(df)

    df["sentiment_score"] = np.clip(
        df["sentiment_score"] + rng.normal(0, 0.03, n), -1.0, 1.0
    ).round(4)
    df["buzz_score"] = np.clip(
        df["buzz_score"] + rng.normal(0, 1.5, n), 0.0, 100.0
    ).round(2)
    df["weekly_delta"] = np.clip(
        df["weekly_delta"] + rng.normal(0, 0.02, n), -0.3, 0.3
    ).round(4)
    df["trending"] = df["weekly_delta"] > 0.05

    return df


def compute_sentiment_weighted_score(sentiment_df: pd.DataFrame) -> pd.Series:
    """
    Compute a unified fan_score in [0, 1] combining sentiment and buzz.

    Formula:
        sentiment_weight = (sentiment_score + 1.0) / 2.0   # [-1,1] → [0,1]
        buzz_weight      = buzz_score / 100.0
        fan_score        = sentiment_weight * 0.7 + buzz_weight * 0.3
    """
    s_weight = (sentiment_df["sentiment_score"] + 1.0) / 2.0
    b_weight = sentiment_df["buzz_score"] / 100.0
    return (s_weight * 0.7 + b_weight * 0.3).round(4)


def get_sentiment_data(refresh_tick: int = 0, base_seed: int = 42) -> pd.DataFrame:
    """
    Return sentiment DataFrame for all players.

    refresh_tick drives the noise seed so each 30-second interval
    produces a slightly different but deterministic result.
    """
    stats_df = get_player_stats(seed=base_seed)
    base = _generate_base_sentiment(stats_df["player_id"], seed=base_seed)
    noisy = add_refresh_noise(base, noise_seed=base_seed + refresh_tick + 1000)
    noisy["fan_score"] = compute_sentiment_weighted_score(noisy)
    return noisy
