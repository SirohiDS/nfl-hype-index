"""
Dash Callbacks.

All callback logic separated from layout (app.py) for clarity.
Imported as a side-effect by app.py to register callbacks on the app object.
"""

from datetime import datetime

from dash import Input, Output, State, callback, no_update
from dash import html

from app.figures import (
    make_scatter_plot,
    make_hype_bar_chart,
    make_player_detail_card,
    make_leaderboard_style_conditions,
)
from data.hype_calculator import get_full_rankings


# ── Callback 1: tick counter ─────────────────────────────────────────────────
@callback(
    Output("refresh-tick", "data"),
    Input("refresh-interval", "n_intervals"),
)
def update_refresh_tick(n_intervals: int) -> int:
    """Advance the tick counter on each interval fire."""
    return n_intervals or 0


# ── Callback 2: main visuals ─────────────────────────────────────────────────
@callback(
    Output("leaderboard-table", "data"),
    Output("leaderboard-table", "style_data_conditional"),
    Output("scatter-plot", "figure"),
    Output("hype-bar-chart", "figure"),
    Output("last-updated", "children"),
    Input("refresh-tick", "data"),
    Input("filter-position", "value"),
    Input("filter-team", "value"),
    Input("filter-hype-category", "value"),
)
def update_all_visuals(tick, pos_filter, team_filter, hype_filter):
    """Fetch rankings, apply filters, build all visual outputs."""
    df = get_full_rankings(refresh_tick=tick or 0)

    # Apply filters
    if pos_filter and pos_filter != "ALL":
        df = df[df["position"] == pos_filter]
    if team_filter and team_filter != "ALL":
        df = df[df["team"] == team_filter]
    if hype_filter and hype_filter != "ALL":
        df = df[df["hype_label"] == hype_filter]

    # Prepare table rows
    table_df = df[[
        "display_rank", "player_name", "team", "position",
        "performance_score", "sentiment_score", "buzz_score",
        "trending", "hype_index", "hype_label", "player_id",
        "hype_color",
    ]].copy()
    table_df["performance_score"] = table_df["performance_score"].round(1)
    table_df["sentiment_score"] = table_df["sentiment_score"].round(3)
    table_df["buzz_score"] = table_df["buzz_score"].round(0).astype(int)
    table_df["trending"] = table_df["trending"].apply(lambda v: "↑ Hot" if v else "—")

    table_data = table_df.drop(columns=["player_id", "hype_color"]).to_dict("records")

    # Style conditions need player_id — pass full df
    style_conds = make_leaderboard_style_conditions(df)

    scatter = make_scatter_plot(df)
    bar = make_hype_bar_chart(df)
    timestamp = f"Last updated: {datetime.now().strftime('%H:%M:%S')}"

    return table_data, style_conds, scatter, bar, timestamp


# ── Callback 3: team filter options ─────────────────────────────────────────
@callback(
    Output("filter-team", "options"),
    Input("filter-position", "value"),
    Input("refresh-tick", "data"),
)
def update_team_options(pos_filter, tick):
    """Update team dropdown to only teams relevant to the selected position."""
    df = get_full_rankings(refresh_tick=tick or 0)
    if pos_filter and pos_filter != "ALL":
        df = df[df["position"] == pos_filter]
    teams = sorted(df["team"].unique().tolist())
    options = [{"label": "ALL", "value": "ALL"}] + [{"label": t, "value": t} for t in teams]
    return options


# ── Callback 4: player detail card ────────────────────────────────────────────
@callback(
    Output("player-detail-card", "children"),
    Input("leaderboard-table", "selected_rows"),
    State("leaderboard-table", "data"),
    Input("refresh-tick", "data"),
    prevent_initial_call=True,
)
def show_player_detail(selected_rows, table_data, tick):
    """Render detail card when a table row is selected."""
    if not selected_rows or not table_data:
        return no_update

    row_idx = selected_rows[0]
    if row_idx >= len(table_data):
        return no_update

    selected_name = table_data[row_idx]["player_name"]
    full_df = get_full_rankings(refresh_tick=tick or 0)
    matches = full_df[full_df["player_name"] == selected_name]
    if matches.empty:
        return no_update

    player = matches.iloc[0].to_dict()
    return [
        html.Hr(style={"borderColor": "#30363D", "margin": "0 0 12px"}),
        make_player_detail_card(player),
    ]
