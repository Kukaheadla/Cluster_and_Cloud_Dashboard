from dash import Dash, html, dcc, Input, Output, dash_table
import plotly.express as px
import pandas as pd
from io import StringIO


def init_dashboard(server):
    """Create a Plotly Dash dashboard."""
    dash_app = Dash(
        server=server,
        routes_pathname_prefix="/dashapp/",
        external_stylesheets=[
            "/static/style.css",
        ],
    )

    # Create Dash Layout
    # dash_app.layout = html.Div(id="dash-container")

    dash_app.layout = html.Div(
        children=[
            dcc.Location(id="url", refresh=False),
            html.H1(
                children="Livability in Melbourne - Cluster and Cloud Computing - Assignment 2"
            ),
            html.Nav(
                children=[
                    dcc.Link("🔭 Dashboard", href="/"),
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
            html.Div(id="my-output")
        ]
    )

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


f = """State,Number of Solar Plants,Installed Capacity (MW),Average MW Per Plant,Generation (GWh)
California,289,4395,15.3,10826
Arizona,48,1078,22.5,2550
Nevada,11,238,21.6,557
New Mexico,33,261,7.9,590
Colorado,20,118,5.9,235
Texas,12,187,15.6,354
North Carolina,148,669,4.5,1162
New York,13,53,4.1,84"""
g = []


def get_data():
    df = pd.read_csv(StringIO(f))
    return df


def test_table():
    y = get_data()
    return [
        html.P(
            "A list of the most recent tweets, dynamically updated if the harvester is working."
        ),
        html.Table(id="live-update-text"),
        dcc.Interval("interval-component", interval=1 * 2000, n_intervals=0),
        dash_table.DataTable(
            y.to_dict("records"), [{"name": i, "id": i} for i in get_data().columns]
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
        Output("live-update-text", "children"),
        Input("interval-component", "n_intervals"),
    )
    def update_metrics(n):
        global g
        g.append(html.Tr(html.Td("California,289,4395,15.3,10826\n")))
        return g

    @dash_app.callback(Output("graph", "figure"), Input("candidate", "value"))
    def display_choropleth(candidate):
        df = px.data.election()  # replace with your own data source
        geojson = px.data.election_geojson()
        fig = px.choropleth(
            df,
            geojson=geojson,
            color=candidate,
            locations="district",
            featureidkey="properties.district",
            projection="mercator",
            range_color=[0, 6500],
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
