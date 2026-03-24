"""
NFL Hype Index Dashboard — Application Entry Point.

Initialises the Dash app, defines the full layout, and registers callbacks.
Run directly for development:  python app/app.py
Served via Gunicorn in Docker: gunicorn app.app:server --bind 0.0.0.0:8050
"""

import yaml
import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, dash_table

# Load configuration
with open("config/settings.yaml") as f:
    CFG = yaml.safe_load(f)

C = CFG["colors"]
POSITIONS = CFG["positions"]
HYPE_CATS = CFG["hype_categories"]
REFRESH_MS = CFG["app"]["refresh_interval_ms"]

# ── Dash app initialisation ──────────────────────────────────────────────────
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.CYBORG],
    suppress_callback_exceptions=True,
    title=CFG["app"]["title"],
)
server = app.server  # Gunicorn entry point


# ── Helper: legend chip ──────────────────────────────────────────────────────
def _legend_chip(label: str, color: str) -> html.Div:
    return html.Div(
        [
            html.Span(style={"background": color, "width": "12px", "height": "12px",
                             "borderRadius": "2px", "display": "inline-block",
                             "marginRight": "6px", "flexShrink": "0"}),
            html.Span(label, style={"fontSize": "11px", "color": C["text_secondary"]}),
        ],
        style={"display": "flex", "alignItems": "center", "marginBottom": "4px"},
    )


# ── Sidebar ──────────────────────────────────────────────────────────────────
sidebar = html.Div(
    [
        html.H5("Filters", style={"color": C["text_primary"], "marginBottom": "16px",
                                  "fontWeight": "600"}),
        html.Label("Position", className="filter-label"),
        dcc.Dropdown(
            id="filter-position",
            options=[{"label": p, "value": p} for p in POSITIONS],
            value="ALL",
            clearable=False,
            className="mb-3",
        ),
        html.Label("Team", className="filter-label"),
        dcc.Dropdown(
            id="filter-team",
            options=[{"label": "ALL", "value": "ALL"}],
            value="ALL",
            clearable=False,
            className="mb-3",
        ),
        html.Label("Hype Category", className="filter-label"),
        dcc.Dropdown(
            id="filter-hype-category",
            options=[{"label": h, "value": h} for h in HYPE_CATS],
            value="ALL",
            clearable=False,
            className="mb-4",
        ),
        html.Hr(style={"borderColor": C["border"]}),
        html.H6("Hype Legend", style={"color": C["text_secondary"], "fontSize": "11px",
                                       "textTransform": "uppercase", "letterSpacing": "0.08em",
                                       "marginBottom": "10px"}),
        _legend_chip("Significantly Overhyped", C["significantly_overhyped"]),
        _legend_chip("Overhyped", C["overhyped"]),
        _legend_chip("Fair Value", C["fair_value"]),
        _legend_chip("Underrated", C["underrated"]),
        _legend_chip("Significantly Underrated", C["significantly_underrated"]),
    ],
    className="filter-card",
)

# ── Leaderboard table ────────────────────────────────────────────────────────
TABLE_COLS = [
    {"id": "display_rank",        "name": "#",              "type": "numeric"},
    {"id": "player_name",         "name": "Player",         "type": "text"},
    {"id": "team",                "name": "Team",           "type": "text"},
    {"id": "position",            "name": "Pos",            "type": "text"},
    {"id": "performance_score",   "name": "Perf. Score",    "type": "numeric"},
    {"id": "sentiment_score",     "name": "Sentiment",      "type": "numeric"},
    {"id": "buzz_score",          "name": "Buzz",           "type": "numeric"},
    {"id": "trending",            "name": "Trending",       "type": "text"},
    {"id": "hype_index",          "name": "Hype Index",     "type": "numeric"},
    {"id": "hype_label",          "name": "Category",       "type": "text"},
]

