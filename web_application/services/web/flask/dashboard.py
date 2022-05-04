"""
This file contains the Dash https://plotly.com/dash/ initialisation code.
It also contains the functions related to rendering the graphs, and
the callbacks implemented to update graphs in response to user input
or in response to any other defined trigger.

Initial author: Alex 

The functions you can expect to find here relate to rendering (at a high level, i.e. declaratively)
the dashboard components. All dashboard items will result in queries to the CouchDB database,
so you must be mindful of any performance issues with doing is. If necessary, 'hide' your function
behind a user interaction such as navigating to a specific page.
"""
from dash import Dash, html, dcc, Input, Output, dash_table
import plotly.express as px
import plotly.graph_objs as go
import pandas as pd
from io import StringIO
from helpers import get_latest_tweets
from client_api import get_tweet_n, get_languages_by_time_view
import re
import melbourne
import random

df = None

def init_dashboard(server):
    """Create a Plotly Dash dashboard."""

    # dash application config
    dash_app = Dash(
        server=server,
        routes_pathname_prefix="/dashapp/",
        external_stylesheets=[
            "https://codepen.io/chriddyp/pen/bWLwgP.css",
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
                    dcc.Link("🌎 Dashboard", href="/"),
                    dcc.Link("✇ Recent Tweets", href="/recent_tweet_list"),
                    dcc.Link("📽 About", href="/about"),
                    html.Img(
                        height=120,
                        src="https://d2glwx35mhbfwf.cloudfront.net/v13.0.0/logo-with-padding.svg",
                    ),
                ]
            ),
            html.Div(id="page-content"),
        ],
    )

    # only register callbacks after app is initialised
    register_callbacks(dash_app)

    return dash_app.server




def language_frequency_graph(data):
    """
    Displays a language frequency stacked bar chart.
    """
    dates = []
    amounts = []
    languages = []
    for date, lang_date_frequencies in dict(data).items():
        dates = dates + ([date] * (len(lang_date_frequencies) - 1))
        for key1, val1 in dict(lang_date_frequencies).items():
            # remove undefined
            if key1 == "und":
                continue
            amounts.append(val1)
            languages.append(key1)

    df = pd.DataFrame(
        {
            "Month": dates,
            "Amount": amounts,
            "Language": languages,
        }
    )
    df["Normalised Frequency"] = df["Amount"] / df.groupby("Month")["Amount"].transform(
        "sum"
    )

    fig = px.bar(
        df,
        x="Month",
        y="Normalised Frequency",
        color="Language",
        barmode="stack",
        height=1000,
    )
    return dcc.Graph(id="example-graph", figure=fig)


def get_latest_tweet_data():
    """
    Gets some of the latest tweets added to the database.
    This is an example of reading data in a csv.
    """
    latest_tweets = get_latest_tweets()
    csv_acc = "id,content,time_created\n"
    for tweet in latest_tweets["results"]:
        try:
            parsed_tweet = get_tweet_n(tweet["id"])
            v = re.sub('"', "", parsed_tweet["doc"]["text"])
            csv_acc = (
                csv_acc + f"{tweet['id']},\"{v}\",{parsed_tweet['created_at_epoch']}\n"
            )
        except Exception:
            pass
    df = pd.read_csv(StringIO(csv_acc)).sort_values("id")
    return (df.to_dict("records"), [{"name": i, "id": i} for i in df.columns])


def recent_tweets_written_to_db_table():
    """
    Just a test to show the latest tweets in a table.
    """
    return [
        html.P(
            "A list of the most recent tweets, dynamically updated if the harvester is running."
        ),
        html.P(
            "This allows you to see that the database is being updated and also the kinds of tweets we are working with. Note that even when not updating sometimes the order may jump around a bit."
        ),
        html.Table(id="live-update-text"),
        dcc.Interval("interval-component", interval=1 * 5000, n_intervals=0),
        dash_table.DataTable(
            get_latest_tweet_data()[0],
            get_latest_tweet_data()[1],
            id="t1",
            style_cell={"textAlign": "left"},
        ),
    ]


