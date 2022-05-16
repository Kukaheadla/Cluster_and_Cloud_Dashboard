"""
This file contains the main rendering functions for the Dashboard.

Created by: Kevin Yang, Alex T

note: this was imported from a Jupyter notebook but required some modifications.
"""

# %% [markdown]
# ### Exploratory Data Analysis
# ensure `SA2_2021_AUST_SHP_GDA94` and `requirements.txt` are to the same directory as this Jupyter notebook file 
# 
# for linux command, run this beforehand:
# ```
# sudo apt-get install gdal-bin
# sudo apt-get install libgdal-dev
# 
# sudo apt install python-geopandas
# ```

# %%
#!pip install -r ./requirements.txt

# %%
import pandas as pd
import geopandas as gpd
import json
import pyproj
import plotly.express as px
import plotly.graph_objects as go
from jupyter_dash import JupyterDash
import os

from dash import Dash, html, dcc
from dash.dependencies import Input, Output

import couchdb

from datetime import datetime
from collections import defaultdict


def init_dashboard(server):


    app = Dash(
        server=server,
        routes_pathname_prefix="/dashapp/",
        external_stylesheets=[
            "https://codepen.io/chriddyp/pen/bWLwgP.css",
            "/static/style.css",
            "/static/dash_stylesheet.css"
        ],
    )

    MAPBOX_ACCESS_TOKEN="pk.eyJ1Ijoia3VrYWhlYWRsYSIsImEiOiJjbDJ5Mml5MHEweHlkM2tvNWxodm1najcwIn0.h1p7x_rboO1iqycGcogJFQ"

    # %% [markdown]
    # ### Exploratory Data Analysis for `Historical Tweets`

    # %%
    USER = 'user'
    PASSWORD = 'password'

    server = couchdb.Server('http://{}:{}@172.26.134.34:5984/'.format(USER, PASSWORD))

    # %%
    db = server['new_tweets']
    # envir_df = server['envir_test1']
    historical_tweet_db = server['historical_tweets']

    # %%
    # envir_db.view('area_week/area_week_topic')
    topic_agg = db.view('area_week/area_week_topic', include_doc=True)
    topic_df = pd.DataFrame((row.key+[row.value['sentiments']['compound']] for row in topic_agg),
                            columns = ['time', 'area', 'topic','sentiment'])

    # Aggregate by average sentiment 
    topic_df = topic_df.groupby(['time', 'area', 'topic']).mean().reset_index()

    #filter out wNaN 
    topic_df['week'] = topic_df.apply(lambda x: x['time'].split('-')[0], axis=1)
    topic_df = topic_df[topic_df['week'] != 'wNaN']

    #Change string to datetime format and filtering out non-valid string
    topic_df['time'] = topic_df.apply(lambda row: datetime.strptime(row['time']+'-1', 'w%W-%Y-%w'), axis=1) #append -1 as Monday
    topic_df = topic_df[topic_df['area'] != 'zzzzzzzzz'] 

    # print("topic_df Shape:", topic_df.shape)
    # topic_df.head()

    # %%
    sentiment_agg = db.view('sentiments/area_week_avg_compound', group_level=2, include_doc=True)
    sentiment_df = pd.DataFrame([row.key+row.value for row in sentiment_agg], 
                                columns=['time', 'area', 'sentiment', 'count'])

    # Remove NaN value
    sentiment_df['week'] = sentiment_df.apply(lambda x: x['time'].split('-')[0], axis=1)
    sentiment_df = sentiment_df[sentiment_df['week'] != 'wNaN']

    # Change string to datetime format
    sentiment_df['time'] = sentiment_df.apply(lambda row: datetime.strptime(row['time']+'-1', 'w%W-%Y-%w'), axis=1)

    # # Filter out only Melbourne and Sydney
    # sentiment_df = sentiment_df[(sentiment_df['area']== 'melbourne') | (sentiment_df['area'] == 'sydney')]

    #remove null_areas
    sentiment_df = sentiment_df[sentiment_df['area'] != 'zzzzzzzzz'] 

    # print("topic_df Shape:", sentiment_df.shape)
    # sentiment_df.head()

    # %%
    sa2_gdf = gpd.read_file("./SA2_2021_AUST_SHP_GDA94")
    sa2_gdf['SA2_NAME21'] = sa2_gdf['SA2_NAME21'].str.lower()
    sa2_gdf.to_crs(pyproj.CRS.from_epsg(4283), inplace=True)
    # sa2_gdf.head()

    # %%
    sa2_gdf_sent = sa2_gdf.copy()
    sentiment_geo_df = sentiment_df.merge(sa2_gdf_sent, left_on='area', right_on='SA2_NAME21', how='left')
    sentiment_gdf = gpd.GeoDataFrame(sentiment_geo_df, crs="EPSG:4283", geometry=sentiment_geo_df.geometry)
    # sentiment_gdf.head()

    # %%
    sentiment_overall_agg = sentiment_gdf.groupby(['GCC_NAME21']).sum().reset_index()
    # sentiment_overall_agg.head()

    # %%
    sentiment_overall_avg = sentiment_gdf.groupby([sentiment_gdf.time.dt.year, sentiment_gdf.GCC_NAME21]).mean().reset_index()
    # sentiment_overall_avg.head()

    # %%
    sentiment_overall_avg = sentiment_df.groupby([sentiment_gdf.time.dt.year, sentiment_gdf.GCC_NAME21]).mean().reset_index()
    melb_sentiment_now = sentiment_overall_avg.loc[
                            (sentiment_overall_avg['GCC_NAME21'] == 'Greater Melbourne') & (sentiment_overall_avg['time'] == datetime.now().year),
                            'sentiment'].item()
    syd_sentiment_now = sentiment_overall_avg.loc[
                            (sentiment_overall_avg['GCC_NAME21'] == 'Greater Sydney') & (sentiment_overall_avg['time'] == datetime.now().year),
                            'sentiment'].item()
    melb_sentiment_prev = sentiment_overall_avg.loc[
                            (sentiment_overall_avg['GCC_NAME21'] == 'Greater Melbourne') & (sentiment_overall_avg['time'] == datetime.now().year-1),
                            'sentiment'].item()
    syd_sentiment_prev = sentiment_overall_avg.loc[
                            (sentiment_overall_avg['GCC_NAME21'] == 'Greater Sydney') & (sentiment_overall_avg['time'] == datetime.now().year-1),
                            'sentiment'].item()
    #Overall Sentiment
    melb_sentiment_overall = sentiment_overall_avg.loc[
                            (sentiment_overall_avg['GCC_NAME21'] == 'Greater Melbourne'),
                            'sentiment'].mean()
    syd_sentiment_overall = sentiment_overall_avg.loc[
                            (sentiment_overall_avg['GCC_NAME21'] == 'Greater Sydney'),
                            'sentiment'].mean()

    # %%
    # topic_df.topic.unique()

    # %%
    pie_fig = px.pie(sentiment_overall_agg, values='count', 
                names='GCC_NAME21', 
                title='Sentiment Count by Area',
                color_discrete_sequence=px.colors.sequential.Peach,
                height=616,
                hole=0.4)
    pie_fig.update_layout(
                    margin={"r":0,"t":50,"l":0,"b":0},
                    paper_bgcolor='rgba(0,0,0,0)', 
                    plot_bgcolor='rgba(0,0,0,0)',
                    font_color='#FFFFFF')
    # pie_fig.show() #comment this out for flask app

    # %%
    indicator_fig = go.Figure()
    indicator_fig.add_trace(go.Indicator(
        mode = "number+delta",
        value = melb_sentiment_now,
        title = {"text": "Greater Melbourne<br> Avg. Sentiment Now<br><span style='font-size:0.8em;color:gray'>Compare to previous year</span>"},
        delta = {'reference': melb_sentiment_prev},
        domain = {'row': 0, 'column': 0}))
    indicator_fig.add_trace(go.Indicator(
        mode = "number+delta",
        value = syd_sentiment_now,
        delta = {'reference': syd_sentiment_prev},
        title = {"text": "Greater Sydney<br> Avg. Sentiment Now<br><span style='font-size:0.8em;color:gray'>Compare to previous year</span>"},
        domain = {'row': 0, 'column': 1}))
    indicator_fig.add_trace(go.Indicator(
        mode = "gauge+number",
        value = melb_sentiment_overall,
        gauge = {
            'axis': {'range': [min(sentiment_df['sentiment']), max(sentiment_df['sentiment'])]}, 
            'bar': {'color': "orange"}},
        title = {"text": "Greater Melboourne <br>Overall Sentiment"},
        domain = {'row': 0, 'column': 2}))
    indicator_fig.add_trace(go.Indicator(
        mode = "gauge+number",
        value = syd_sentiment_overall,
        gauge = {
            'axis': {'range': [min(sentiment_df['sentiment']), max(sentiment_df['sentiment'])]}, 
            'bar': {'color': "orange"}},
        title = {"text": "Greater Sydney <br>Overall Sentiment"},
        domain = {'row': 0, 'column': 3}))

    indicator_fig.update_layout(
        grid = {'rows': 1, 'columns': 4, 'pattern': "independent"},
        paper_bgcolor='rgba(0,0,0,0)', 
        plot_bgcolor='rgba(0,0,0,0)',
        font_color='#FFFFFF')
    # indicator_fig.show() # comment this line for flask app

    # %%
    sa2_gdf_topic = sa2_gdf.copy()
    topic_df = topic_df.merge(sa2_gdf_topic, left_on='area', right_on='SA2_NAME21', how='left')
    topic_df = gpd.GeoDataFrame(topic_df, crs="EPSG:4283", geometry=topic_df.geometry)
    # topic_df.head() # comment this out for flask app

    # %%
    topic_df_overtime = topic_df.groupby([topic_df.time.dt.year, topic_df.topic]).mean().reset_index()
    # topic_df_overtime[topic_df_overtime.topic == "environment"] 

    # %%
    lin_fig = go.Figure()

    for topic in topic_df_overtime.topic.unique():
        lin_fig.add_trace(go.Scatter(
            x=topic_df_overtime[topic_df_overtime.topic == topic]['time'],
            y=topic_df_overtime[topic_df_overtime.topic == topic]['sentiment'],
            name=topic,
            connectgaps=True
        ))

    lin_fig.update_layout(
        title="Sentiment by Topic Overtime",
        xaxis_title="Year",
        yaxis_title="Sentiment",
        paper_bgcolor='rgba(0,0,0,0)', 
        plot_bgcolor='rgba(0,0,0,0)',
        font_color='#FFFFFF'
    )
    # lin_fig.show() #comment this for flask app

    # %% [markdown]
    # Considering  `envir_test1` data wrangglings below (feel fee to ignore)

    # %%
    # envir_topic = envir_db.view('area_week/area_week_topic', include_doc=True)
    # envir_topic_df = pd.DataFrame((row.key+[row.value['sentiments']['compound']] for row in envir_topic),
    #                         columns = ['time', 'area', 'topic','sentiment'])
    # envir_topic_df = envir_topic_df.groupby(['time', 'area', 'topic']).mean().reset_index()
    # envir_topic_df['time'] = envir_topic_df.apply(lambda row: datetime.strptime(row['time']+'-1', 'w%W-%Y-%w'), axis=1) #append -1 as Monday
    # envir_topic_df = envir_topic_df[envir_topic_df['area'] != 'zzzzzzzzz']
    # envir_topic_df.head()

    # %%
    # # envir_topic_df = envir_topic_df.merge(sa2_gdf, left_on='area', right_on='SA2_NAME21', how='left')
    # envir_topic_overall_df = envir_topic_df.groupby(['area', 'topic']).mean().reset_index()
    # # envir_topic_overall_df.head()

    # envir_topic_overall_df = envir_topic_overall_df.merge(sa2_gdf, left_on='area', right_on='SA2_NAME21', how='left')
    # envir_topic_overall_df

    # %%
    # # envir_topic_overall.to_crs(pyproj.CRS.from_epsg(4283), inplace=True)
    # envir_topic_overall_df = gpd.GeoDataFrame(envir_topic_overall_df, crs="EPSG:4283", geometry=envir_topic_overall_df.geometry)
    # # envir_topic_overall_df.set_index('area', inplace=True)
    # envir_topic_overall_df.head()

    # %%
    # fig = px.choropleth_mapbox(envir_topic_overall_df, geojson=envir_topic_overall_df.geometry, 
    #                             locations=envir_topic_overall_df.index,
    #                             color=envir_topic_overall_df.sentiment,
    #                             zoom= 5,
    #                             center = {"lat": -37.8136, "lon": 144.9631}, mapbox_style="carto-positron")
    # fig.update_layout(mapbox_style="dark", mapbox_accesstoken=MAPBOX_ACCESS_TOKEN)
    # fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
    # fig.show()

    # %% [markdown]
    # ### Using `plotly.graph_objects` as alternative, uncomment those for substitutes

    # %%
    # envir_topic_df = envir_topic_df.merge(sa2_gdf, left_on='area', right_on='SA2_NAME21', how='left')
    # envir_topic_df = gpd.GeoDataFrame(envir_topic_df, crs="EPSG:4283", geometry=envir_topic_df.geometry)
    # envir_topic_df.crs

    # %%
    # dff = topic_df.copy()
    # gdff = dff[dff['time'].dt.year == 2022]
    # gdff = gdff[gdff['topic'] == 'health']
    # gdff.set_index('area', inplace=True)
    # gdff.shape

    # %%
    # fig = px.choropleth_mapbox(gdff, 
    #                         geojson=gdff.geometry,
    #                         color=gdff.sentiment,
    #                         locations=gdff.index,
    #                         zoom=5,
    #                         center = {"lat": -37.8136, "lon": 144.9631},
    #                         mapbox_style="carto-positron")
    # fig.show()

    # %%
    # geometry_json = json.loads(gdff.geometry.to_json())
    # fig = go.Figure(
    #     data=go.Choroplethmapbox(geojson=geometry_json,
    #                             locations=gdff.index,
    #                             z=gdff.sentiment,
    #                             zmin=min(gdff.sentiment), zmax=max(gdff.sentiment),
    #                             colorscale="Oranges",
    #                             marker_opacity=0.5, marker_line_width=0)
    # )
    # fig.update_layout(mapbox_style="dark", 
    #                 mapbox_accesstoken=MAPBOX_ACCESS_TOKEN,
    #                 mapbox_center = {"lat": -37.8136, "lon": 144.9631},
    #                 mapbox_zoom=3)
    # fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, 
    #                 paper_bgcolor='rgba(0,0,0,0)', 
    #                 plot_bgcolor='rgba(0,0,0,0)',
    #                 font_color='#FFFFFF')
    # fig.show()

    # %% [markdown]
    # ### Historical Tweets components 

    # %%
    hist_sentiment_df = pd.read_pickle('hist_sentiment_df.pkl')
    hist_sentiment_df = hist_sentiment_df.groupby([hist_sentiment_df.area]).mean().reset_index()
    hist_sentiment_df.head()

    # %%
    sa2_gdf_sent = sa2_gdf.copy()
    hist_sentiment_geo_df = hist_sentiment_df.merge(sa2_gdf_sent, left_on='area', right_on='SA2_NAME21', how='left')
    hist_sentiment_gdf = gpd.GeoDataFrame(hist_sentiment_geo_df, crs="EPSG:4283", geometry=hist_sentiment_geo_df.geometry)

    # %%
    hist_gdff = hist_sentiment_gdf.copy()
    hist_gdff.set_index('area', inplace=True)
    hist_gdff.index = hist_gdff.index.str.capitalize()
    hist_gdff.head()

    # %%
    hist_gdf_fig = px.choropleth_mapbox(hist_gdff, 
                        geojson=hist_gdff.geometry,
                        color=hist_gdff.sentiment,
                        locations=hist_gdff.index,
                        zoom=7.5,
                        center = {"lat": -37.8136, "lon": 144.9631},
                        mapbox_style="carto-positron",
                        color_continuous_scale="oranges",
                        title="Historical Sentiment by SA2 Area in Melbourne"
                        )
    hist_gdf_fig.update_traces(marker_line_width=0, marker_opacity=0.8)
    hist_gdf_fig.update_layout(mapbox_style="dark", mapbox_accesstoken=MAPBOX_ACCESS_TOKEN)
    hist_gdf_fig.update_layout(margin={"r":0,"t":50,"l":0,"b":0}, 
                    paper_bgcolor='rgba(0,0,0,0)', 
                    plot_bgcolor='rgba(0,0,0,0)',
                    font_color='#FFFFFF')


    # %% [markdown]
    # ## Dash app Logics Code

    # %%
    df_prerendered_dict = defaultdict(dict)
    for topic_itr in topic_df.topic.unique():
        for year_itr in range(min(topic_df.time).year, max(topic_df.time).year+1):
            prerednered_dff = topic_df.copy()
            prerednered_gdff = prerednered_dff[prerednered_dff['time'].dt.year == year_itr]
            prerednered_gdff = prerednered_gdff[prerednered_gdff['topic'] == topic_itr.lower()]
            prerednered_gdff.set_index('area', inplace=True)
            prerednered_gdff.index = prerednered_gdff.index.str.capitalize()

            df_prerendered_dict[topic_itr][str(year_itr)] = prerednered_gdff        

    # %%
    drop_down_lst = list(map(lambda x: x.capitalize(), topic_df.topic.unique()))
    left_container = html.Div(
                    id="left-container",
                    children=[
                        dcc.Dropdown(drop_down_lst , drop_down_lst[0],
                                    id='topic-dropdown',
                                    style={'font-family':'sans-serif', 
                                        'margin': '0px 0px 5px 0px', 
                                        'padding': '5px 0px 5px 0px',
                                        'background-color':'#282828'},
                                    clearable=False
                        ),
                        dcc.Graph(id='choropleth-mapbox', figure={}),
                        html.Div(
                            children=[
                                html.P(
                                    id="slider-text",
                                    children="Drag the slider to change the year:",
                                    style={'color':'#FFECE8', 'font-family':'sans-serif'}
                                ),
                                dcc.Slider(
                                        id='year-slider',
                                        min=min(topic_df.time).year,
                                        max=max(topic_df.time).year,
                                        value=max(topic_df.time).year,
                                        marks={str(year): {
                                            'label':str(year), 
                                            'style': {"color": "#FDA172", 'font-family':'sans-serif'} 
                                        } for year in range(min(topic_df.time).year, max(topic_df.time).year+1, 1)},
                                        step=None
                                )
                            ],
                            style={'padding': '20px 20px 20px 20px', 'background-color':'#282828'}),
                        html.Div(id='output-container', children=[], 
                                style={'text-align': 'center', 
                                    'color':'#FDA172', 
                                    'padding':'10px',
                                    'display': 'none'
                                },),
                        # dcc.Loading(
                        #     id="loading-1",
                        #     type="default",
                        #     children=html.Div(id="choropleth-mapbox")
                        # ),
                    ], style={'display': 'inline-block', 'width':'49%', 'vertical-align':'top'})

    # %%
    right_container = html.Div([
        dcc.Graph(id='tweet-distb-by-city', figure=pie_fig),
    ], style={'display': 'inline-block', 
            'width': '49%', 
            'margin': '0px 0px 0px 10px', 
            'padding': '0.2em 0em 0.5em 1.1em',
            'verticle-align':'top', 
            'text-align': 'center', 
            'background-color':'#282828'})

    # %%
    # JupyterDash._terminate_server_for_port('127.0.0.1', 8050)

    # %%
    # For Jupyter notebook uncomment the following line
    # app = JupyterDash(__name__)

    # For flask app uncomment the following line
    # app = Dash(__name__)

    app.layout = html.Div([
        html.H1('Sentiment Transportation on Dashboard', 
                                style={'text_align': 'center', 
                                    'color':'#FDA172', 
                                    'font-family':'sans-serif',
                                    'margin': '1em 0.3em 0.8em 0.3em'}),
        html.Div(id="heading-description", children=[
            html.H2('This dashboard shows the sentiment of selected topic in Australia. (+ve means happy, -ve mean sad).', 
                style={'text_align': 'center', 'color':'#FFFFFF', 'font-family':'sans-serif', 'margin': '0.7em'}),
            html.P('The data were product from MapReduce for Tweets that have location enabled and text which are able to be parsed into a Machine Learning Sentiment Scorer',
                style={'text_align': 'center', 'color':'#FFFFFF', 'font-family':'sans-serif', 'margin': '0.8em 0.8em 1.2em 0.8em'})
        ], style={'border-left': '5px solid darkorange'}),
        dcc.Graph(id='indicators', 
            figure=indicator_fig, 
            style={
                'width':'100%',
                'background-color':'#282828',
                'margin': '8px 0px 8px 0px',
            }),
        html.Div(children=[
            left_container,
            right_container
        ], style={'width': '100%', 'margin-bottom': '10px'}),
        dcc.Graph(id='tweet-sentiment-overtime', figure=lin_fig, style={'background-color':'#282828'}),
        dcc.Graph(id='hist-tweet-choropleth-mapbox', figure=hist_gdf_fig, style={'background-color':'#282828','padding': '10px'})
    ])

    @app.callback(
        [
        Output(component_id='output-container', component_property='children'),
        Output(component_id='choropleth-mapbox', component_property='figure')
        ],
        [Input(component_id='year-slider', component_property='value'),
        Input(component_id='topic-dropdown', component_property='value')]
    )
    def update_graph(year, topic):
        container = "The year selected was: {}".format(year)
        
        # dff = topic_df.copy()
        # gdff = dff[dff['time'].dt.year == year]
        # gdff = gdff[gdff['topic'] == topic.lower()]
        # gdff.set_index('area', inplace=True)
        # gdff.index = gdff.index.str.capitalize()
        gdff = df_prerendered_dict[topic.lower()][str(year)]

        ##### -- Uncomment below for plotly express, altough it renders slow
        # fig = px.choropleth_mapbox(gdff, 
        #                     geojson=gdff.geometry,
        #                     color=gdff.sentiment,
        #                     locations=gdff.index,
        #                     zoom=5,
        #                     center = {"lat": -37.8136, "lon": 144.9631},
        #                     mapbox_style="carto-positron",
        #                     color_continuous_scale="oranges")
        # fig.update_layout(mapbox_style="dark", mapbox_accesstoken=MAPBOX_ACCESS_TOKEN)
        # fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, 
        #                 paper_bgcolor='rgba(0,0,0,0)', 
        #                 plot_bgcolor='rgba(0,0,0,0)',
        #                 font_color='#FFFFFF')
        #####-- End of plotly express

        geometry_json = json.loads(gdff.geometry.to_json())
        fig = go.Figure(
            data=go.Choroplethmapbox(geojson=geometry_json,
                                    locations=gdff.index,
                                    z=gdff.sentiment,
                                    zmin=min(gdff.sentiment), zmax=max(gdff.sentiment),
                                    colorscale="Oranges",
                                    marker_opacity=0.5, marker_line_width=0)
        )
        fig.update_layout(mapbox_style="dark", 
                        mapbox_accesstoken=MAPBOX_ACCESS_TOKEN,
                        mapbox_center = {"lat": -37.8136, "lon": 144.9631},
                        mapbox_zoom=5)
        fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, 
                        paper_bgcolor='rgba(0,0,0,0)', 
                        plot_bgcolor='rgba(0,0,0,0)',
                        font_color='#FFFFFF')
        return container, fig
        # return fig
        
    return app.server

        
    # app.run_server(mode="external", debug=True)

    # %%


    # %%



