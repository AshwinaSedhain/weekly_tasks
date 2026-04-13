import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc
import plotly.express as px
import polars as pl

# Importing the  functions from data engine 
from data_engine import load_and_clean_data, get_countries

# Loading  and cleaning the  dataset when app starts
df = load_and_clean_data("wfp_food_prices_database.csv")

#  It Gets the  list of countries for dropdown menu
countries = get_countries(df)

# Creating the  Dash application and apply Bootstrap theme for styling
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.LUX])


# Defifning the page layout 
app.layout = dbc.Container([

    # Setting the title of dashboard
    dbc.Row([
        dbc.Col(html.H1("Food Price Dashboard",
                        className="text-center my-4"))
    ]),

    # Row for filters (dropdowns)
    dbc.Row([

        # Country dropdown
        dbc.Col([
            html.Label("Country"),
            dcc.Dropdown(
                id="country-dropdown",
                options=[{"label": c, "value": c} for c in countries],
                value=countries[0] if countries else None
            )
        ], width=3),

        # Commodity dropdown (filled later dynamically)
        dbc.Col([
            html.Label("Commodity"),
            dcc.Dropdown(id="commodity-dropdown")
        ], width=3),

        # Market dropdown (allows multiple selection)
        dbc.Col([
            html.Label("Market"),
            dcc.Dropdown(id="market-dropdown", multi=True)
        ], width=3),

        # View dropdown (controls type of chart)
        dbc.Col([
            html.Label("View"),
            dcc.Dropdown(
                id="view-dropdown",
                options=[
                    {"label": "Time Series", "value": "time"},
                    {"label": "Market Comparison", "value": "market"},
                    {"label": "Distribution", "value": "dist"}
                ],
                value="time"
            )
        ], width=3),

    ], className="mb-4"),

    # Graph area where chart will be shown
    dbc.Row([
        dbc.Col(dcc.Loading(dcc.Graph(id="main-graph")))
    ])

], fluid=True)


# -----------------------
# CALLBACK 1: UPDATE COMMODITIES
# -----------------------

@app.callback(
    Output("commodity-dropdown", "options"),
    Output("commodity-dropdown", "value"),
    Input("country-dropdown", "value")
)
def update_commodities(country):

    # Filter data for selected country only
    dff = df.filter(pl.col("adm0_name") == country)

    # Get unique commodity names
    commodities = sorted(dff["cm_name"].unique().to_list())

    # Convert into dropdown format
    options = [{"label": c, "value": c} for c in commodities]

    # Auto-select first commodity if available
    value = commodities[0] if commodities else None

    return options, value


# -----------------------
# CALLBACK 2: UPDATE MARKETS
# -----------------------

@app.callback(
    Output("market-dropdown", "options"),
    Output("market-dropdown", "value"),
    Input("country-dropdown", "value"),
    Input("commodity-dropdown", "value")
)
def update_markets(country, commodity):

    # Filter dataset step by step
    dff = df.filter(
        (pl.col("adm0_name") == country) &
        (pl.col("cm_name") == commodity)
    )

    # Get unique market names
    markets = sorted(dff["mkt_name"].unique().to_list())

    # Format for dropdown
    options = [{"label": m, "value": m} for m in markets]

    # Auto-select first market if exists
    value = markets[:1] if markets else None

    return options, value


# -----------------------
# CALLBACK 3: UPDATE GRAPH
# -----------------------

@app.callback(
    Output("main-graph", "figure"),
    Input("country-dropdown", "value"),
    Input("commodity-dropdown", "value"),
    Input("market-dropdown", "value"),
    Input("view-dropdown", "value")
)
def update_graph(country, commodity, markets, view):

    # If user has not selected everything, show empty graph
    if not country or not commodity or not markets:
        return px.scatter(title="Please select all filters")

    # Filter data based on user selection
    dff = df.filter(
        (pl.col("adm0_name") == country) &
        (pl.col("cm_name") == commodity) &
        (pl.col("mkt_name").is_in(markets))
    )

    # If no data found, show message
    if dff.is_empty():
        return px.scatter(title="No data available")

    # Convert Polars to Pandas (needed for Plotly)
    pdf = dff.to_pandas()

    # -----------------------
    # Choose graph type
    # -----------------------

    # Time series graph
    if view == "time":
        fig = px.line(
            pdf,
            x="date",
            y="mp_price",
            color="mkt_name",
            title="Price Over Time"
        )

    # Market comparison graph
    elif view == "market":
        fig = px.box(
            pdf,
            x="mkt_name",
            y="mp_price",
            title="Market Comparison"
        )

    # Distribution graph
    else:
        fig = px.histogram(
            pdf,
            x="mp_price",
            title="Price Distribution"
        )

    return fig


# -----------------------
# RUN APP
# -----------------------

if __name__ == "__main__":
    app.run(debug=True)