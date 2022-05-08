"""
Main crawler application which can do one of two things:
    - stream data via the Twitter API, that is, look at real time tweets and write them to the database
    - perform a search back into the past seven days and write those tweets into the database
The functions found here all relate to the Twitter API and crucially, what specific fields and data
we wish to extract from the API.
The main loop of the application should not be performed here. For example, if the credentials used encounter the daily limit
or the monthly account limit, that error should be passed back to the main module, and called with new credentials.
Authors: David, Alex
"""
from asyncore import poll
from numpy import (
    place,
)
from flask import Flask, make_response, jsonify
import tweepy
from tweepy import OAuthHandler
import time, datetime
from logger.logger import log
import typing

# To run the text_sentiment function:
from twitter.text_sentiment import attach_sentiment
import json, re

# To get the suburb:
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, shape
from shapely.geometry.polygon import Polygon

# tweet fields that we want returned in the Twitter API response
# Left out 'referenced_tweets' in tweet_fields as it may lead to RuntimeError.
# Left out "entities.mentions.username", "referenced_tweets.id" and "referenced_tweets.id.author_id" as can lead to RuntimeError.

###For the shapefiles:
shapefile = gpd.read_file("twitter/SA2_2021_AUST_SHP_GDA2020/SA2_2021_AUST_GDA2020.shp")

sa2_name21 = list(shapefile.SA2_NAME21)
sa2_code21 = list(shapefile.SA2_CODE21)

sa3_name21 = list(shapefile.SA3_NAME21)
sa3_code21 = list(shapefile.SA3_CODE21)

sa4_name21 = list(shapefile.SA4_NAME21)
sa4_code21 = list(shapefile.SA4_CODE21)

gcc_name21 = list(shapefile.GCC_NAME21)
gcc_code21 = list(shapefile.GCC_CODE21)

###

tweet_fields = [
    "attachments",
    "author_id",
    "context_annotations",
    "conversation_id",
    "created_at",
    "entities",
    "geo",
    "id",
    "in_reply_to_user_id",
    "lang",
    "public_metrics",
    "possibly_sensitive",
    "reply_settings",
    "source",
    "text",
    "withheld",
]
user_fields = [
    "created_at",
    "description",
    "entities",
    "id",
    "location",
    "name",
    "pinned_tweet_id",
    "profile_image_url",
    "protected",
    "public_metrics",
    "url",
    "username",
    "verified",
    "withheld",
]
expansions = [
    "attachments.poll_ids",
    "attachments.media_keys",
    "author_id",
    "geo.place_id",
    "in_reply_to_user_id",
]
media_fields = [
    "duration_ms",
    "height",
    "media_key",
    "preview_image_url",
    "type",
    "url",
    "width",
    "public_metrics",
    "alt_text",
]
place_fields = [
    "contained_within",
    "country",
    "country_code",
    "full_name",
    "geo",
    "id",
    "name",
    "place_type",
]
poll_fields = ["duration_minutes", "end_datetime", "id", "options", "voting_status"]
"""
Flask application for optional use. Does not need to be run as a server unless you want to create some custom views etc.
"""
app = Flask(__name__, static_url_path="")


def determine_geo_info():
    pass