def cross_compare():
    """
    Allows editing of variables for comparison.
    """

    global df

    my_csv = """Country Name,Indicator Name,day,Value
    Melbourne,"Distinct Languages",2016-01,2
    Melbourne,"Distinct Languages",2016-02,8
    Melbourne,"Distinct Languages",2016-03,16
    Melbourne,"Distinct Languages",2016-04,5
    Melbourne,"Distinct Languages",2016-05,7
    Melbourne,"Distinct Languages",2016-06,25
    Sydney,"Distinct Languages",2016-01,20
    """
    csv_acc = "Country Name,Indicator Name,day,Value\n"
    my_data = get_languages_by_time_view()


    # df = pd.read_csv('https://plotly.github.io/datasets/country_indicators.csv')
    df3 = pd.read_csv(StringIO(my_csv))
    # print(df)

    columns = ["Country Name", "Indicator Name", "day", "value"]

    df = pd.DataFrame(my_data).transpose().sum(axis=1)
    df = df.reset_index().rename_axis("index_test")
    df.columns = ["day", "Value"]
    df["Indicator Name"] = ["Tweets Total"] * 15
    df["Country Name"] = ["Melbourne"] * 15
    df = df.sort_values("day")

    df2 = pd.DataFrame(my_data).transpose().product(axis=1)
    df2 = df2.reset_index().rename_axis("index_test")
    df2.columns = ["day", "Value"]
    df2["Indicator Name"] = ["Tweets Total"] * 15
    df2["Country Name"] = ["Sydney"] * 15
    df2 = df2.sort_values("day")

    # df = pd.DataFrame(my_data)
    # df["Indicator Name"] = ["Distinct Languages"]
    # print(df)
    df = pd.concat([df, df2, df3])
    print(df)


    layout = html.Div([
        html.Div([

            html.Div([
                dcc.Dropdown(
                    df['Indicator Name'].unique(),
                    'Fertility rate, total (births per woman)',
                    id='crossfilter-xaxis-column',
                ),
                dcc.RadioItems(
                    ['Linear', 'Log'],
                    'Linear',
                    id='crossfilter-xaxis-type',
                    labelStyle={'display': 'inline-block', 'marginTop': '5px'}
                )
            ],
            style={'width': '49%', 'display': 'inline-block'}),

            html.Div([
                dcc.Dropdown(
                    df['Indicator Name'].unique(),
                    'Life expectancy at birth, total (years)',
                    id='crossfilter-yaxis-column'
                ),
                dcc.RadioItems(
                    ['Linear', 'Log'],
                    'Linear',
                    id='crossfilter-yaxis-type',
                    labelStyle={'display': 'inline-block', 'marginTop': '5px'}
                )
            ], style={'width': '49%', 'float': 'right', 'display': 'inline-block'})
        ], style={
            'padding': '10px 5px'
        }),

        html.Div([
            dcc.Graph(
                id='crossfilter-indicator-scatter',
                hoverData={'points': [{'customdata': 'Japan'}]}
            )
        ], style={'width': '49%', 'display': 'inline-block', 'padding': '0 20'}),
        html.Div([
            dcc.Graph(id='x-time-series'),
            dcc.Graph(id='y-time-series'),
        ], style={'display': 'inline-block', 'width': '49%'}),

        html.Div(dcc.Slider(
            df['day'].min(),
            df['day'].max(),
            step=None,
            id='crossfilter-year--slider',
            value=df['day'].max(),
            marks={str(year): str(year) for year in df['day'].unique()}
        ), style={'width': '49%', 'padding': '0px 20px 20px 20px'})
    ])
    return layout


def render_dashboard():
    """
    Main functions for the dashboard should go here (but not callbacks)
    """
    # experimenting with some couchdb graphing
    languages_by_date_view = (
        get_languages_by_time_view()
    )  # note that you can vary the grouping level in the couchDB query
    total_counts = []
    c = 0
    for val in dict(languages_by_date_view).values():
        for t in dict(val).values():
            c += t
        total_counts.append(c)
        c = 0

    sf = sorted(
        list(dict(languages_by_date_view).keys()),
        key=lambda x: (x.split("-")[0], int(x.split("-")[1])),
    )

    # 'scatterplot' but in reality the lines are joined so it looks like a line chart
    fig = go.Figure(data=[go.Scatter(x=sf, y=total_counts)])

    # return the children for the main render function
    return [
        html.H2(children="Main Dashboard"),
        cross_compare(),
        html.P("The following data is extracted from the CouchDB database."),
        html.H2("Figure 1. Language Frequencies grouped by Month in Database"),
        html.P(
            "Diversity of languages in Melbourne can be regarded as a proxy livability figure with respect to the desirability of the city (under a few key assumptions)."
            + "\nEnglish clearly dominates the language skyline of Melbourne across time (make sure to click the 'en' square in the legend to disable English and have a more interesting picture!)"
            + "\nHas this changed across the years? Do the most recent Tweets of 2022 show any difference in patterns?",
            style={"textAlign": "center"},
        ),
        language_frequency_graph(languages_by_date_view),
        html.H2("Figure 2. Tweet Frequencies grouped by Month in Database"),
        html.P(
            "Note that while each value is the range across the entire month, not just the month's first day."
        ),
        dcc.Graph(figure=fig),
        dcc.RadioItems(
            id="candidate",
            options=["Joly", "Coderre", "Bergeron"],
            value="Coderre",
            inline=True,
        ),
        dcc.Graph(id="graph"),
    ]


