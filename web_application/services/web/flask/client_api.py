"""
This file contains endpoints and functions relating to client access to the cloud infrastructure. The RESTful api here can be queried
to e.g. return tweets, or aggregate statistics from couchdb.
"""

from flask import Blueprint, request
from couchdb import Server
import requests
import json
import os
# couchDB anonymous server connection

username = "admin"
password = "password"

couchserver = Server(f"{os.getenv('COUCHDB_DATABASE')}/")
for dbname in couchserver:
    # print(dbname)
    pass

db = couchserver["test"]

api_bp = Blueprint("api", __name__)

def get_tweet_n(id):
    return db[id]

@api_bp.route("/tweets/latest/")
def get_latest_tweets():
    r = requests.get(f"{os.getenv('COUCHDB_DATABASE')}/test/_changes?descending=true&limit=10")
    # print(json.loads(r.content)["results"][0])
    return r.content

@api_bp.route("/tweet/")
def get_tweet():
    tweet_id = request.args.get("id")
    return db[tweet_id]


@api_bp.route("/sentiments/suburb", methods=["GET"])
def suburb_sentiment():
    suburb_name = request.args.get("suburb", "")
    # request to couchDB
    return "happy"
