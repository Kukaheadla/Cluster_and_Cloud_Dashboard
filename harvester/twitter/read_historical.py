from numpy import (
    place,
)
from flask import Flask, make_response, jsonify, request
import tweepy
from tweepy import OAuthHandler
import time, datetime, os, copy

# from logger.logger import log

# To run the text_sentiment function:
# from twitter.text_sentiment import attach_sentiment
import json, re
from couchdb import Server, Document

# To get the suburb:
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, shape
from shapely.geometry.polygon import Polygon

##
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import json, re, contractions

shapefile = gpd.read_file("SA2_2021_AUST_SHP_GDA2020/SA2_2021_AUST_GDA2020.shp")
# melb_polygon = Polygon([(144.4, -37.52), (144.40, -38.42), (145.58, -38.42), (145.58, -37.52) ]) # Melbourne rectangle
# sydney_polygon = Polygon([(150.50, -33.51), (150.50, -34.16), (151.35, -34.16), (151.35, -33.51)]) # Sydney rectangle

# shapefile = shapefile[shapefile.geometry.intersects(melb_polygon)]
shapefile = shapefile.loc[shapefile["STE_NAME21"].isin(["Victoria"])]

sa2_name21 = list(shapefile.SA2_NAME21)
sa2_code21 = list(shapefile.SA2_CODE21)

sa3_name21 = list(shapefile.SA3_NAME21)
sa3_code21 = list(shapefile.SA3_CODE21)

sa4_name21 = list(shapefile.SA4_NAME21)
sa4_code21 = list(shapefile.SA4_CODE21)

gcc_name21 = list(shapefile.GCC_NAME21)
gcc_code21 = list(shapefile.GCC_CODE21)

shapefile_vic_geometry = shapefile.geometry


def attach_sentiment(tweet_object):

    analyzer = SentimentIntensityAnalyzer()
    sentence = tweet_object["doc"]["text"]

    # Remove url from string
    sentence = re.sub(r"http\S+", "", sentence).strip()
    # fix contractions
    # IndexError for 3005469185e7ce96f1066bf3b1ffbcb7:
    # İsrail temsilcisiyle yanyana oturmamak için Münih Güvenlik Konferansına katılmayan dış İşleri Bakanı Mevlüt Çavuşoğlu'nu ayakta alkışlıyoruz
    try:
        prior = sentence
        sentence = contractions.fix(sentence, slang=True)
    except IndexError:
        sentence = prior

    # remove punctuation from string
    sentence = re.sub(r"[^\w\s]", "", sentence).strip()
    # remove extra whitespace
    sentence = re.sub(r" +", " ", sentence).strip()
    # lowercase everything
    sentence = sentence.lower()

    sentiment_dict = analyzer.polarity_scores(sentence)
    # Using the sentiment results, can also obtain the general sentiment:

    neg = sentiment_dict["neg"]
    neu = sentiment_dict["neu"]
    pos = sentiment_dict["pos"]

    if neg > neu and neg > pos:
        tweet_object["doc"].update({"sentiments": sentiment_dict})
        tweet_object["doc"].update({"overall_sentiment": "negative_sentiment"})
        return tweet_object

    elif neu > pos and neu > neg:
        tweet_object["doc"].update({"sentiments": sentiment_dict})
        tweet_object["doc"].update({"overall_sentiment": "neutral_sentiment"})
        return tweet_object

    elif pos > neu and pos > neg:
        tweet_object["doc"].update({"sentiments": sentiment_dict})
        tweet_object["doc"].update({"overall_sentiment": "positive_sentiment"})
        return tweet_object

    elif pos == neu and pos == neg:
        tweet_object["doc"].update({"sentiments": sentiment_dict})
        tweet_object["doc"].update({"overall_sentiment": "no_clear_sentiment"})
        return tweet_object

    elif pos == neu and pos != neg:
        tweet_object["doc"].update({"sentiments": sentiment_dict})
        tweet_object["doc"].update({"overall_sentiment": "positive_neutral_sentiment"})
        return tweet_object

    elif neg == neu and neu != neg:
        tweet_object["doc"].update({"sentiments": sentiment_dict})
        tweet_object["doc"].update({"overall_sentiment": "negative_neutral_sentiment"})
        return tweet_object

    elif neg == pos and neu != pos:
        tweet_object["doc"].update({"sentiments": sentiment_dict})
        tweet_object["doc"].update({"overall_sentiment": "positive_negative_sentiment"})
        return tweet_object

    tweet_object["doc"].update({"sentiments": sentiment_dict})
    return tweet_object


##

# Read through the historical_tweets data frame.
username = "user"
password = "password"

couchserver = Server("http://user:password@172.26.130.155:5984")
# couchserver = Server("http://user:pass@localhost:5984")
# for dbname in couchserver:
#    print(dbname)
#    pass

db = couchserver["historical_tweets"]

# Create a new couchdb for the adjusted tweets.

# Now iterate through the database one document at a time.
# https://stackoverflow.com/questions/55510000/how-to-retrieve-all-docs-from-couchdb-and-convert-it-as-csv-using-python
# Use for row in db.view('_all_docs'):
# https://stackoverflow.com/questions/37050231/how-to-display-all-documents-in-couchdb-using-python
# <class 'couchdb.client.Document'>
def get_suburb(tweet_coords):
    # First read in the shapefile.
    # This will be used to check if the Point objects are in Australia or not.
    # Then obtain the point as a Point object.
    pt = Point(tweet_coords[1], tweet_coords[0])
    # Now iterate through the shapes.
    count = 0
    suburb = ["", "", "", "", "", "", "", ""]
    for shape in shapefile_vic_geometry:
        if shape != None:
            if shape.covers(pt):
                # surburb is determined:
                suburb[0] = sa2_name21[count]
                suburb[1] = sa2_code21[count]
                # SA3
                suburb[2] = sa3_name21[count]
                suburb[3] = sa3_code21[count]
                # SA4
                suburb[4] = sa4_name21[count]
                suburb[5] = sa4_code21[count]
                # GCC
                suburb[6] = gcc_name21[count]
                suburb[7] = gcc_code21[count]
                return suburb
        count += 1
    # In this case the location is outside Australia.
    return [
        "ZZZZZZZZZ",
        "ZZZZZZZZZ",
        "ZZZZZZZZZ",
        "ZZZZZZZZZ",
        "ZZZZZZZZZ",
        "ZZZZZZZZZ",
        "ZZZZZZZZZ",
        "ZZZZZZZZZ",
    ]


count_tweet = 0
check_point = 0

for item in db.view("_design/GeoInfo/_view/TweetsWithGeoInfo"):

    if count_tweet < check_point:
        print("skip count =", str(count_tweet))
        count_tweet += 1
        continue

    tweet_id = item["id"]

    tmp = dict(db[tweet_id])

    print(item["id"], str(count_tweet))

    res = get_suburb(tmp["doc"]["geo"]["coordinates"])

    tmp["doc"]["suburb"] = res[0]
    tmp["doc"]["suburb_code"] = res[1]

    tmp["doc"]["suburb_SA3"] = res[2]
    tmp["doc"]["suburb_code_SA3"] = res[3]

    tmp["doc"]["suburb_SA4"] = res[4]
    tmp["doc"]["suburb_code_SA4"] = res[5]

    tmp["doc"]["GCC_NAME21"] = res[6]
    tmp["doc"]["GCC_CODE21"] = res[7]

    attach_sentiment(tmp)

    db[str(tmp["_id"])] = tmp

    count_tweet += 1

print("count is", str(count_tweet))
