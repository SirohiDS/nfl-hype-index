# NFL Hype Index Dashboard

> A sentiment-driven NFL player ranking engine that identifies **over/underrated players** by comparing fan enthusiasm rank vs objective performance rank — in real time.

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)
![Dash](https://img.shields.io/badge/Dash-3.0.4-blueviolet?logo=plotly)
![Plotly](https://img.shields.io/badge/Plotly-6.1.2-blue?logo=plotly)
![Docker](https://img.shields.io/badge/Docker-ready-2496ED?logo=docker)

---

## What is the Hype Index?

The **Hype Index** quantifies the gap between how fans perceive a player and what their statistics actually justify:

```
Hype Index = Sentiment Rank − Performance Rank
```

| Value | Interpretation |
|---|---|
| **≥ +20** | Significantly Overhyped — fans love them far more than stats warrant |
| **+10 to +20** | Overhyped |
| **−10 to +10** | Fair Value — hype matches production |
| **−20 to −10** | Underrated |
| **≤ −20** | Significantly Underrated — a hidden gem |

A player ranked **#5 by sentiment** but **#40 by performance** gets a Hype Index of **+35 → Significantly Overhyped**.

---

## Dashboard Features

- **Live Leaderboard** — sortable, filterable table with color-coded Hype Index cells
- **Performance vs Sentiment Scatter Plot** — dashed "fair value" diagonal; outliers annotated
- **Hype Bar Chart** — top 10 most overhyped and underrated players side-by-side
- **Player Detail Card** — click any row to expand per-game stats, rank comparison, and sentiment breakdown
- **Filters** — position (QB / RB / WR / TE / DEF), team, hype category
- **Auto-Refresh** — sentiment data updates every 30 seconds (seeded noise simulates live shifts)

---

## Architecture

```
+------------------+     +---------------------+     +-------------------+
|  player_stats.py |     | sentiment_engine.py  |     | hype_calculator.py|
|                  |     |                     |     |                   |
| • 100 NFL players|     | • sentiment_score   |     | • sentiment_rank  |
| • per-game stats |────▶| • buzz_score        |────▶| • perf_rank       |
| • perf_score     |     | • trending          |     | • hype_index      |
|   (0–100)        |     | • weekly_delta      |     | • hype_label      |
+------------------+     | • noise on refresh  |     +--------+----------+
                          +---------------------+              │
                                                               ▼
                    +----------------------------------------------+
                    |            Dash App  (app.py)                |
                    |                                              |
                    |  Sidebar Filters   │  Main Panel            |
                    |  • Position        │  • Leaderboard Table   |
                    |  • Team            │  • Scatter Plot        |
                    |  • Hype Category   │  • Hype Bar Chart      |
                    |                    │  • Player Detail Card  |
                    |       Auto-refresh every 30 seconds         |
                    +----------------------------------------------+
                                         │
                               http://localhost:8050
```

---

## Quick Start

### Docker (recommended)

```bash
git clone https://github.com/<your-username>/nfl-hype-index.git
cd nfl-hype-index
docker-compose up --build
```

Open **http://localhost:8050**

### Local Development

```bash
git clone https://github.com/<your-username>/nfl-hype-index.git
cd nfl-hype-index

python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

python app/app.py
```

Open **http://localhost:8050**

### Run Tests

```bash
pip install -r requirements.txt
python -m pytest tests/ -v
```

---

## Project Structure

```
nfl-hype-index/
├── data/
│   ├── player_stats.py       # NFL roster + per-game stat generator + Performance Score
│   ├── sentiment_engine.py   # Simulated fan sentiment with seeded refresh noise
│   └── hype_calculator.py    # Hype Index: rank delta computation + 5-tier labeling
├── app/
│   ├── app.py                # Dash init, layout, server export
│   ├── callbacks.py          # All Dash callbacks
│   ├── figures.py            # Plotly figure factories (scatter, bar, detail card)
│   └── assets/custom.css     # Dark theme overrides
├── config/
│   └── settings.yaml         # Thresholds, colors, seeds, refresh interval
├── tests/                    # Pytest unit tests for all data modules
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

---

## Data Design

All data is **generated in-memory** — no external APIs or database required.

### Performance Score (0–100)
Position-weighted composite of normalized per-game stats:
- **QB**: 40% passing yards, 25% pass TDs, 20% rush yards, 15% INTs (inverted)
- **RB**: 50% rush yards, 30% rush TDs, 20% receiving yards
- **WR**: 55% receiving yards, 30% recv TDs, 15% rush yards
- **TE**: 55% receiving yards, 45% recv TDs
- **DEF**: 50% sacks, 50% tackles

### Sentiment Score & Fan Score
```
fan_score = sentiment_weight × 0.7 + buzz_weight × 0.3
```
where `sentiment_weight = (sentiment_score + 1) / 2` maps [-1, 1] → [0, 1].

Each refresh tick injects small deterministic noise (seeded), so the dashboard simulates a live data stream without any external dependencies.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Dashboard | Dash 3.0.4 + Dash Bootstrap Components |
| Charts | Plotly 6.1.2 |
| Data | Pandas 2.2.2 + NumPy 1.26.4 |
| Config | PyYAML 6.0.2 |
| Server | Gunicorn 23.0.0 |
| Container | Docker + docker-compose |
| Tests | Pytest 7.4.4 |
| Python | 3.11 |