leaderboard = html.Div(
    [
        html.H5("Player Rankings", style={"color": C["text_primary"], "marginBottom": "12px",
                                           "fontWeight": "600"}),
        dash_table.DataTable(
            id="leaderboard-table",
            columns=TABLE_COLS,
            data=[],
            page_size=20,
            sort_action="native",
            filter_action="native",
            style_as_list_view=True,
            row_selectable="single",
            style_table={"overflowX": "auto"},
            style_header={
                "backgroundColor": C["card_background"],
                "color": C["accent"],
                "fontWeight": "600",
                "fontSize": "12px",
                "textTransform": "uppercase",
                "letterSpacing": "0.06em",
                "borderBottom": f"1px solid {C['border']}",
            },
            style_cell={
                "backgroundColor": C["card_background"],
                "color": C["text_primary"],
                "border": f"1px solid {C['border']}",
                "fontSize": "13px",
                "padding": "8px 12px",
                "textAlign": "left",
                "whiteSpace": "normal",
            },
            style_cell_conditional=[
                {"if": {"column_id": "display_rank"},      "width": "45px",  "textAlign": "center"},
                {"if": {"column_id": "team"},               "width": "55px",  "textAlign": "center"},
                {"if": {"column_id": "position"},           "width": "50px",  "textAlign": "center"},
                {"if": {"column_id": "performance_score"},  "width": "110px", "textAlign": "right"},
                {"if": {"column_id": "sentiment_score"},    "width": "100px", "textAlign": "right"},
                {"if": {"column_id": "buzz_score"},         "width": "70px",  "textAlign": "right"},
                {"if": {"column_id": "trending"},           "width": "80px",  "textAlign": "center"},
                {"if": {"column_id": "hype_index"},         "width": "100px", "textAlign": "right"},
            ],
            style_data_conditional=[],
            filter_query="",
        ),
    ],
    className="stat-card",
    style={"padding": "16px"},
)

# ── Main layout ──────────────────────────────────────────────────────────────
app.layout = dbc.Container(
    fluid=True,
    style={"backgroundColor": C["background"], "minHeight": "100vh", "padding": "0"},
    children=[
        # Hidden state components
        dcc.Interval(id="refresh-interval", interval=REFRESH_MS, n_intervals=0),
        dcc.Store(id="refresh-tick", data=0),
        dcc.Store(id="selected-player", data=None),

        # Header
        dbc.Row(
            dbc.Col(
                html.Div(
                    [
                        html.H1(
                            [html.Span("NFL ", style={"color": C["accent"]}),
                             "Hype Index"],
                            style={"margin": "0", "fontWeight": "700",
                                   "color": C["text_primary"], "fontSize": "28px"},
                        ),
                        html.P(
                            id="last-updated",
                            style={"margin": "0", "color": C["text_secondary"],
                                   "fontSize": "12px"},
                        ),
                    ],
                    style={"padding": "20px 24px 16px"},
                ),
            ),
            style={"borderBottom": f"1px solid {C['border']}",
                   "backgroundColor": C["card_background"]},
        ),

        # Main content
        dbc.Row(
            [
                # Sidebar
                dbc.Col(sidebar, width=2,
                        style={"padding": "16px", "borderRight": f"1px solid {C['border']}",
                               "minHeight": "calc(100vh - 70px)"}),

                # Main panel
                dbc.Col(
                    [
                        # Leaderboard
                        dbc.Row(dbc.Col(leaderboard, width=12), className="mb-3",
                                style={"padding": "16px 16px 0"}),

                        # Charts row
                        dbc.Row(
                            [
                                dbc.Col(
                                    html.Div(
                                        dcc.Graph(id="scatter-plot", config={"displayModeBar": False}),
                                        className="stat-card",
                                    ),
                                    width=6,
                                ),
                                dbc.Col(
                                    html.Div(
                                        dcc.Graph(id="hype-bar-chart", config={"displayModeBar": False}),
                                        className="stat-card",
                                    ),
                                    width=6,
                                ),
                            ],
                            className="mb-3",
                            style={"padding": "0 16px"},
                        ),

                        # Player detail card (hidden until row clicked)
                        dbc.Row(
                            dbc.Col(
                                html.Div(id="player-detail-card"),
                                width=12,
                            ),
                            style={"padding": "0 16px 16px"},
                        ),
                    ],
                    width=10,
                ),
            ],
            style={"margin": "0"},
        ),
    ],
)

# Register callbacks (side-effect import)
import app.callbacks  # noqa: E402, F401

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=CFG["app"]["port"])
