"""
NFL Player Statistics Generator.

Generates a reproducible roster of 100 NFL players with realistic
per-game statistics and a composite Performance Score (0–100).
"""

import numpy as np
import pandas as pd

# 32 NFL teams (3-letter codes)
NFL_TEAMS = [
    "ARI", "ATL", "BAL", "BUF", "CAR", "CHI", "CIN", "CLE",
    "DAL", "DEN", "DET", "GB", "HOU", "IND", "JAX", "KC",
    "LAC", "LAR", "LV", "MIA", "MIN", "NE", "NO", "NYG",
    "NYJ", "PHI", "PIT", "SEA", "SF", "TB", "TEN", "WAS",
]

# Realistic name pools per position
_QB_NAMES = [
    "Patrick Mahomes", "Lamar Jackson", "Josh Allen", "Jalen Hurts",
    "Joe Burrow", "Dak Prescott", "Tua Tagovailoa", "Justin Herbert",
    "Brock Purdy", "Jordan Love",
]
_RB_NAMES = [
    "Christian McCaffrey", "Derrick Henry", "Saquon Barkley", "Tony Pollard",
    "Austin Ekeler", "Breece Hall", "Rhamondre Stevenson", "Travis Etienne",
    "Jonathan Taylor", "De'Von Achane", "Aaron Jones", "Josh Jacobs",
    "Alvin Kamara", "James Conner", "Rachaad White", "Raheem Mostert",
    "Jaylen Warren", "Kenneth Walker III", "Isiah Pacheco", "Dameon Pierce",
    "Chuba Hubbard", "D'Andre Swift",
]
_WR_NAMES = [
    "Tyreek Hill", "Justin Jefferson", "CeeDee Lamb", "Stefon Diggs",
    "Davante Adams", "Jaylen Waddle", "Mike Evans", "DJ Moore",
    "Puka Nacua", "Deebo Samuel", "DK Metcalf", "Cooper Kupp",
    "DeVonta Smith", "Chris Olave", "Amon-Ra St. Brown", "Tyler Lockett",
    "Brandin Cooks", "Michael Pittman Jr.", "Garrett Wilson", "Romeo Doubs",
    "Rashid Shaheed", "Drake London", "Gabe Davis", "Tee Higgins",
    "Kadarius Toney", "Courtland Sutton", "Zay Jones", "Diontae Johnson",
    "Elijah Moore", "Christian Kirk", "Darius Slayton", "Jerry Jeudy",
]
_TE_NAMES = [
    "Travis Kelce", "Sam LaPorta", "Mark Andrews", "T.J. Hockenson",
    "Dallas Goedert", "George Kittle", "David Njoku", "Evan Engram",
    "Jake Ferguson", "Tyler Conklin", "Pat Freiermuth", "Cole Kmet",
    "Kyle Pitts", "Dalton Kincaid",
]
_DEF_NAMES = [
    "Micah Parsons", "Myles Garrett", "Maxx Crosby", "Nick Bosa",
    "Danielle Hunter", "TJ Watt", "Haason Reddick", "Aidan Hutchinson",
    "Khalil Mack", "Josh Allen (DEF)", "Brian Burns", "Trey Hendrickson",
    "Rashan Gary", "Jonathan Greenard", "Will Anderson Jr.", "Kayvon Thibodeaux",
    "Jalen Carter", "Quay Walker", "Fred Warner", "Roquan Smith",
    "Darius Leonard", "Devin White",
]

# Position stat distribution parameters (mean, std) — per-game averages
_STAT_PARAMS = {
    "QB": {
        "passing_yards_pg": (260.0, 55.0),
        "rush_yards_pg": (28.0, 18.0),
        "pass_tds_pg": (1.8, 0.6),
        "interceptions_pg": (0.7, 0.35),
    },
    "RB": {
        "rush_yards_pg": (72.0, 28.0),
        "receiving_yards_pg": (28.0, 18.0),
        "rush_tds_pg": (0.55, 0.3),
        "recv_tds_pg": (0.1, 0.1),
    },
    "WR": {
        "receiving_yards_pg": (68.0, 25.0),
        "recv_tds_pg": (0.45, 0.25),
        "rush_yards_pg": (2.0, 4.0),
    },
    "TE": {
        "receiving_yards_pg": (52.0, 22.0),
        "recv_tds_pg": (0.38, 0.22),
    },
    "DEF": {
        "sacks_pg": (0.65, 0.35),
        "tackles_pg": (4.2, 1.8),
    },
}

