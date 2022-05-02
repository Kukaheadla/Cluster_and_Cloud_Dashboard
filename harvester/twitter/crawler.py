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
from numpy import (
    place,
)
from flask import Flask, make_response, jsonify
import tweepy
from tweepy import OAuthHandler
import time, datetime
from logger.logger import log

#To run the text_sentiment function:
from twitter.text_sentiment import attach_sentiment
import json, re

#To get the suburb:
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, shape
from shapely.geometry.polygon import Polygon

# tweet fields that we want returned in the Twitter API response
#Left out 'referenced_tweets' in tweet_fields as it may lead to RuntimeError.
#Left out "entities.mentions.username", "referenced_tweets.id" and "referenced_tweets.id.author_id" as can lead to RuntimeError.

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
user_fields = ["created_at", "description", "entities", "id", "location", "name", "pinned_tweet_id", "profile_image_url", "protected", 
    "public_metrics", "url", "username", "verified", "withheld"]
expansions = ["attachments.poll_ids", "attachments.media_keys", "author_id", "geo.place_id", 
    "in_reply_to_user_id"]
media_fields = ["duration_ms", "height", "media_key", "preview_image_url", "type", "url", "width", "public_metrics", "alt_text"]
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

class TweetListener(tweepy.StreamingClient):
    """
    StreamingClient allows filtering and sampling of realtime Tweets using Twitter API v2.
    https://docs.tweepy.org/en/latest/streamingclient.html#tweepy.StreamingClient
    """

    count = 0
    total_tweets_read = 0
    tweet_id_lst = []
    start_time = time.time()

    def __init__(self, couchdb_server, city_name, topic, twitter_bearer_token, auth, **kwargs):
        """
        Creates a Tweetlistener which will listen for a certain amount of time.
        Including our own override so we can use the couchdb server defined in main.py
        """
        super().__init__(twitter_bearer_token, **kwargs)
        self.couchdb_server = couchdb_server
        self.city_name = city_name
        self.topic_name = topic
        api = tweepy.API(auth)
        self.api = api
        if "twitter_stream_envir" in self.couchdb_server:
            print("Use existing database")
            self.twitter_stream = self.couchdb_server["twitter_stream_envir"]
            print("Existing database used: twitter_stream_envir")

        elif "twitter_stream_envir" not in self.couchdb_server:
            print("Create new database")
            self.twitter_stream = self.couchdb_server.create("twitter_stream_envir")
            print("Database created: twitter_stream_envir")

    # Defining some variables:
    def on_tweet(self, tweet: tweepy.Tweet):
        """
        Event listener for Tweet events in the HTTP long poll.
        """

        if time.time() - self.start_time > 60:
            print("Streaming Count is:", str(self.count))
            self.disconnect()
            return False

        if self.total_tweets_read % 10 == 0:
            print("Number of streamed tweets read is", self.total_tweets_read)
        tmp = dict(tweet.data)
        if "geo" in tmp.keys() and tmp["geo"] != {}:
            print("Geo available")
            suburb = ''
            if "place_id" in tmp["geo"] and "coordinates" not in tmp["geo"].keys():
                loc = tmp["geo"]["place_id"]
                location = self.api.geo_id(loc)
                tmp["geo"]["geo_location"] = {
                    "id" : location.id,
                    "url" : location.url,
                    "place_type" : location.place_type,
                    "name" : location.name,
                    "full_name" : location.full_name,
                    "country_code" : location.country_code,
                    "contained_within" : str(location.contained_within),
                    "geometry" : str(location.geometry),
                    "polylines" : str(location.polylines),
                    "centroid" : str(location.centroid),
                    "bounding_box" : str(location.bounding_box)
                }
                #Using the centroid:
                suburb = get_suburb(location.centroid)
                tmp["geo"]["suburb"] = suburb
            elif "coordinates" in tmp["geo"].keys():
                #Get the coordinates directly:
                suburb = get_suburb(tmp["geo"]["coordinates"])
                tmp["geo"]["suburb"] = suburb
            
        if tmp["id"] not in self.tweet_id_lst:
            tmp["day_of_week"] = tmp["created_at"].strftime("%A")
            tmp["year"] = tmp["created_at"].strftime("%Y")
            tmp["month"] = tmp["created_at"].strftime("%m")
            tmp["day"] = tmp["created_at"].strftime("%d")
            tmp["hour"] = tmp["created_at"].strftime("%H")

            if "created_at" in tmp.keys() and tmp["created_at"] != None:
                tmp["created_at"] = str(tmp["created_at"])
                tmp["city_rule_key"] = self.city_name
                tmp["topic_name"] = self.topic_name

                # duplicate update check.
                # we use the tweet ID from twitter as the primary key for rows
                # this prevents duplicates being written into the database
                # however it will make couchdb throw an error.
                try:
                    tmp = attach_sentiment(tmp)
                    self.twitter_stream[str(tmp["id"])] = tmp
                    self.tweet_id_lst.append(tmp["id"])
                    self.count += 1
                except Exception as e:
                    print("Exception B")
                    log(e, False)
                    pass
        self.total_tweets_read += 1

    def on_request_error(self, status_code):
        print(status_code)
        log(status_code, True)
        # rate limit error
        if status_code == 420 or status_code == 429:
            return False
        return False

    # def on_connection_error(self):
    #     self.disconnect()

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
    #First read in the shapefile.
    #This will be used to check if the Point objects are in Australia or not.
    shapefile = gpd.read_file("twitter/SA2_2021_AUST_SHP_GDA2020/SA2_2021_AUST_GDA2020.shp")
    #Then obtain the point as a Point object.
    pt = Point(tweet_coords[0], tweet_coords[1])
    #Now iterate through the shapes.
    count = 0
    suburb = ''
    for shape in shapefile.geometry:
        if shape != None:
            if shape.contains(pt) or shape.touches(pt):
                #surburb is determined:
                suburb = shapefile.SA2_NAME21[count]
                return suburb
        count += 1
     #In this case the location is outside Australia.
    return "ZZZZZZZZZ"

