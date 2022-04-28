import logging
from numpy import place #logging is used to track events that occur when the software runs.
from email.policy import default
from tokenize import String

##
from keys import _keys, User
##
from dotenv import load_dotenv
load_dotenv("config.env")

#Contains the main application code.
from concurrent.futures import process
import os, json, datetime, couchdb
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
ids = ["893542"]

#An optional file to read the tweets to:
fp = open("tweets_draft2.json", "w")

app = Flask(__name__, static_url_path="")

class TweetListener(tweepy.StreamingClient):
    """
    StreamingClient allows filtering and sampling of realtime Tweets using Twitter API v2.
    https://docs.tweepy.org/en/latest/streamingclient.html#tweepy.StreamingClient
    """
    count = 0
    limit = 0
    total_tweets_read = 0
    result = []
    tweet_id_lst = []
    #Defining some variables:
    def on_tweet(self, tweet: tweepy.Tweet):
        if self.total_tweets_read % 100 == 0:
            print("Number of tweets read is", self.total_tweets_read)
        tmp = dict(tweet.data)
        if self.limit >= self.count:
            if tmp["id"] not in self.tweet_id_lst: 
                #print(tweet.__repr__())
                tmp['created_at'] = str(tmp['created_at'])
                if 'created_at' in tmp.keys() and tmp['created_at'] != None:
                    tmp['created_at'] = str(tmp['created_at'])
                    #json.dump(tmp, fp)
                    (TweetListener.result).append(tmp)
                    self.tweet_id_lst.append(tmp["id"])
                    self.count += 1
        self.total_tweets_read += 1
        if self.limit < self.count:
            print("Streaming Count is:", str(self.count))
            self.disconnect()
            return False

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
def main_search(tweet_lst, id_lst, search_no, bearer_token):
    
    client = tweepy.Client(bearer_token, wait_on_rate_limit=True)
    query = "melbourne"

    max_results = 100
    limit = search_no
    counter = 0
    total_tweets_read = 0

    resp = client.search_recent_tweets(query, max_results=max_results, tweet_fields = tweet_fields, user_fields = user_fields)
    print("Search counter at the start is", counter)

    #print(len(resp.includes["geo.place_id"]))
    if resp.errors:
        raise RuntimeError(resp.errors)
    #with open("output.json", "w") as file: 
    if resp.data:
        for tweet in resp.data:
            tmp = dict(resp.data[counter])
            #Check to see if the tweet has been posted before:
            if str(tmp["id"]) not in id_lst:
                #print(tweet.__repr__())
                tmp['created_at'] = str(tmp['created_at'])
                #Need to check if the ids match:
                tweet_lst.append(tmp)
                id_lst.append(str(tmp["id"]))
                #json.dump(tmp, fp)
                counter += 1
            total_tweets_read += 1

    print("Search counter is", counter)       
    while resp.meta["next_token"] and counter < limit:
        if (limit - counter >= max_results):
            resp = client.search_recent_tweets(query, max_results=max_results, next_token=resp.meta["next_token"], 
            tweet_fields = tweet_fields, user_fields = user_fields)
            total_tweets_read += max_results

        elif (limit - counter <  max_results):
            resp = client.search_recent_tweets(query, max_results=limit-counter, next_token=resp.meta["next_token"], 
            tweet_fields = tweet_fields, user_fields = user_fields)
            total_tweets_read += limit-counter

        if resp.errors:
            raise RuntimeError(resp.errors)

        if resp.data:
            for tweet in resp.data:
                tmp = dict(tweet)
                if str(tmp["id"]) not in id_lst:
                    #print(tweet.__repr__())
                    tmp['created_at'] = str(tmp['created_at'])
                    #First check if the ids match:
                    tweet_lst.append(tmp)
                    id_lst.append(str(tmp["id"]))
                    #json.dump(tmp, fp)
                    counter += 1
        print("Search counter is", counter) 
    #temp = {"new_edits" : False, "docs" : tweets}
    return [tweet_lst, counter, total_tweets_read]

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

def main_stream(streaming_no, bearer_token):
    #First obtain the necessary authorization data
    if not bearer_token:
        raise RuntimeError("Not found bearer token")

    client = TweetListener(bearer_token, wait_on_rate_limit=True)
    client.limit = streaming_no

    rules = [
            tweepy.StreamRule(value="melbourne")
    ]   
    rule_regulation(client, rules)
    # https://developer.twitter.com/en/docs/twitter-api/tweets/filtered-stream/api-reference/get-tweets-search-stream-rules
    print(client.get_rules())
    read_stream(client)
    return [client.result, client.tweet_id_lst]
    

if __name__ == "__main__":
    """
     - Save it in a secure location
     - Treat it like a password or a set of keys
     - If security has been compromised, regenerate it
     - DO NOT store it in public places or shared docs
    """
    streaming_no = 100
    search_no = 500
    total_tweets_read = 0
    total_tweets_obtained = 0

    total = []
    for value in ids: 
        print("User is", str(value))
        person = User(value, _keys[value]["bearer_token"], _keys[value]["consumer_key"], _keys[value]["consumer_secret"], 
            _keys[value]["access_token"], _keys[value]["access_token_secret"]) 
        tmp = []

        val = main_stream(streaming_no, person.bearer_token)
        tmp = val[0]
        id_lst = val[1]
        print("Now run the search API")

        search_result = main_search(tmp, id_lst, search_no, person.bearer_token)

        total_tweets_obtained += search_result[1]
        total_tweets_read += search_result[2]
        total.extend(search_result[0])

        print("Complete for id", str(value))
        print("Total number of tweets read", str(search_result[2]))
        print("Total number of unique tweets obtained:", search_result[1])

    #Print the results:
    print("Number of tweets read", str(total_tweets_read))
    print("Number of valid tweets obtained", str(total_tweets_obtained))
    json.dump({"docs": total}, fp)
    fp.close()