class TweetListener(tweepy.StreamingClient):
    """
    StreamingClient allows filtering and sampling of realtime Tweets using Twitter API v2.
    https://docs.tweepy.org/en/latest/streamingclient.html#tweepy.StreamingClient
    """

    count = 0
    total_tweets_read = 0
    tweet_id_lst = []
    start_time = time.time()
    topic_name="environment"

    def __init__(
        self,
        tweet_id_lst,
        author_id_lst,
        couchdb_server,
        city_name,
        topic,
        usr_count,
        twitter_bearer_token,
        auth,
        **kwargs,
    ):
        """
        Creates a Tweetlistener which will listen for a certain amount of time.
        Including our own override so we can use the couchdb server defined in main.py
        """
        super().__init__(twitter_bearer_token, **kwargs)
        self.tweet_id_lst = tweet_id_lst
        self.user_id = author_id_lst
        self.couchdb_server = couchdb_server
        self.city_name = city_name
        self.topic_name = topic
        self.usr_count = usr_count
        api = tweepy.API(auth)
        self.api = api

        if "new_tweets" in self.couchdb_server:
            print("Use existing database")
            self.twitter_stream = self.couchdb_server["new_tweets"]
            print("Existing database used: envir_test1")

        elif "new_tweets" not in self.couchdb_server:
            print("Create new database")
            self.twitter_stream = self.couchdb_server.create("new_tweets")
            print("Database created: new_tweets")

    # Defining some variables:
    def on_tweet(self, tweet: tweepy.Tweet):
        """
        Event listener for Tweet events in the HTTP long poll.
        """
        
        if self.total_tweets_read % 10 == 0:
            print("Number of streamed tweets read is", self.total_tweets_read)
        tmp = dict(tweet.data)
        if "geo" in tmp.keys() and tmp["geo"] != {}:
            print("Geo available")
            suburb = ""
            if "place_id" in tmp["geo"] and "coordinates" not in tmp["geo"].keys():
                loc = tmp["geo"]["place_id"]
                location = self.api.geo_id(loc)
                tmp["geo"]["geo_location"] = {
                    "id": location.id,
                    "url": location.url,
                    "place_type": location.place_type,
                    "name": location.name,
                    "full_name": location.full_name,
                    "country_code": location.country_code,
                    "contained_within": str(location.contained_within),
                    "geometry": str(location.geometry),
                    "polylines": str(location.polylines),
                    "centroid": str(location.centroid),
                    "bounding_box": str(location.bounding_box),
                }
                # Using the centroid:
                suburb = get_suburb(location.centroid)
                tmp["geo"]["suburb"] = suburb[0]
                tmp["geo"]["suburb_code"] = suburb[1]

                tmp["geo"]["suburb_SA3"] = suburb[2]
                tmp["geo"]["suburb_code_SA3"] = suburb[3]

                tmp["geo"]["suburb_SA4"] = suburb[4]
                tmp["geo"]["suburb_code_SA4"] = suburb[5]

                tmp["geo"]["GCC_NAME21"] = suburb[6]
                tmp["geo"]["GCC_CODE21"] = suburb[7]

            elif "coordinates" in tmp["geo"].keys():
                # Get the coordinates directly:
                suburb = get_suburb(tmp["geo"]["coordinates"])
                tmp["geo"]["suburb"] = suburb[0]
                tmp["geo"]["suburb_code"] = suburb[1]

                tmp["geo"]["suburb_SA3"] = suburb[2]
                tmp["geo"]["suburb_code_SA3"] = suburb[3]

                tmp["geo"]["suburb_SA4"] = suburb[4]
                tmp["geo"]["suburb_code_SA4"] = suburb[5]

                tmp["geo"]["GCC_NAME21"] = suburb[6]
                tmp["geo"]["GCC_CODE21"] = suburb[7]

        if tmp["id"] not in self.tweet_id_lst:
            try:
                tmp["day_of_week"] = tmp["created_at"].strftime("%A")
                tmp["year"] = tmp["created_at"].strftime("%Y")
                tmp["month"] = tmp["created_at"].strftime("%m")
                tmp["day"] = tmp["created_at"].strftime("%d")
                tmp["hour"] = tmp["created_at"].strftime("%H")
            except Exception as e:
                pass

            if "created_at" in tmp.keys() and tmp["created_at"] != None:
                tmp["created_at"] = str(tmp["created_at"])
                tmp["city_rule_key"] = self.city_name
                tmp["topic_name"] = self.topic_name

                # duplicate update check.
                # we use the tweet ID from twitter as the primary key for rows
                # this prevents duplicates being written into the database
                # however it will make couchdb throw an error.
                try:
                    attach_sentiment(tmp)
                    self.twitter_stream[str(tmp["id"])] = tmp
                    self.tweet_id_lst.append(tmp["id"])
                    self.count += 1
                except Exception as e:
                    print("Exception B")
                    log(e, False)
                    pass
        self.total_tweets_read += 1

    def on_request_error(self, status_code):
        """
        Is triggered when the connection is closed etc.
        """
        print(status_code)
        log(status_code, True)
        # rate limit error
        if status_code == 420:
            return False

    # def on_connection_error(self):
    #     self.disconnect()


