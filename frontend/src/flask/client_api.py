"""
This file contains endpoints and functions relating to client access to the cloud infrastructure. The RESTful api here can be queried
to e.g. return tweets, or aggregate statistics from couchdb.
"""

from flask import Blueprint
from couchdb import Server
from flaskext.couchdb import Document

couchDBServer = Server()

api_bp = Blueprint("api", __name__)


@api_bp.route("/tweet/")
def get_tweet():
    return "I am a tweet!"


@api_bp.route("/sentiments/suburb", methods=["GET"])
def suburb_sentiment():
    suburb_name = request.args.get("suburb", "")
    # request to couchDB
    return "happy"
