"""
This file serves as the entry point to the crawler application.

This file is essentially a dispatch point for various options relating to crawling Tweets.
You can set various modes, and pass in particular relevant keys.
"""

import argparse
import couchdb
import sys
from twitter.crawler import do_work
from logger.logger import log



if __name__ == "__main__":
    parser = argparse.ArgumentParser("main")
    parser.add_argument(
        "--couchdb-host", help="IP:Port", type=str, required=True
    )
    parser.add_argument(
        "--couchdb-username", help="username of couchdb", type=str, required=False, default="user"
    )
    parser.add_argument(
        "--couchdb-password", help="password of couchdb user", type=str, required=False, default="password"
    )
    parser.add_argument(
        "--credentials-id", help="credentials ID number", type=int, required=True
    )
    parser.add_argument(
        "--city", help="city topic, e.g. melbourne or sydney", type=str, required=True
    )
    parser.add_argument(
        "--mode", help="e.g. stream or search", type=str, required=True
    )
    parser.add_argument(
        "-o",
        help="specify an output file for returned Tweets.",
        type=str,
        required=False,
    )
    parser.add_argument(
        "--debug", help="enables debug logging", action="store_const", const=True
    )
    args = parser.parse_args()

    # connect to couchdb server
    couchdb_server = couchdb.Server(f"http://{args.couchdb_username}:{args.couchdb_password}@{args.couchdb_host}/")

    # get Twitter credentials from CouchDB table
    # in the DB it should look like the following in a credentials table:
    """
    {
        "_id": "twitter_credentials",
        "_rev": "2-f73b7adb1009d392f0d0caca53b86adb",
        "val": [
            {
            "consumer_key": "<example_key>",
            "bearer_token": "<bearer_token>",
            <rest_of_credentials>
            }
        ]
        }
    """
    doc_id = "twitter_credentials"
    credentials_server = couchdb_server["credentials"]
    doc = credentials_server["twitter_credentials"]
    twitter_credentials = None

    # attempt to find the credentials by position. If this is server 0 and that was the ID passed in,
    # then we will attempt to use the credentials at array position 0 in the twitter_credentials record in couchDB.
    try:
        twitter_credentials = doc["val"][args.credentials_id]
    except IndexError:
        log(f"No credentials object found at index {str(args.credentials_id)}",True)
        sys.exit() # cannot do anything further, so quit.
    log(twitter_credentials, args.debug)
    
    if args.mode.lower() == "stream":
        # do some streaming
        # this will run until terminated, or an API error is encountered from which we cannot recover
        log("streaming", args.debug)
        do_work(twitter_credentials, args, couchdb_server, mode="stream")
    elif args.mode.lower() == "search":
        # do some searching
        # this will also run until terminated or an API error etc.
        log("searching", args.debug)
        do_work(twitter_credentials, args,couchdb_server, mode="search")