def log(message: str, debug: bool):
    """
    Logs a message if debug flag is True.
    """
    if debug:
        print(message)


def rule_regulation(client, rules):

    # remove existing rules
    resp = client.get_rules()
    if resp and resp.data:
        rule_ids = []
        for rule in resp.data:
            rule_ids.append(rule.id)

        client.delete_rules(rule_ids)

    # Validate the rule
    resp = client.add_rules(rules, dry_run=True)
    if resp.errors:
        raise RuntimeError(resp.errors)

    # Add the rule
    resp = client.add_rules(rules)
    if resp.errors:
        raise RuntimeError(resp.errors)


#### Working with shapefiles
def get_suburb(tweet_coords):

    # Important to check the format type of tweet_coords:
    if type(tweet_coords) is dict:
        tweet_coords = tweet_coords["coordinates"]

    # This will be used to check if the Point objects are in Australia or not.

    # Then obtain the point as a Point object.
    pt = Point(tweet_coords[0], tweet_coords[1])
    # Now iterate through the shapes.
    count = 0
    suburb = ["", "", "", "", "", "", "", ""]

    for shape in shapefile.geometry:

        if shape != None:

            if shape.contains(pt) or shape.touches(pt):
                # surburb is determined:
                suburb[0] = sa2_name21[count]
                suburb[1] = sa2_code21[count]
                # SA3
                suburb[2] = sa3_name21[count]
                suburb[3] = sa3_code21[count]
                # SA4
                suburb[4] = sa4_name21[count]
                suburb[5] = sa4_code21[count]

                suburb[6] = gcc_name21[count]
                suburb[7] = gcc_name21[count]

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


####

