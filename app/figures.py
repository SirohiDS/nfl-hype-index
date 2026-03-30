"""
Plotly Figure Factories.

Pure functions: take DataFrames, return go.Figure or Dash HTML components.
No Dash app imports — fully testable in isolation.
"""

import pandas as pd
import plotly.graph_objects as go
import dash_bootstrap_components as dbc
from dash import html

# Color constants (mirrors settings.yaml — kept inline for import independence)
_BG = "#0D1117"
_CARD_BG = "#161B22"
_BORDER = "#30363D"
_TEXT = "#E6EDF3"
_TEXT_SEC = "#8B949E"
_ACCENT = "#58A6FF"

_HYPE_COLORS = {
    "Significantly Overhyped": "#E74C3C",
    "Overhyped": "#E67E22",
    "Fair Value": "#27AE60",
    "Underrated": "#2980B9",
    "Significantly Underrated": "#8E44AD",
}

_DARK_LAYOUT = dict(
    paper_bgcolor=_CARD_BG,
    plot_bgcolor=_CARD_BG,
    font=dict(color=_TEXT, family="Segoe UI, Arial, sans-serif", size=12),
    margin=dict(l=12, r=12, t=40, b=12),
    xaxis=dict(gridcolor=_BORDER, zerolinecolor=_BORDER),
    yaxis=dict(gridcolor=_BORDER, zerolinecolor=_BORDER),
)


def make_scatter_plot(df: pd.DataFrame) -> go.Figure:
    """
    Performance Score (x) vs Sentiment Score (y) scatter plot.

    - Dot color: hype_index_normalized (diverging RdYlGn)
    - Dot size: buzz_score (6–20 px)
    - Dashed diagonal: 'fair value' reference line
    - Top-5 outliers annotated by name
    """
    if df.empty:
        return go.Figure(layout=_DARK_LAYOUT)

    # Normalise buzz to marker size [6, 20]
    buzz_min, buzz_max = df["buzz_score"].min(), df["buzz_score"].max()
    if buzz_max > buzz_min:
        sizes = 6 + (df["buzz_score"] - buzz_min) / (buzz_max - buzz_min) * 14
    else:
        sizes = pd.Series(10, index=df.index)

    fig = go.Figure()

    # Fair-value diagonal (where sentiment ≈ performance)
    fig.add_trace(go.Scatter(
        x=[0, 100], y=[-1, 1],
        mode="lines",
        line=dict(color=_TEXT_SEC, dash="dash", width=1),
        name="Fair Value Line",
        hoverinfo="skip",
    ))

    # Main scatter
    fig.add_trace(go.Scatter(
        x=df["performance_score"],
        y=df["sentiment_score"],
        mode="markers",
        marker=dict(
            size=sizes,
            color=df["hype_index_normalized"],
            colorscale="RdYlGn_r",  # red=overhyped, green=underrated
            cmin=-100, cmax=100,
            colorbar=dict(
                title=dict(text="Hype Index", font=dict(color=_TEXT_SEC, size=11)),
                tickfont=dict(color=_TEXT_SEC, size=10),
                len=0.7, thickness=10,
            ),
            line=dict(color=_BORDER, width=0.5),
            opacity=0.85,
        ),
        text=df["player_name"],
        customdata=df[["team", "position", "hype_label", "hype_index"]].values,
        hovertemplate=(
            "<b>%{text}</b><br>"
            "%{customdata[0]} | %{customdata[1]}<br>"
            "Perf. Score: %{x:.1f}<br>"
            "Sentiment: %{y:.2f}<br>"
            "Hype: %{customdata[3]:+d} (%{customdata[2]})"
            "<extra></extra>"
        ),
        name="Players",
    ))

    # Annotate top-5 most extreme outliers (highest absolute hype_index)
    extremes = df.nlargest(3, "hype_index_normalized").index.tolist()
    extremes += df.nsmallest(3, "hype_index_normalized").index.tolist()
    for idx in extremes:
        row = df.loc[idx]
        fig.add_annotation(
            x=row["performance_score"],
            y=row["sentiment_score"],
            text=row["player_name"].split()[-1],  # last name only
            showarrow=True,
            arrowhead=0,
            arrowcolor=_TEXT_SEC,
            arrowwidth=1,
            font=dict(size=9, color=_TEXT_SEC),
            bgcolor=_CARD_BG,
            bordercolor=_BORDER,
            borderwidth=1,
            ax=20, ay=-20,
        )

    fig.update_layout(
        **{k: v for k, v in _DARK_LAYOUT.items() if k not in ("xaxis", "yaxis")},
        title=dict(text="Performance vs Sentiment", font=dict(size=14, color=_TEXT), x=0.02),
        xaxis=dict(**_DARK_LAYOUT["xaxis"], title="Performance Score (0–100)", range=[-2, 105]),
        yaxis=dict(**_DARK_LAYOUT["yaxis"], title="Sentiment Score (−1 to +1)", range=[-1.1, 1.1]),
        showlegend=False,
        height=380,
    )
    return fig


