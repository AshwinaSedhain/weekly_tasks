# This file is the main Dash application. It is defining the layout and registering
# all callbacks that fetch data from the FastAPI backend and update the charts every
# 30 seconds. The dashboard shows a live news feed, sentiment distribution, trending
# keywords, source distribution, and system health metrics at the top.

import logging
import os
from collections import defaultdict

import requests
import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output
import plotly.graph_objects as go

logger = logging.getLogger(__name__)

API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000")


def _card_style() -> dict:
    # Returning a shared CSS style dictionary for the dashboard cards so all
    # panels have a consistent white rounded look with a subtle shadow.
    return {
        "backgroundColor": "white",
        "borderRadius": "8px",
        "padding": "20px",
        "boxShadow": "0 2px 4px rgba(0,0,0,0.1)",
    }


def _safe_get(url: str) -> dict:
    # Making a GET request to the API and returning the parsed JSON. Returning
    # an empty dictionary when the request fails so callbacks handle missing
    # data gracefully without crashing the dashboard.
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        return response.json()
    except Exception as exc:
        logger.warning("API request to %s failing: %s", url, exc)
        return {}


app = dash.Dash(
    __name__,
    title="News Analytics Dashboard",
    update_title=None,
)

app.layout = html.Div(
    style={"fontFamily": "Arial, sans-serif", "backgroundColor": "#f4f6f9", "padding": "20px"},
    children=[
        html.H1(
            "Real-Time News Analytics Dashboard",
            style={"textAlign": "center", "color": "#2c3e50"},
        ),

        # This interval component triggers all callbacks every 30 seconds so
        # the dashboard refreshes automatically without the user doing anything.
        dcc.Interval(id="refresh-interval", interval=30_000, n_intervals=0),

        # Top row showing three summary metric cards.
        html.Div(
            style={"display": "grid", "gridTemplateColumns": "1fr 1fr 1fr", "gap": "20px"},
            children=[
                html.Div(
                    id="card-total",
                    style=_card_style(),
                    children=[html.H3("Total Articles"), html.H2(id="metric-total", children="...")],
                ),
                html.Div(
                    id="card-today",
                    style=_card_style(),
                    children=[html.H3("Articles Today"), html.H2(id="metric-today", children="...")],
                ),
                html.Div(
                    id="card-uptime",
                    style=_card_style(),
                    children=[html.H3("API Uptime (s)"), html.H2(id="metric-uptime", children="...")],
                ),
            ],
        ),

        # Middle row showing sentiment pie chart and trending keywords bar chart.
        html.Div(
            style={"display": "grid", "gridTemplateColumns": "1fr 1fr", "gap": "20px", "marginTop": "20px"},
            children=[
                html.Div(
                    style=_card_style(),
                    children=[
                        html.H3("Sentiment Distribution"),
                        dcc.Graph(id="sentiment-chart"),
                    ],
                ),
                html.Div(
                    style=_card_style(),
                    children=[
                        html.H3("Trending Keywords"),
                        dcc.Graph(id="trending-chart"),
                    ],
                ),
            ],
        ),

        # Source distribution bar chart showing articles per data source.
        html.Div(
            style={"marginTop": "20px", **_card_style()},
            children=[
                html.H3("Source Distribution"),
                dcc.Graph(id="source-chart"),
            ],
        ),

        # News feed table showing the latest articles with colour coding.
        html.Div(
            style={"marginTop": "20px", **_card_style()},
            children=[
                html.H3("Latest News Feed"),
                dash_table.DataTable(
                    id="news-table",
                    columns=[
                        {"name": "Title", "id": "title"},
                        {"name": "Publisher", "id": "source_name"},
                        {"name": "Data Source", "id": "source"},
                        {"name": "Sentiment", "id": "sentiment_label"},
                        {"name": "Published", "id": "published_at"},
                    ],
                    style_table={"overflowX": "auto"},
                    style_cell={"textAlign": "left", "padding": "8px", "fontSize": "13px"},
                    style_header={
                        "backgroundColor": "#2c3e50",
                        "color": "white",
                        "fontWeight": "bold",
                    },
                    # Highlighting positive articles green and negative articles red.
                    style_data_conditional=[
                        {
                            "if": {"filter_query": '{sentiment_label} = "positive"'},
                            "backgroundColor": "#d5f5e3",
                        },
                        {
                            "if": {"filter_query": '{sentiment_label} = "negative"'},
                            "backgroundColor": "#fadbd8",
                        },
                    ],
                    page_size=15,
                ),
            ],
        ),
    ],
)


