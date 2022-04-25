import logging
from numpy import place #logging is used to track events that occur when the software runs.
from email.policy import default
from tokenize import String
from dotenv import load_dotenv
load_dotenv("config.env")

#Contains the main application code.
from concurrent.futures import process
import os, json, datetime
from flask import Flask, request, abort, make_response, url_for, jsonify
import pandas as pd
import tweepy, os, json, datetime
import pandas as pd

##Fields
tweet_fields = ["attachments", "author_id", "context_annotations", "conversation_id", "created_at", "entities", "geo", "lang", "id", "text"]
user_fields = ["name", "username", "location", "verified", "description"]
expansions = ["author_id", "entities.mentions.username", "geo.place_id"]
place_fields = ["contained_within", "country", "country_code", "geo", "name", "full_name"]
##

#authorisation data:
bearer_token = os.getenv("TWITTER_BEARER_TOKEN")
consumer_key = os.environ.get("TWITTER_API_KEY")
consumer_secret = os.environ.get("TWITTER_API_KEY_SECRET")
access_token = os.environ.get("TWITTER_ACCESS_TOKEN")
access_token_secret = os.environ.get("TWITTER_ACCESS_SECRET")
##

#An optional file to read the tweets to:
fp = open("tweets.json", "a")

app = Flask(__name__, static_url_path="")

class TweetListener(tweepy.StreamingClient):
    """
    StreamingClient allows filtering and sampling of realtime Tweets using Twitter API v2.
    https://docs.tweepy.org/en/latest/streamingclient.html#tweepy.StreamingClient
    """
    count = 0
    limit = 1
    result = []
    tweet_dict = {}
    #Defining some variables:
    def on_tweet(self, tweet: tweepy.Tweet):
        tmp = dict(tweet.data)
        if self.limit >= self.count and TweetListener.count >= TweetListener.limit:
            self.disconnect()
            return False
        elif 'created_at' in tmp.keys() and tmp['created_at'] != None:
            tmp['created_at'] = str(tmp['created_at'])
            #json.dump(tmp, fp)
            (TweetListener.result).append(tmp)
            print(tweet.__repr__()) #Prints out content of the tweet.
            TweetListener.count += 1

    def on_request_error(self, status_code):
        print(status_code)

    def on_connection_error(self):
        self.disconnect()

def rule_regulation(client, rules):

    #remove existing rules
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
@app.route('/melbourne_test')
def main_search(tweet_lst):
    tweets = []
    client = tweepy.Client(bearer_token)
    query = "melbourne"

    max_results = 10
    limit = 10
    counter = 0

    resp = client.search_recent_tweets(query, max_results=max_results, tweet_fields = tweet_fields, user_fields = user_fields)
    #print(len(resp.includes["geo.place_id"]))
    if resp.errors:
        raise RuntimeError(resp.errors)
    #with open("output.json", "w") as file: 
    if resp.data:
        for tweet in resp.data:
            tmp = dict(resp.data[counter])
            print(tweet.__repr__())
            tmp['created_at'] = str(tmp['created_at'])
            tweet_lst.append(tmp)
            #json.dump(tmp, fp)
            counter += 1

    while resp.meta["next_token"] and counter < limit:
        resp = client.search_recent_tweets(query, max_results=max_results, next_token=resp.meta["next_token"], 
            tweet_fields = tweet_fields, user_fields = user_fields)
        #print(resp)
        if resp.errors:
            raise RuntimeError(resp.errors)
        if resp.data:
            for tweet in resp.data:
                tmp = dict(resp.data[counter])
                print(tweet.__repr__())
                tmp['created_at'] = str(tmp['created_at'])
                tweet_lst.append(tmp)
                #json.dump(tmp, fp)
                counter += 1
    #temp = {"new_edits" : False, "docs" : tweets}
    return tweet_lst

@app.errorhandler(400)
def not_found(error):
    return make_response(jsonify({'error': 'Bad request'}), 400)


@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)
###

def read_stream(client):
    print("function read_stream")
    try:
        # https://developer.twitter.com/en/docs/twitter-api/tweets/filtered-stream/api-reference/get-tweets-search-stream
        client.filter(expansions=expansions, place_fields=place_fields, tweet_fields=tweet_fields, user_fields=user_fields, threaded=False)
    except KeyboardInterrupt or Exception: 
        return

def main_stream():
    #First obtain the necessary authorization data
    if not bearer_token:
        raise RuntimeError("Not found bearer token")

    client = TweetListener(bearer_token)

    rules = [
            tweepy.StreamRule(value="melbourne")
    ]   
    rule_regulation(client, rules)
    # https://developer.twitter.com/en/docs/twitter-api/tweets/filtered-stream/api-reference/get-tweets-search-stream-rules
    print(client.get_rules())
    read_stream(client)
    return client.result
    

if __name__ == "__main__":
    """
     - Save it in a secure location
     - Treat it like a password or a set of keys
     - If security has been compromised, regenerate it
     - DO NOT store it in public places or shared docs
    """
    tmp = main_stream()
    print("Now run the search API")
    main_search(tmp)
    json.dump(tmp, fp)
    fp.close()
    print("Complete")
    #Search at the same time.