def make_hype_bar_chart(df: pd.DataFrame) -> go.Figure:
    """
    Horizontal bar chart: Top 10 most overhyped + Top 10 most underrated.

    Positive bars extend right, negative bars extend left.
    Threshold lines at ±10 and ±20.
    """
    if df.empty:
        return go.Figure(layout=_DARK_LAYOUT)

    top_over = df.nlargest(10, "hype_index")
    top_under = df.nsmallest(10, "hype_index")
    combined = pd.concat([top_over, top_under]).drop_duplicates("player_id")
    combined = combined.sort_values("hype_index")

    colors = combined["hype_color"].tolist()

    fig = go.Figure(go.Bar(
        x=combined["hype_index"],
        y=combined["player_name"],
        orientation="h",
        marker=dict(color=colors, line=dict(color=_BORDER, width=0.5)),
        text=combined["hype_index"].apply(lambda v: f"{v:+d}"),
        textposition="outside",
        textfont=dict(size=10, color=_TEXT_SEC),
        customdata=combined[["team", "position", "hype_label"]].values,
        hovertemplate=(
            "<b>%{y}</b><br>"
            "%{customdata[0]} | %{customdata[1]}<br>"
            "Hype Index: %{x:+d}<br>"
            "%{customdata[2]}<extra></extra>"
        ),
    ))

    # Threshold lines
    for xval, color in [(-20, "#8E44AD"), (-10, "#2980B9"),
                         (10, "#E67E22"), (20, "#E74C3C")]:
        fig.add_vline(x=xval, line_dash="dot", line_color=color,
                      line_width=1, opacity=0.6)

    # Zero line
    fig.add_vline(x=0, line_color=_TEXT_SEC, line_width=1.5)

    fig.update_layout(
        **{k: v for k, v in _DARK_LAYOUT.items() if k not in ("xaxis", "yaxis")},
        title=dict(text="Most Overhyped & Underrated (Top 10 Each)",
                   font=dict(size=14, color=_TEXT), x=0.02),
        xaxis=dict(**_DARK_LAYOUT["xaxis"], title="Hype Index",
                   tickvals=[-20, -10, 0, 10, 20]),
        yaxis=dict(**_DARK_LAYOUT["yaxis"], title="", tickfont=dict(size=10)),
        height=380,
        bargap=0.25,
    )
    return fig


