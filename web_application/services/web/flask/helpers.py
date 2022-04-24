import requests
import json
import os

username = "admin"
password = "password"


def get_latest_tweets():
    r = requests.get(
        f"{os.getenv('COUCHDB_DATABASE')}/test/_changes?descending=true&limit=30"
    )
    return json.loads(r.content)