def register_callbacks(dash_app):
    """
    Register callbacks with application using decorators.

    A callback is a function called on some kind of interaction, where that could be a user action,
    the loading of a page, or an interval set by the runtime.
    """

    @dash_app.callback(
        Output("t1", "data"),
        Input("interval-component", "n_intervals"),
    )
    def update_metrics(n):
        return get_latest_tweet_data()[0]

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
        # todo: replace
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
            return recent_tweets_written_to_db_table()
        if pathname == "/dashapp/" or pathname == "/":
            return render_dashboard()

    @dash_app.callback(
        Output('crossfilter-indicator-scatter', 'figure'),
        Input('crossfilter-xaxis-column', 'value'),
        Input('crossfilter-yaxis-column', 'value'),
        Input('crossfilter-xaxis-type', 'value'),
        Input('crossfilter-yaxis-type', 'value'),
        Input('crossfilter-year--slider', 'value'))
    def update_graph(xaxis_column_name, yaxis_column_name,
                    xaxis_type, yaxis_type,
                    year_value):
        dff = df[df['day'] == year_value]

        fig = px.scatter(x=dff[dff['Indicator Name'] == xaxis_column_name]['Value'],
                y=dff[dff['Indicator Name'] == yaxis_column_name]['Value'],
                hover_name=dff[dff['Indicator Name'] == yaxis_column_name]['Country Name']
                )

        fig.update_traces(customdata=dff[dff['Indicator Name'] == yaxis_column_name]['Country Name'])

        fig.update_xaxes(title=xaxis_column_name, type='linear' if xaxis_type == 'Linear' else 'log')

        fig.update_yaxes(title=yaxis_column_name, type='linear' if yaxis_type == 'Linear' else 'log')

        fig.update_layout(margin={'l': 40, 'b': 40, 't': 10, 'r': 0}, hovermode='closest')

        return fig


    def create_time_series(dff, axis_type, title):

        fig = px.scatter(dff, x='day', y='Value')

        fig.update_traces(mode='lines+markers')

        fig.update_xaxes(showgrid=False)

        fig.update_yaxes(type='linear' if axis_type == 'Linear' else 'log')

        fig.add_annotation(x=0, y=0.85, xanchor='left', yanchor='bottom',
                        xref='paper', yref='paper', showarrow=False, align='left',
                        text=title)

        fig.update_layout(height=225, margin={'l': 20, 'b': 30, 'r': 10, 't': 10})

        return fig


    @dash_app.callback(
        Output('x-time-series', 'figure'),
        Input('crossfilter-indicator-scatter', 'hoverData'),
        Input('crossfilter-xaxis-column', 'value'),
        Input('crossfilter-xaxis-type', 'value'))
    def update_y_timeseries(hoverData, xaxis_column_name, axis_type):
        country_name = hoverData['points'][0]['customdata']
        dff = df[df['Country Name'] == country_name]
        dff = dff[dff['Indicator Name'] == xaxis_column_name]
        title = '<b>{}</b><br>{}'.format(country_name, xaxis_column_name)
        return create_time_series(dff, axis_type, title)


    @dash_app.callback(
        Output('y-time-series', 'figure'),
        Input('crossfilter-indicator-scatter', 'hoverData'),
        Input('crossfilter-yaxis-column', 'value'),
        Input('crossfilter-yaxis-type', 'value'))
    def update_x_timeseries(hoverData, yaxis_column_name, axis_type):
        dff = df[df['Country Name'] == hoverData['points'][0]['customdata']]
        dff = dff[dff['Indicator Name'] == yaxis_column_name]
        return create_time_series(dff, axis_type, yaxis_column_name)