def make_player_detail_card(player: dict) -> dbc.Card:
    """
    Rich detail card shown when a leaderboard row is clicked.
    Returns a dbc.Card component.
    """
    hype_color = player.get("hype_color", "#27AE60")
    hype_label = player.get("hype_label", "Fair Value")
    trending_icon = "↑ Hot" if player.get("trending") else "—"

    # Position-specific raw stats
    pos = player.get("position", "")
    stat_rows = []
    if pos == "QB":
        stat_rows = [
            ("Passing Yds/G", f"{player.get('passing_yards_pg', 0):.1f}"),
            ("Rush Yds/G",    f"{player.get('rush_yards_pg', 0):.1f}"),
            ("Pass TDs/G",    f"{player.get('pass_tds_pg', 0):.2f}"),
            ("INTs/G",        f"{player.get('interceptions_pg', 0):.2f}"),
        ]
    elif pos == "RB":
        stat_rows = [
            ("Rush Yds/G",    f"{player.get('rush_yards_pg', 0):.1f}"),
            ("Rush TDs/G",    f"{player.get('rush_tds_pg', 0):.2f}"),
            ("Rec Yds/G",     f"{player.get('receiving_yards_pg', 0):.1f}"),
            ("Rec TDs/G",     f"{player.get('recv_tds_pg', 0):.2f}"),
        ]
    elif pos in ("WR", "TE"):
        stat_rows = [
            ("Rec Yds/G",     f"{player.get('receiving_yards_pg', 0):.1f}"),
            ("Rec TDs/G",     f"{player.get('recv_tds_pg', 0):.2f}"),
        ]
    elif pos == "DEF":
        stat_rows = [
            ("Sacks/G",       f"{player.get('sacks_pg', 0):.2f}"),
            ("Tackles/G",     f"{player.get('tackles_pg', 0):.1f}"),
        ]

    def _stat(label, value):
        return html.Div([
            html.Span(f"{label}: ", style={"color": _TEXT_SEC, "fontSize": "12px"}),
            html.Span(value, style={"color": _TEXT, "fontWeight": "600", "fontSize": "12px"}),
        ], style={"marginBottom": "4px"})

    return dbc.Card(
        dbc.CardBody([
            dbc.Row([
                # Identity
                dbc.Col([
                    html.H4(player.get("player_name", ""), style={"color": _TEXT, "marginBottom": "4px"}),
                    html.H6(f"{player.get('team', '')} · {pos}",
                            style={"color": _TEXT_SEC, "marginBottom": "8px"}),
                    dbc.Badge(hype_label, style={"backgroundColor": hype_color,
                                                  "fontSize": "11px", "padding": "4px 10px"}),
                ], width=3),

                # Scores
                dbc.Col([
                    html.P("Fan Metrics", style={"color": _ACCENT, "fontWeight": "600",
                                                  "fontSize": "11px", "textTransform": "uppercase",
                                                  "letterSpacing": "0.08em", "marginBottom": "8px"}),
                    _stat("Performance Score", f"{player.get('performance_score', 0):.1f} / 100"),
                    _stat("Sentiment Score",   f"{player.get('sentiment_score', 0):+.3f}"),
                    _stat("Buzz Score",        f"{player.get('buzz_score', 0):.0f} / 100"),
                    _stat("Trending",          trending_icon),
                ], width=3),

                # Rankings
                dbc.Col([
                    html.P("Rankings", style={"color": _ACCENT, "fontWeight": "600",
                                              "fontSize": "11px", "textTransform": "uppercase",
                                              "letterSpacing": "0.08em", "marginBottom": "8px"}),
                    _stat("Performance Rank", f"#{player.get('performance_rank', '—')}"),
                    _stat("Sentiment Rank",   f"#{player.get('sentiment_rank', '—')}"),
                    _stat("Hype Index",       f"{player.get('hype_index', 0):+d}"),
                ], width=3),

                # Raw stats
                dbc.Col([
                    html.P("Raw Stats (per game)", style={
                        "color": _ACCENT, "fontWeight": "600", "fontSize": "11px",
                        "textTransform": "uppercase", "letterSpacing": "0.08em", "marginBottom": "8px",
                    }),
                    *[_stat(lbl, val) for lbl, val in stat_rows],
                ], width=3),
            ]),
        ]),
        className="player-detail-card",
        style={"backgroundColor": _CARD_BG, "border": f"1px solid {hype_color}",
               "borderRadius": "8px"},
    )


def make_leaderboard_style_conditions(df: pd.DataFrame) -> list:
    """Generate style_data_conditional for color-coded Hype Index cells."""
    conditions = []
    if df.empty:
        return conditions
    for _, row in df.iterrows():
        conditions.append({
            "if": {
                "filter_query": f'{{player_id}} = "{row["player_id"]}"',
                "column_id": "hype_index",
            },
            "backgroundColor": row["hype_color"],
            "color": "#FFFFFF",
            "fontWeight": "700",
        })
    return conditions