# Position-specific performance score weights
_PERF_WEIGHTS = {
    "QB":  {"passing_yards_pg": 0.40, "pass_tds_pg": 0.25, "rush_yards_pg": 0.20, "interceptions_pg": 0.15},
    "RB":  {"rush_yards_pg": 0.50, "rush_tds_pg": 0.30, "receiving_yards_pg": 0.20},
    "WR":  {"receiving_yards_pg": 0.55, "recv_tds_pg": 0.30, "rush_yards_pg": 0.15},
    "TE":  {"receiving_yards_pg": 0.55, "recv_tds_pg": 0.45},
    "DEF": {"sacks_pg": 0.50, "tackles_pg": 0.50},
}

ALL_STAT_COLS = [
    "passing_yards_pg", "rush_yards_pg", "receiving_yards_pg",
    "pass_tds_pg", "recv_tds_pg", "rush_tds_pg",
    "interceptions_pg", "sacks_pg", "tackles_pg",
]


def build_roster(seed: int = 42) -> pd.DataFrame:
    """Build a 100-player NFL roster across 32 teams."""
    rng = np.random.default_rng(seed)
    positions = (
        [("QB", name) for name in _QB_NAMES] +
        [("RB", name) for name in _RB_NAMES] +
        [("WR", name) for name in _WR_NAMES] +
        [("TE", name) for name in _TE_NAMES] +
        [("DEF", name) for name in _DEF_NAMES]
    )
    teams = rng.choice(NFL_TEAMS, size=len(positions), replace=True)
    roster = pd.DataFrame(
        [{"player_id": f"P{i:03d}", "player_name": name, "position": pos, "team": teams[i]}
         for i, (pos, name) in enumerate(positions)]
    )
    return roster


def _sample_stat(rng: np.random.Generator, mean: float, std: float, low: float = 0.0) -> float:
    return float(np.clip(rng.normal(mean, std), low, None))


def generate_stats(roster_df: pd.DataFrame, seed: int = 42) -> pd.DataFrame:
    """Generate position-gated per-game statistics for each player."""
    rng = np.random.default_rng(seed + 1)
    rows = []
    for _, row in roster_df.iterrows():
        pos = row["position"]
        params = _STAT_PARAMS[pos]
        stat = {col: 0.0 for col in ALL_STAT_COLS}
        for col, (mean, std) in params.items():
            stat[col] = _sample_stat(rng, mean, std)
        rows.append(stat)

    stats_df = pd.DataFrame(rows, index=roster_df.index)
    return pd.concat([roster_df.reset_index(drop=True), stats_df.reset_index(drop=True)], axis=1)


def _minmax(series: pd.Series, invert: bool = False) -> pd.Series:
    mn, mx = series.min(), series.max()
    if mx == mn:
        return pd.Series(0.5, index=series.index)
    normalized = (series - mn) / (mx - mn)
    return 1.0 - normalized if invert else normalized


def compute_performance_score(df: pd.DataFrame) -> pd.DataFrame:
    """Compute a composite Performance Score [0, 100] per player."""
    # Build normalized stat columns
    norm = {}
    for col in ALL_STAT_COLS:
        invert = col == "interceptions_pg"
        norm[f"norm_{col}"] = _minmax(df[col], invert=invert)

    norm_df = pd.DataFrame(norm, index=df.index)
    scores = pd.Series(0.0, index=df.index)

    for _, row in df.iterrows():
        pos = row["position"]
        weights = _PERF_WEIGHTS[pos]
        score = sum(norm_df.loc[row.name, f"norm_{col}"] * w for col, w in weights.items())
        scores[row.name] = score

    # Scale to 0–100
    df = df.copy()
    df["performance_score"] = (_minmax(scores) * 100).round(2)
    return df


def get_player_stats(seed: int = 42) -> pd.DataFrame:
    """Return complete DataFrame with all stat columns + performance_score."""
    roster = build_roster(seed=seed)
    stats = generate_stats(roster, seed=seed)
    return compute_performance_score(stats)
