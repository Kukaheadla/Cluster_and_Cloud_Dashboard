"""
This file contains endpoints and functions relating to client access to the cloud infrastructure. The RESTful api here can be queried
to e.g. return tweets, or aggregate statistics from couchdb.
"""

from flask import Blueprint, request
from couchdb import Server
import requests
import json
import os
from collections import defaultdict

# couchDB anonymous server connection

username = "admin"
password = "password"

couchserver = Server(f"{os.getenv('COUCHDB_DATABASE')}/")
for dbname in couchserver:
    # print(dbname)
    pass

db = couchserver["test"]

api_bp = Blueprint("api", __name__)


# api functions and routes below
# @api_bp.route("/tweets/languages_by_time/")
def get_languages_by_time_view():
    """
    map:
        function (document) {
            const [day, month, month_date, time, offset, year] = document.key.doc.created_at.split(" ");
            const lang = document.key.doc.lang;
            emit([lang, year, month, month_date], 1);
        }
    reduce:
        _count

    also see: https://blog.pablobm.com/2019/07/18/map-reduce-with-couchdb-a-visual-primer.html
    """
    acc = defaultdict(lambda: defaultdict(lambda: 0))
    # example of iterating a view
    for item in db.view("_design/LanguageInfo/_view/TestView", group=True, group_level=4):
        # where the positions of the keys are derived from the order in the 'emit' function in couchdb
        date_key = f"{item['key'][1]}-{item['key'][2]}-{item['key'][3]}"
        lang = item['key'][0]
        acc[date_key][lang] = acc[date_key][lang] + item['value']
    return acc


def get_tweet_n(id):
    return db[id]


@api_bp.route("/tweets/latest/")
def get_latest_tweets():
    r = requests.get(
        f"{os.getenv('COUCHDB_DATABASE')}/test/_changes?descending=true&limit=10"
    )
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


@api_bp.route("/external_service_acess_confirmation", methods=["GET"])
def external_service_acess_confirmation():
    r = requests.get("http://172.26.128.165/wp-admin/install.php")
    return r.content
