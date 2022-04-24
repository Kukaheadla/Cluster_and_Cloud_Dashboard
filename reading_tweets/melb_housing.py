from email.policy import default
from tokenize import String
from dotenv import load_dotenv
load_dotenv("config.env")
#Contains the main application code.
from concurrent.futures import process
import tweepy, os, json, datetime
from tweepy import Client
from flask import Flask, request, abort, make_response, url_for, jsonify
import pandas as pd

app = Flask(__name__, static_url_path="")

consumer_key = os.environ.get("TWITTER_API_KEY")
consumer_secret = os.environ.get("TWITTER_API_KEY_SECRET")
access_token = os.environ.get("TWITTER_ACCESS_TOKEN")
access_token_secret = os.environ.get("TWITTER_ACCESS_SECRET")
bearer_token = os.getenv("TWITTER_BEARER_TOKEN")
tweet_fields = ["attachments", "author_id", "context_annotations", "conversation_id", "created_at", "entities", "geo", "lang", "id", "text"]
user_fields = ["name", "username", "location", "verified", "description"]
expansions = ["author_id", "entities.mentions.username", "geo.place_id"]
place_fields = ["contained_within", "country", "country_code", "geo", "name", "full_name"]


@app.route('/melbourne_test')
def melb_test():

    tweets = []
    client = Client(bearer_token)
    query = "melbourne"

    max_results = 10
    limit = 10
    counter = 0

    resp = client.search_recent_tweets(query, max_results=max_results, tweet_fields = tweet_fields, user_fields = user_fields)
    #print(len(resp.includes["geo.place_id"]))
    if resp.errors:
        raise RuntimeError(resp.errors)
    with open("output.json", "a") as file: 
        if resp.data:
            for tweet in resp.data:
                tmp = dict(resp.data[counter])
                print(tmp)
                tmp['created_at'] = str(tmp['created_at'])
                tweets.append(tmp)
                #json.dump(tmp, file)
                #print(tweet.__repr__())
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
                    print(tmp)
                    tmp['created_at'] = str(tmp['created_at'])
                    tweets.append(tmp)
                    #tweets.append(json.dumps(dict(resp.data[counter]), cls=DateTimeEncoder))
                    #json.dump(tmp)
                    #print(tweet.__repr__())
                    counter += 1
    file.close()
    temp = {"new_edits" : False, "docs" : tweets}
    return temp

@app.errorhandler(400)
def not_found(error):
    return make_response(jsonify({'error': 'Bad request'}), 400)


@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)

if __name__ == '__main__':
    app.run(debug=True)