####

##The following functions are for the search method:
@app.route("/melbourne_test")
def main_search(id_lst, bearer_token, client, couchdb_server, city_name, topic, args):
    """
    Main non-streaming search function.
    """
    twitter_stream_search = None
    if "twitter_stream_envir" in couchdb_server:
        print("Use existing database")
        twitter_stream_search = couchdb_server["twitter_stream_envir"]
        print("Existing database used: twitter_stream_envir")

    elif "twitter_stream_envir" not in couchdb_server:
        print("Create new database")
        twitter_stream_search = couchdb_server.create("twitter_stream_envir")
        print("Database created: twitter_stream_envir")

    # vars related to searching
    search_client = tweepy.Client(bearer_token, wait_on_rate_limit=True)
    if topic == "environment":
        query = "(" + city_name + ' ' + topic + " OR nature OR sustainable OR bio OR plant OR green) - biology - party"
    elif topic == "transport":
        query = city_name + ' ' + topic + " OR bus OR (public transport) OR train OR tram"
    elif topic != "transport" and topic != "environment":
        query = city_name

    print("The query is", query)
    max_results = 100
    counter = 0
    total_tweets_read = 0

    resp = search_client.search_recent_tweets(
        query,
        max_results=max_results,
        tweet_fields=tweet_fields,
        user_fields=user_fields,
        expansions=expansions,
        media_fields=media_fields,
        place_fields=place_fields,
        poll_fields=poll_fields
    )
    print("Search counter at the start is", counter)

    try:
        while resp.meta["next_token"]:
            resp = search_client.search_recent_tweets(
                query,
                max_results=max_results,
                next_token=resp.meta["next_token"],
                tweet_fields=tweet_fields,
                user_fields=user_fields,
                expansions=expansions,
                media_fields=media_fields,
                place_fields=place_fields,
                poll_fields=poll_fields
            )
            total_tweets_read += max_results

            if resp.errors:
                raise RuntimeError(resp.errors)

            # successfully got data returned
            if resp.data:
                for tweet in resp.data:
                    tmp = dict(tweet)
                    if str(tmp["id"]) not in client.tweet_id_lst:
                        # print(tweet.__repr__())
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
                            suburb = ''
                            if "place_id" in tmp["geo"] and "coordinates" not in tmp["geo"].keys():
                                loc = tmp["geo"]["place_id"]
                                location = client.api.geo_id(loc)
                                tmp["geo"]["geo_location"] = {
                                    "id" : location.id,
                                    "url" : location.url,
                                    "place_type" : location.place_type,
                                    "name" : location.name,
                                    "full_name" : location.full_name,
                                    "country_code" : location.country_code,
                                    "contained_within" : str(location.contained_within),
                                    "geometry" : str(location.geometry),
                                    "polylines" : str(location.polylines),
                                    "centroid" : str(location.centroid),
                                    "bounding_box" : str(location.bounding_box)
                                }
                                #Now obtain the suburb:
                                #Using the centroid:
                                suburb = get_suburb(location.centroid)
                                tmp["geo"]["suburb"] = suburb
                            elif "coordinates" in tmp["geo"].keys():
                                #Get the coordinates directly:
                                suburb = get_suburb(tmp["geo"]["coordinates"])
                                tmp["geo"]["suburb"] = suburb
                        # duplicate update check.
                        # we use the tweet ID from twitter as the primary key for rows
                        # this prevents duplicates being written into the database
                        # however it will make couchdb throw an error.
                        try:
                            tmp = attach_sentiment(tmp)
                            twitter_stream_search[str(tmp["id"])] = tmp
                            (client.tweet_id_lst).append(str(tmp["id"]))
                            counter += 1
                        except Exception as e:
                            log(e, args.verbose)
                            pass
                        #twitter_stream_search.save(tmp)
                        # json.dump(tmp, fp)
            if counter % 100 == 0:
                log(f"search counter is {str(counter)}", args.debug)
    except KeyboardInterrupt:
        log("terminating due to received event", True)
        return [counter, total_tweets_read]
    except Exception or RuntimeError:
        print("Exception A")
        return False