@app.callback(
    Output("metric-total", "children"),
    Output("metric-today", "children"),
    Output("metric-uptime", "children"),
    Input("refresh-interval", "n_intervals"),
)
def update_metrics(n: int):
    # Fetching live metrics from the API and updating the three summary cards
    # at the top of the dashboard.
    data = _safe_get(f"{API_BASE}/metrics/live")
    total = data.get("total_articles", "N/A")
    today = data.get("articles_today", "N/A")
    uptime = data.get("uptime_seconds", "N/A")
    return total, today, uptime


@app.callback(
    Output("sentiment-chart", "figure"),
    Input("refresh-interval", "n_intervals"),
)
def update_sentiment(n: int):
    # Fetching the sentiment summary and rendering a pie chart showing the
    # proportion of positive, negative, and neutral articles.
    data = _safe_get(f"{API_BASE}/analytics/sentiment")
    sentiment = data.get("sentiment", {})
    if not sentiment:
        return go.Figure()
    labels = list(sentiment.keys())
    values = list(sentiment.values())
    colors = {"positive": "#2ecc71", "negative": "#e74c3c", "neutral": "#95a5a6"}
    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        marker_colors=[colors.get(label, "#3498db") for label in labels],
    )])
    fig.update_layout(margin=dict(t=10, b=10, l=10, r=10))
    return fig


@app.callback(
    Output("trending-chart", "figure"),
    Input("refresh-interval", "n_intervals"),
)
def update_trending(n: int):
    # Fetching the trending keywords and rendering a horizontal bar chart
    # sorted by frequency score.
    data = _safe_get(f"{API_BASE}/analytics/trends")
    trending = data.get("trending", [])
    if not trending:
        return go.Figure()
    keywords = [t["keyword"] for t in trending[:15]]
    scores = [t["trend_score"] for t in trending[:15]]
    fig = go.Figure(go.Bar(
        x=scores,
        y=keywords,
        orientation="h",
        marker_color="#3498db",
    ))
    fig.update_layout(
        yaxis={"autorange": "reversed"},
        margin=dict(t=10, b=10, l=10, r=10),
    )
    return fig


@app.callback(
    Output("source-chart", "figure"),
    Input("refresh-interval", "n_intervals"),
)
def update_sources(n: int):
    # Fetching the source distribution and rendering a bar chart showing how
    # many articles came from each data source.
    data = _safe_get(f"{API_BASE}/analytics/sources")
    sources = data.get("sources", {})
    if not sources:
        return go.Figure()
    fig = go.Figure(go.Bar(
        x=list(sources.keys()),
        y=list(sources.values()),
        marker_color="#9b59b6",
    ))
    fig.update_layout(margin=dict(t=10, b=10, l=10, r=10))
    return fig


@app.callback(
    Output("news-table", "data"),
    Input("refresh-interval", "n_intervals"),
)
def update_news_table(n: int):
    # Fetching the latest 60 articles and interleaving them by source so all
    # three sources appear in the table rather than just the most recently
    # collected source dominating all rows.
    data = _safe_get(f"{API_BASE}/news/latest?limit=60")
    articles = data.get("articles", [])

    by_source: dict = defaultdict(list)
    for a in articles:
        by_source[a.get("source", "unknown")].append(a)

    interleaved = []
    sources = list(by_source.values())
    max_len = max((len(s) for s in sources), default=0)
    for i in range(max_len):
        for source_list in sources:
            if i < len(source_list):
                interleaved.append(source_list[i])

    return [
        {
            "title": a.get("title", ""),
            "source_name": a.get("source_name", ""),
            "source": a.get("source", "").replace("newsapi_headlines", "NewsAPI Headlines")
                                          .replace("newsapi_everything", "NewsAPI Everything")
                                          .replace("hackernews", "Hacker News"),
            "sentiment_label": a.get("sentiment_label", ""),
            "published_at": a.get("published_at", "")[:10] if a.get("published_at") else "",
        }
        for a in interleaved[:50]
    ]


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    app.run(debug=False, host="0.0.0.0", port=8050)
