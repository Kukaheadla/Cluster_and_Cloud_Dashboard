"""
This file contains the Dash https://plotly.com/dash/ initialisation code.
It also contains the functions related to rendering the graphs, and
the callbacks implemented to update graphs in response to user input
or in response to any other defined trigger.
"""
from dash import Dash, html, dcc, Input, Output, dash_table
import plotly.express as px
import pandas as pd
from io import StringIO
from helpers import get_latest_tweets
from client_api import get_tweet_n
import re
import melbourne
import random


def init_dashboard(server):
    """Create a Plotly Dash dashboard."""

    # dash application config
    dash_app = Dash(
        server=server,
        routes_pathname_prefix="/dashapp/",
        external_stylesheets=[
            "/static/style.css",
        ],
    )

    # dash application initial layout
    dash_app.layout = html.Div(
        id="dash-container",
        children=[
            dcc.Location(id="url", refresh=False),
            html.H1(
                children="Livability in Melbourne - Cluster and Cloud Computing - Assignment 2"
            ),
            html.Nav(
                children=[
                    dcc.Link("🔭 Dashboard TEST2", href="/"),
                    dcc.Link("✇ Recent Tweets", href="/recent_tweet_list"),
                    dcc.Link("📽 About", href="/about"),
                    html.Img(
                        height=120,
                        src="https://d2glwx35mhbfwf.cloudfront.net/v13.0.0/logo-with-padding.svg",
                    ),
                ]
            ),
            html.Div(id="page-content"),
            html.Div(["Input: ", dcc.Input(id="my-input", value="", type="text")]),
            html.Div(id="my-output"),
        ],
    )

    # only register callbacks after app is initialised
    register_callbacks(dash_app)

    return dash_app.server


def test():
    df = pd.DataFrame(
        {
            "Fruit": ["Apples", "Oranges", "Bananas", "Apples", "Oranges", "Bananas"],
            "Amount": [4, 1, 2, 2, 4, 5],
            "City": ["SF", "SF", "SF", "Montreal", "Montreal", "Montreal"],
        }
    )

    fig = px.bar(df, x="Fruit", y="Amount", color="City", barmode="group")
    return dcc.Graph(id="example-graph", figure=fig)


def get_data():
    """
    Gets some of the latest tweets added to the database.
    """
    latest_tweets = get_latest_tweets()
    csv_acc = "id,content,time_created\n"
    for tweet in latest_tweets["results"]:
        my_tweet = get_tweet_n(tweet["id"])
        v = re.sub('"', "", my_tweet["key"]["doc"]["text"])
        csv_acc = (
            csv_acc + f"{tweet['id']},\"{v}\",{my_tweet['key']['created_at_epoch']}\n"
        )
    df = pd.read_csv(StringIO(csv_acc))
    x = df.to_dict("records")
    return (x, [{"name": i, "id": i} for i in df.columns])


def test_table():
    y = get_data()
    return [
        html.P(
            "A list of the most recent tweets, dynamically updated if the harvester is running."
        ),
        html.Table(id="live-update-text"),
        dcc.Interval("interval-component", interval=1 * 5000, n_intervals=0),
        dash_table.DataTable(
            get_data()[0], get_data()[1], id="t1", style_cell={"textAlign": "left"}
        ),
    ]


def dashboard():
    return [
        html.H2(children="Dashboard"),
        dcc.RadioItems(
            id="candidate",
            options=["Joly", "Coderre", "Bergeron"],
            value="Coderre",
            inline=True,
        ),
        dcc.Graph(id="graph"),
        test(),
    ]


def register_callbacks(dash_app):
    @dash_app.callback(
        Output("t1", "data"),
        Input("interval-component", "n_intervals"),
    )
    def update_metrics(n):
        return get_data()[0]

    @dash_app.callback(Output("graph", "figure"), Input("candidate", "value"))
    def display_choropleth(candidate):
        df = px.data.election()  # replace with your own data source
        details = {
            "name": ["Cremorne"],
            "Coderre": [2300],
            "total": [9000],
            "cartodb_id": [31],
        }

        # do some hacking around to produce a map of melbourne with hardcoded data
        geojson = px.data.election_geojson()
        geojson = melbourne.melbourne_geo()
        for thing in geojson["features"]:
            if thing["properties"]["name"] not in details["name"]:
                details["name"] = details["name"] + [thing["properties"]["name"]]
                details["cartodb_id"] = details["cartodb_id"] + [
                    thing["properties"]["cartodb_id"]
                ]
        details["Coderre"] = details["Coderre"] * len(details["name"])
        details["total"] = details["total"] * len(details["name"])
        for i in range(len(details["total"]) - 1):
            details["Coderre"][i] = random.randrange(100, 15000, 1000)

        df = pd.DataFrame(details)
        # print(geojson)
        fig = px.choropleth(
            df,
            geojson=geojson,
            color=candidate,
            locations="name",
            featureidkey="properties.name",
            projection="mercator",
            range_color=[0, 15500],
            height=700,
        )
        fig.update_geos(fitbounds="locations", visible=False)
        fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
        return fig

    @dash_app.callback(
        Output(component_id="my-output", component_property="children"),
        Input(component_id="my-input", component_property="value"),
    )
    def update_output_div(input_value):
        return f"Output: {input_value}"

    @dash_app.callback(Output("page-content", "children"), [Input("url", "pathname")])
    def display_page(pathname):
        if pathname == "/recent_tweet_list":
            return test_table()
        if pathname == "/dashapp/" or pathname == "/":
            return dashboard()
