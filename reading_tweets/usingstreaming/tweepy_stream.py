import logging
from numpy import place #logging is used to track events that occur when the software runs.
from tweepy import StreamingClient, StreamRule, Tweet, Cursor
from email.policy import default
from tokenize import String
from dotenv import load_dotenv
load_dotenv("config.env")

#Contains the main application code.
from concurrent.futures import process
import os, json, datetime
from flask import Flask
import pandas as pd

##Fields
tweet_fields = ["attachments", "author_id", "context_annotations", "conversation_id", "created_at", "entities", "geo", "lang", "id", "text"]
user_fields = ["name", "username", "location", "verified", "description"]
expansions = ["author_id", "entities.mentions.username", "geo.place_id"]
place_fields = ["contained_within", "country", "country_code", "geo", "name", "full_name"]
##

app = Flask(__name__, static_url_path="")
fp = open("output.json", "a")

class TweetListener(StreamingClient):
    """
    StreamingClient allows filtering and sampling of realtime Tweets using Twitter API v2.
    https://docs.tweepy.org/en/latest/streamingclient.html#tweepy.StreamingClient
    """
    count = 0
    limit = 5
    result = []
    tweet_dict = {}
    #Defining some variables:
    def on_tweet(self, tweet: Tweet):
        tmp = dict(tweet.data)
        print(tmp)
        if 'created_at' in tmp.keys() and tmp['created_at'] != None:
            tmp['created_at'] = str(tmp['created_at'])
        #json.dump(dict(tmp), fp, cls=DateTimeEncoder)
        (TweetListener.result).append(tmp)
        print(tweet.__repr__()) #Prints out content of the tweet.
        TweetListener.count += 1
        if TweetListener.count >= TweetListener.limit:
            json.dump(TweetListener.result, fp)
            self.disconnect()

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
    
def main():
    #First obtain the necessary authorization data
    bearer_token = os.getenv("TWITTER_BEARER_TOKEN")

    if not bearer_token:
        raise RuntimeError("Not found bearer token")

    client = TweetListener(bearer_token)

    rules = [
            StreamRule(value="melbourne")
    ]   
    rule_regulation(client, rules)
    # https://developer.twitter.com/en/docs/twitter-api/tweets/filtered-stream/api-reference/get-tweets-search-stream-rules
    print(client.get_rules())

    # https://developer.twitter.com/en/docs/twitter-api/tweets/filtered-stream/api-reference/get-tweets-search-stream
    client.filter(expansions=expansions, place_fields=place_fields, tweet_fields=tweet_fields, user_fields=user_fields, threaded=True)

if __name__ == "__main__":
    """
     - Save it in a secure location
     - Treat it like a password or a set of keys
     - If security has been compromised, regenerate it
     - DO NOT store it in public places or shared docs
    """
    main()