##The following functions are for the search method:
@app.route("/melbourne_test")
def main_search(id_lst, bearer_token, client, couchdb_server, city_name, topic, args):
    """
    Main non-streaming search function.
    """
    client.start_time = time.time()

    twitter_stream_search = None
    if "new_tweets" in couchdb_server:
        print("Use existing database")
        twitter_stream_search = couchdb_server["new_tweets"]
        print("Existing database used: new_tweets")

    elif "new_tweets" not in couchdb_server:
        print("Create new database")
        twitter_stream_search = couchdb_server.create("new_tweets")
        print("Database created: new_tweets")

    # vars related to searching
    search_client = tweepy.Client(bearer_token, wait_on_rate_limit=True)

    if topic == "environment" and city_name == "melbourne":
        query = city_name + ' ("air quality" OR @SustainVic OR pollution OR #Environment OR #savetheplanet OR #Green OR #Solar OR renewable OR ' + \
        '#ClimateCrisis OR #Earth OR #climatechange OR #ClimateAction OR #plasticpollution OR climate OR #nature OR #OnlyOneEarth OR #RenewableEnergy OR #Energy OR ' + \
        '@climatecouncil OR #Ecofriendly OR Earth OR recycling OR #AirPollution OR Carbon OR coal OR @FoEAustralia OR emissions OR "climate change" OR nature OR "renewable energy" OR '+\
        '@EnviroVic OR #netzero OR #greenpeaceap OR @GreenpeaceAP)'
    
    elif topic == "environment" and city_name == "sydney":
        query = city_name + ' ("air quality" OR @SustainVic OR pollution OR #Environment OR #savetheplanet OR #Green OR #Solar OR renewable OR ' + \
        '#ClimateCrisis OR #Earth OR #climatechange OR #ClimateAction OR #plasticpollution OR climate OR #nature OR #OnlyOneEarth OR #RenewableEnergy OR #Energy OR ' + \
        '@climatecouncil OR #Ecofriendly OR Earth OR recycling OR #AirPollution OR Carbon OR coal OR @FoEAustralia OR emissions OR "climate change" OR nature OR "renewable energy" OR '+\
        '@EnviroVic OR #netzero OR #greenpeaceap OR @GreenpeaceAP)'

    elif topic == "health":
        query = city_name + '(@VicGovDH OR @VictorianCHO OR @NSWHealth OR )'
    elif topic == "transport":
        query = (
            city_name
            + " ( "
            + topic
            + ' OR bus OR "public transport" OR train OR tram)'
        )
    elif topic != "transport" and topic != "environment":
        query = city_name

    print("The query is", query)
    max_results = 100
    counter = 0
    total_tweets_read = 0
    user_ids = []

    try:
        tst_paginator = tweepy.Paginator(
            search_client.search_recent_tweets,
            query,
            max_results=max_results,
            tweet_fields=tweet_fields,
            user_fields=user_fields,
            expansions=expansions,
            media_fields=media_fields,
            place_fields=place_fields,
            poll_fields=poll_fields,
        ).flatten(limit=100000)

        id_last = ''

        for tweet in tst_paginator:

            # check for time
            #if (time.time() - client.start_time) > 1800:
            #    print("exceeded time")
            #    raise Exception

            total_tweets_read += 1

            twt = dict(tweet)
            if twt["author_id"] not in client.user_id:
                client.user_id.append(str(twt["author_id"]))
                user_ids.append(str(twt["author_id"]))

            elif twt["author_id"] in client.user_id:
                continue

            if str(twt["id"]) not in client.tweet_id_lst:

                # duplicate update check.
                # we use the tweet ID from twitter as the primary key for rows
                # this prevents duplicates being written into the database
                # however it will make couchdb throw an error.

                #Now check for likes:
                if twt["public_metrics"]["like_count"] > 0:
                    liking_users = search_client.get_liking_users(twt["id"], max_results=100)

                    for item in liking_users.data:
                        if item["id"] not in client.user_id:
                            user_ids.append(str(item["id"]))
                            client.user_id.append(str(twt["id"]))

                adjust_tmp(twt, city_name, topic, twitter_stream_search, client)

                try:
                    twt = attach_sentiment(twt)
                    twitter_stream_search[str(twt["id"])] = twt
                    (client.tweet_id_lst).append(str(twt["id"]))
                    counter += 1
                except Exception as e:
                    log(e, args.verbose)
                    pass

            if total_tweets_read % 100 == 0:
                print("total tweets read =", str(total_tweets_read))
        
        client.user_id = list(set(client.user_id))
        print("length is", len(client.user_id))
        #client.user_id.insert(0, 1099615236)
        #client.user_id.insert(0, 52027672)
        #client.user_id.insert(0, 1043745428879986689)
        #client.user_id.insert(0, 1493422299462402052)
        
        count_ids = client.usr_count

        print("Now go through the user_ids:")
        #for id_val in client.user_id:
        #while count_ids < len(client.user_id):

        for id_val in client.user_id:

            id_val = client.user_id[count_ids]
            print("id", str(id_val))
            res = tweepy.Paginator(
                search_client.get_users_tweets,
                id=id_val,
                expansions=expansions,
                media_fields=media_fields,
                place_fields=place_fields,
                poll_fields=poll_fields,
                tweet_fields=tweet_fields,
                user_fields=user_fields,
                max_results=10,
            ).flatten(limit=1000)

            #if (time.time() - client.start_time) > 1800:
            #    print("exceeded time user_ids")
            #    raise Exception
            location = None

            for tmp in res:
                tmp = dict(tmp)
                count  = 0
                total_tweets_read += 1

                tmp["day_of_week"] = tmp["created_at"].strftime("%A")
                tmp["year"] = tmp["created_at"].strftime("%Y")
                tmp["month"] = tmp["created_at"].strftime("%m")
                tmp["day"] = tmp["created_at"].strftime("%d")
                tmp["hour"] = tmp["created_at"].strftime("%H")
        
                tmp["created_at"] = str(tmp["created_at"])
                tmp["city_rule_key"] = city_name
                tmp["topic_name"] = topic

                if count == 0:
                    location = adjust_usr_tmp(tmp, client, count, location)
                elif count > 0:
                    adjust_usr_tmp(tmp, client, count, location)

                if total_tweets_read % 100 == 0:
                    print("total tweets read =", str(total_tweets_read))

                if str(tmp["id"]) not in client.tweet_id_lst:
                    attach_sentiment(tmp)
                    twitter_stream_search[str(tmp["id"])] = tmp
                    (client.tweet_id_lst).append(str(tmp["id"]))
                    counter += 1
                count += 1
            
            count_ids += 1
            client.usr_count += 1
            #client.user_id.remove(id)

        #client.user_id = client.user_id[count_ids:]

    except tweepy.errors.TooManyRequests:
        #client.user_id = client.user_id[count_ids:]

        #client.user_id.remove(id_last)
        print("Too many requests")
        client.usr_count += 1
        return [counter, total_tweets_read]

    # except tweepy.errors.HTTPException:
    #    print("General tweepy exception")
    #    return [counter, total_tweets_read]

    except KeyboardInterrupt or Exception:
        # except Exception or RuntimeError:
        #client.user_id = client.user_id[count_ids:]
        #print("len is now", str(len(client.user_id)))
        client.usr_count += 1
        print("Exception number of tweets read is", str(total_tweets_read))
        return [counter, total_tweets_read]

    print("Reached the end")
    print("number of tweets read is", str(total_tweets_read))
    return [counter, total_tweets_read]