@app.errorhandler(400)
def not_found(error):
    return make_response(jsonify({"error": "Bad request"}), 400)


@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({"error": "Not found"}), 404)


###


def read_stream(client, start_time):
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
        print("Stop the streaming")
        return client
    except Exception:
        print("Exception")
        return False


def main_stream(client, city_name="melbourne", topic="environment"):
    """
    Main function for streaming Tweets using the Twitter Streaming API.
    """
    # First obtain the necessary authorization data
    if topic == "environment":
        query = city_name + ' ' + topic
    elif topic == "transport":
        query = city_name + ' ' + topic
    elif topic != "transport" and topic != "environment":
        query = city_name
    print("The query is:", query)
    rules = [tweepy.StreamRule(value=query)]
    rule_regulation(client, rules)
    # https://developer.twitter.com/en/docs/twitter-api/tweets/filtered-stream/api-reference/get-tweets-search-stream-rules
    print(client.get_rules())
    start_time = time.time()
    result = read_stream(client, start_time)
    if result == False:
        #The cause is exceeding the rate limit.
        return False
    return [client.tweet_id_lst, client.count, client.total_tweets_read]


def do_work(twitter_credentials, args, couchdb_server, mode="stream"):
    """
    Does the main loop for the crawler.
    """
    streaming_no = 0
    search_no = 0
    total_tweets_read = 0
    total_tweets_obtained = 0

    total = []

    auth = OAuthHandler(twitter_credentials["consumer_key"], twitter_credentials["consumer_secret"])
    auth.set_access_token(twitter_credentials["access_token"], twitter_credentials["access_token_secret"])

    client = TweetListener(
        couchdb_server,
        args.city,
        args.topic,
        twitter_credentials["bearer_token"],
        auth,
        wait_on_rate_limit=True, 
    )

    if mode == "stream":
        log("running the streaming API", args.debug)
        val = main_stream(client, args.city, args.topic)
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

    return "todo: result goes here! This might be an error which we can recover from, such as hitting API limits"
