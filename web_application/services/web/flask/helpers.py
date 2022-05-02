"""
Author: Alex T

This file contains miscellaneous helper functions.
Any function which does not have a clear place elsewhere in the project can go here.
"""
import requests
import json
import os

username = "admin"
password = "password"


def get_latest_tweets():
    r = requests.get(
        f"{os.getenv('COUCHDB_DATABASE')}/test2/_changes?descending=true&limit=30"
    )
    return json.loads(r.content)