def adjust_tmp(tmp, city_name, topic, twitter_stream_search, client):

    tmp["day_of_week"] = tmp["created_at"].strftime("%A")
    tmp["year"] = tmp["created_at"].strftime("%Y")
    tmp["month"] = tmp["created_at"].strftime("%m")
    tmp["day"] = tmp["created_at"].strftime("%d")
    tmp["hour"] = tmp["created_at"].strftime("%H")
    tmp["created_at"] = str(tmp["created_at"])
    tmp["city_rule_key"] = city_name
    tmp["topic_name"] = topic

    if "geo" in tmp.keys() and tmp["geo"] != {}:
        print("Geo available")
        suburb = ["", "", "", "", "", "", "", ""]
        if "place_id" in tmp["geo"] and "coordinates" not in tmp["geo"].keys():
            loc = tmp["geo"]["place_id"]
            location = client.api.geo_id(loc)
            tmp["geo"]["geo_location"] = {
                "id": location.id,
                "url": location.url,
                "place_type": location.place_type,
                "name": location.name,
                "full_name": location.full_name,
                "country_code": location.country_code,
                "contained_within": str(location.contained_within),
                "geometry": str(location.geometry),
                "polylines": str(location.polylines),
                "centroid": str(location.centroid),
                "bounding_box": str(location.bounding_box),
            }

            # Now obtain the suburb:
            # Using the centroid:
            suburb = get_suburb(location.centroid)
            tmp["geo"]["suburb"] = suburb[0]
            tmp["geo"]["suburb_code"] = suburb[1]

            tmp["geo"]["suburb_SA3"] = suburb[2]
            tmp["geo"]["suburb_code_SA3"] = suburb[3]

            tmp["geo"]["suburb_SA4"] = suburb[4]
            tmp["geo"]["suburb_code_SA4"] = suburb[5]

            tmp["geo"]["GCC_NAME21"] = suburb[6]
            tmp["geo"]["GCC_CODE21"] = suburb[7]

        elif "coordinates" in tmp["geo"].keys() and len(tmp["geo"]["coordinates"]) > 0:
            # Get the coordinates directly:
            suburb = get_suburb(tmp["geo"]["coordinates"])
            tmp["geo"]["suburb"] = suburb[0]
            tmp["geo"]["suburb_code"] = suburb[1]

            tmp["geo"]["suburb_SA3"] = suburb[2]
            tmp["geo"]["suburb_code_SA3"] = suburb[3]

            tmp["geo"]["suburb_SA4"] = suburb[4]
            tmp["geo"]["suburb_code_SA4"] = suburb[5]

            tmp["geo"]["GCC_NAME21"] = suburb[6]
            tmp["geo"]["GCC_CODE21"] = suburb[7]


