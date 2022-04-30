import logging
from numpy import (
    place,
)  # logging is used to track events that occur when the software runs.
from email.policy import default
from tokenize import String
from credentials.keys import User

# Contains the main application code.
from concurrent.futures import process
import os, json, datetime, couchdb, time
from flask import Flask, request, abort, make_response, url_for, jsonify
import pandas as pd
import tweepy, os, json, datetime
import pandas as pd
from logger.logger import log

##Fields
tweet_fields = [
    "attachments",
    "author_id",
    "context_annotations",
    "conversation_id",
    "created_at",
    "entities",
    "geo",
    "lang",
    "id",
    "text",
]
user_fields = ["name", "username", "location", "verified", "description"]
expansions = ["author_id", "entities.mentions.username", "geo.place_id"]
place_fields = [
    "contained_within",
    "country",
    "country_code",
    "geo",
    "name",
    "full_name",
]

# CouchDB connections
##
couch = couchdb.Server("http://admin:password@localhost:5984/")

if "twitter_stream" in couch:
    twitter_stream = couch["twitter_stream"]
    print("Existing database used: twitter_stream")

elif "twitter_stream" not in couch:
    twitter_stream = couch.create("twitter_stream")
    print("Database created: twitter_stream")


ids = ["893542"]

# An optional file to read the tweets to:

app = Flask(__name__, static_url_path="")

# TweetListener(twitter_credentials["bearer_token"], wait_on_rate_limit=True)
class TweetListener(tweepy.StreamingClient):
    """
    StreamingClient allows filtering and sampling of realtime Tweets using Twitter API v2.
    https://docs.tweepy.org/en/latest/streamingclient.html#tweepy.StreamingClient
    """

    count = 0
    total_tweets_read = 0
    tweet_id_lst = []
    start_time = time.time()

    # Defining some variables:
    def on_tweet(self, tweet: tweepy.Tweet):

        if time.time() - self.start_time > 60:
            print("Streaming Count is:", str(self.count))
            self.disconnect()
            return False

        if self.total_tweets_read % 10 == 0:
            print("Number of streamed tweets read is", self.total_tweets_read)
        tmp = dict(tweet.data)
        if tmp["id"] not in self.tweet_id_lst:
            tmp["created_at"] = str(tmp["created_at"])
            if "created_at" in tmp.keys() and tmp["created_at"] != None:
                tmp["created_at"] = str(tmp["created_at"])
                twitter_stream.save(tmp)
                self.tweet_id_lst.append(tmp["id"])
                self.count += 1
        self.total_tweets_read += 1

    def on_request_error(self, status_code):
        print(status_code)

    def on_connection_error(self):
        self.disconnect()


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


##The following functions are for the search method:
@app.route("/melbourne_test")
def main_search(id_lst, bearer_token, client, couchdb_server):
    """
    Main non-streaming search function.
    """
    twitter_stream_search = None
    if "twitter_stream" in couch:
        twitter_stream_search = couchdb_server["twitter_stream"]
        print("Existing database used: twitter_stream")

    elif "twitter_stream" not in couch:
        twitter_stream_search = couchdb_server.create("twitter_stream")
        print("Database created: twitter_stream")

    search_client = tweepy.Client(bearer_token, wait_on_rate_limit=True)
    query = "melbourne"

    max_results = 100
    counter = 0
    total_tweets_read = 0

    resp = search_client.search_recent_tweets(
        query,
        max_results=max_results,
        tweet_fields=tweet_fields,
        user_fields=user_fields,
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
            )
            total_tweets_read += max_results

            if resp.errors:
                raise RuntimeError(resp.errors)

            if resp.data:
                for tweet in resp.data:
                    tmp = dict(tweet)
                    # todo: remove duplicates purely by using couchDB's functionality
                    # as checking like this will not work if multiple harvesters are working simultaneously
                    if str(tmp["id"]) not in client.tweet_id_lst:
                        # print(tweet.__repr__())
                        tmp["created_at"] = str(tmp["created_at"])
                        # First check if the ids match:
                        twitter_stream_search.save(tmp)
                        (client.tweet_id_lst).append(str(tmp["id"]))
                        # json.dump(tmp, fp)
                        counter += 1
            if counter % 100 == 0:
                print("Search counter is", counter)
    except KeyboardInterrupt or Exception or RuntimeError:
        print("Stop the searching API")
        return [counter, total_tweets_read]


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
            threaded=False,
        )
    except KeyboardInterrupt or Exception:
        print("Stop the streaming")
        return


def main_stream(client, city_name="melbourne"):
    """
    Main function for streaming Tweets using the Twitter Streaming API.
    """
    # First obtain the necessary authorization data

    rules = [tweepy.StreamRule(value=city_name)]
    rule_regulation(client, rules)
    # https://developer.twitter.com/en/docs/twitter-api/tweets/filtered-stream/api-reference/get-tweets-search-stream-rules
    print(client.get_rules())
    start_time = time.time()
    read_stream(client, start_time)
    return [client.tweet_id_lst, client.count, client.total_tweets_read]


def do_work(twitter_credentials, args, couchdb_server, mode="search"):
    """
    Does the main loop for the crawler.
    """
    streaming_no = 0
    search_no = 0
    total_tweets_read = 0
    total_tweets_obtained = 0

    total = []
    for value in ids:

        client = TweetListener(
            twitter_credentials["bearer_token"], wait_on_rate_limit=True
        )

        if mode == "stream":
            log("running the streaming API", args.debug)
            val = main_stream(client, args.city)
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
                [], twitter_credentials["bearer_token"], client, couchdb_server
            )
            log(
                f"Total number of tweets read for search API is {str(search_result[1])}\nTotal number of unique tweets obtained for search API is {str(search_result[0])}",
                args.debug,
            )
            total_tweets_obtained += search_result[0]
            total_tweets_read += search_result[1]

            print("Complete for id", str(value))
            print("Total number of tweets read", str(search_result[1]))
            print("Total number of unique tweets obtained:", search_result[0])

    # Print the results:
    print("Number of tweets read", str(total_tweets_read))
    print("Number of valid tweets obtained", str(total_tweets_obtained))