def adjust_usr_tmp(tmp, client, count, usr):

    location = None

    if "geo" in tmp.keys() and tmp["geo"] != {}:
        print("Geo available")
        suburb = ["", "", "", "", "", "", "", ""]
        if "place_id" in tmp["geo"] and "coordinates" not in tmp["geo"].keys():
            loc = tmp["geo"]["place_id"]
            if count == 0:
                location = client.api.geo_id(loc)
            elif count > 0:
                location=usr

            tmp["geo"]["geo_location"] = {
                "id": location.id,
                "url": location.url,
                "place_type": location.place_type,
                "name": location.name,
                "full_name": location.full_name,
                "country_code": location.country_code,
                "contained_within": str(location.contained_within),
                "geometry": str(location.geometry),
                "polylines": str(location.polylines),
                "centroid": str(location.centroid),
                "bounding_box": str(location.bounding_box),
            }

            # Now obtain the suburb:
            # Using the centroid:
            suburb = get_suburb(location.centroid)
            tmp["geo"]["suburb"] = suburb[0]
            tmp["geo"]["suburb_code"] = suburb[1]

            tmp["geo"]["suburb_SA3"] = suburb[2]
            tmp["geo"]["suburb_code_SA3"] = suburb[3]

            tmp["geo"]["suburb_SA4"] = suburb[4]
            tmp["geo"]["suburb_code_SA4"] = suburb[5]

            tmp["geo"]["GCC_NAME21"] = suburb[6]
            tmp["geo"]["GCC_CODE21"] = suburb[7]

        elif "coordinates" in tmp["geo"].keys() and len(tmp["geo"]["coordinates"]) > 0:
            # Get the coordinates directly:
            suburb = get_suburb(tmp["geo"]["coordinates"])
            tmp["geo"]["suburb"] = suburb[0]
            tmp["geo"]["suburb_code"] = suburb[1]

            tmp["geo"]["suburb_SA3"] = suburb[2]
            tmp["geo"]["suburb_code_SA3"] = suburb[3]

            tmp["geo"]["suburb_SA4"] = suburb[4]
            tmp["geo"]["suburb_code_SA4"] = suburb[5]

            tmp["geo"]["GCC_NAME21"] = suburb[6]
            tmp["geo"]["GCC_CODE21"] = suburb[7]

    return location



@app.errorhandler(400)
def not_found(error):
    return make_response(jsonify({"error": "Bad request"}), 400)


@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({"error": "Not found"}), 404)


###


def read_stream(client, start_time):
    """
    -> (
        typing.Any
        | tuple[typing.Literal[False], typing.Any]
        | tuple[typing.Literal[False], Exception]
        | None
    ):
    """
    """
    todo
    """
    try:
        # https://developer.twitter.com/en/docs/twitter-api/tweets/filtered-stream/api-reference/get-tweets-search-stream
        client.filter(
            expansions=expansions,
            place_fields=place_fields,
            tweet_fields=tweet_fields,
            user_fields=user_fields,
            media_fields=media_fields,
            poll_fields=poll_fields,
            threaded=False,
        )
    except KeyboardInterrupt:
        log("stopping streaming due to keyboard interrupt", True)
        print("Stop the streaming")
        return client
    except tweepy.errors.HTTPException as tweepyHttpException:
        # explicit raise of this error as we may want to do something else
        log("Tweepy HTTP exception", True)
        raise tweepyHttpException
    except Exception as e:
        raise e
    return client


def main_stream(client, city_name="melbourne", topic="environment"):
    """
    Main function for streaming Tweets using the Twitter Streaming API.
    """
    # First obtain the necessary authorization data
    if topic == "environment":
        query = city_name + ' ("air quality" OR #ClimateEmergency OR plant OR pollution OR #Environment OR #savetheplanet OR #Green OR #Solar OR renewable OR ' + \
        '#ClimateCrisis OR #Earth OR #climatechange OR #ClimateAction OR #plasticpollution OR climate OR #nature OR nature OR sustainable OR #OnlyOneEarth OR #RenewableEnergy OR #Energy OR ' + \
        'sustainability OR #Ecofriendly OR Earth OR recycling OR #AirPollution OR Carbon OR coal OR fuel OR emissions OR "climate change" OR nature OR "renewable energy")'

    elif topic == "transport":
        query = (
            city_name + " (" + topic + ' OR bus OR "public transport" OR train OR tram)'
        )
    elif topic != "transport" and topic != "environment":
        query = city_name

    print("The query is:", query)
    rules = [tweepy.StreamRule(value=query)]
    rule_regulation(client, rules)
    # https://developer.twitter.com/en/docs/twitter-api/tweets/filtered-stream/api-reference/get-tweets-search-stream-rules
    print(client.get_rules())
    start_time = time.time()

    result = None
    try:
        result = read_stream(client, start_time)
    except Exception as e:
        log(f"exception raised: {str(e)}", True)
        raise e

    return [client.tweet_id_lst, client.count, client.total_tweets_read]


def do_work(
    twitter_id_lst,
    author_id_lst,
    twitter_credentials,
    args,
    couchdb_server,
    curr_iter,
    usr_value,
    mode="stream",
):
    """
    Does the main loop for the crawler.
    """

    streaming_no = 0
    search_no = 0
    total_tweets_read = 0
    total_tweets_obtained = 0

    total = []

    auth = OAuthHandler(
        twitter_credentials["consumer_key"], twitter_credentials["consumer_secret"]
    )
    auth.set_access_token(
        twitter_credentials["access_token"], twitter_credentials["access_token_secret"]
    )

    client = TweetListener(
        twitter_id_lst,
        author_id_lst,
        couchdb_server,
        args.city,
        args.topic,
        usr_value,
        twitter_credentials["bearer_token"],
        auth,
        wait_on_rate_limit=True,
    )

    if mode == "stream":
        log("running the streaming API", args.debug)
        val = None
        try:
            val = main_stream(client, args.city, args.topic)
        except Exception as e:
            log(e, args.debug)
            raise e
        id_lst = val[0]
        log(
            f"Total number of tweets read for streaming API is {str(val[2])}\nTotal number of unique tweets obtained for streaming API is {str(val[1])}",
            args.debug,
        )
        total_tweets_obtained += val[1]
        total_tweets_read += val[2]

    if mode == "search":
        log("running the search API", args.debug)
        search_result = main_search(
            [],
            twitter_credentials["bearer_token"],
            client,
            couchdb_server,
            args.city,
            args.topic,
            args,
        )
        if search_result == False:
            return False
        log(
            f"Total number of tweets read for search API is {str(search_result[1])}\nTotal number of unique tweets obtained for search API is {str(search_result[0])}",
            args.debug,
        )

        total_tweets_obtained += search_result[0]
        total_tweets_read += search_result[1]
        print("Total number of tweets read", str(search_result[1]))
        print("Total number of unique tweets obtained:", search_result[0])

    # Print the results:
    print("Number of tweets read", str(total_tweets_read))
    print("Number of valid tweets obtained", str(total_tweets_obtained))

    return [
        total_tweets_obtained,
        total_tweets_read,
        client.tweet_id_lst,
        client.user_id,
        client.usr_count
    ]
    # return "todo: result goes here! This might be an error which we can recover from, such as hitting API limits"
