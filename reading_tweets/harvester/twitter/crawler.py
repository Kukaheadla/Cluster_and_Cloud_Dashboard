"""
Main crawler application which can do one of two things:
    - stream data via the Twitter API, that is, look at real time tweets and write them to the database
    - perform a search back into the past seven days and write those tweets into the database

The functions found here all relate to the Twitter API and crucially, what specific fields and data
we wish to extract from the API.

The main loop of the application should not be performed here. For example, if the credentials used encounter the daily limit
or the monthly account limit, that error should be passed back to the main module, and called with new credentials.

Authors: David, Alex
"""
from numpy import (
    place,
)
from flask import Flask, make_response, jsonify
import tweepy
import time
from logger.logger import log

# tweet fields that we want returned in the Twitter API response
tweet_fields = [
    "attachments",
    "author_id",
    "context_annotations",
    "conversation_id",
    "created_at",
    "entities",
    "geo",
    "lang",
    "id",
    "text",
]
user_fields = ["name", "username", "location", "verified", "description"]
expansions = ["author_id", "entities.mentions.username", "geo.place_id"]
place_fields = [
    "contained_within",
    "country",
    "country_code",
    "geo",
    "name",
    "full_name",
]

"""
Flask application for optional use. Does not need to be run as a server unless you want to create some custom views etc.
"""
app = Flask(__name__, static_url_path="")


class TweetListener(tweepy.StreamingClient):
    """
    StreamingClient allows filtering and sampling of realtime Tweets using Twitter API v2.
    https://docs.tweepy.org/en/latest/streamingclient.html#tweepy.StreamingClient
    """

    count = 0
    total_tweets_read = 0
    tweet_id_lst = []
    start_time = time.time()

    def __init__(self, couchdb_server, city_name, twitter_bearer_token, **kwargs):
        """
        Creates a Tweetlistener which will listen for a certain amount of time.
        Including our own override so we can use the couchdb server defined in main.py
        """
        super().__init__(twitter_bearer_token, **kwargs)
        self.couchdb_server = couchdb_server
        self.city_name = city_name
        if "twitter_stream" in self.couchdb_server:
            self.twitter_stream = self.couchdb_server["twitter_stream"]

        elif "twitter_stream" not in self.couchdb_server:
            self.twitter_stream = self.couchdb_server.create("twitter_stream")

    # Defining some variables:
    def on_tweet(self, tweet: tweepy.Tweet):
        """
        Event listener for Tweet events in the HTTP long poll.
        """

        if time.time() - self.start_time > 60:
            print("Streaming Count is:", str(self.count))
            self.disconnect()
            return False

        if self.total_tweets_read % 10 == 0:
            print("Number of streamed tweets read is", self.total_tweets_read)
        tmp = dict(tweet.data)
        if tmp["id"] not in self.tweet_id_lst:
            tmp["created_at"] = str(tmp["created_at"])
            if "created_at" in tmp.keys() and tmp["created_at"] != None:
                tmp["created_at"] = str(tmp["created_at"])
                tmp["city_rule_key"] = self.city_name

                # duplicate update check.
                # we use the tweet ID from twitter as the primary key for rows
                # this prevents duplicates being written into the database
                # however it will make couchdb throw an error.
                try:
                    self.twitter_stream[str(tmp["id"])] = tmp
                except Exception as e:
                    log(e, False)
                    pass

                self.tweet_id_lst.append(tmp["id"])
                self.count += 1
        self.total_tweets_read += 1

    def on_request_error(self, status_code):
        print(status_code)

    # def on_connection_error(self):
    #     self.disconnect()


def rule_regulation(client, rules):

    # remove existing rules
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
@app.route("/melbourne_test")
def main_search(id_lst, bearer_token, client, couchdb_server, city_name, args):
    """
    Main non-streaming search function.
    """
    twitter_stream_search = None
    if "twitter_stream" in couchdb_server:
        twitter_stream_search = couchdb_server["twitter_stream"]
        print("Existing database used: twitter_stream")

    elif "twitter_stream" not in couchdb_server:
        twitter_stream_search = couchdb_server.create("twitter_stream")
        print("Database created: twitter_stream")

    # vars related to searching
    search_client = tweepy.Client(bearer_token, wait_on_rate_limit=True)
    query = city_name

    max_results = 100
    counter = 0
    total_tweets_read = 0

    resp = search_client.search_recent_tweets(
        query,
        max_results=max_results,
        tweet_fields=tweet_fields,
        user_fields=user_fields,
    )
    print("Search counter at the start is", counter)

    try:
        while resp.meta["next_token"]:
            resp = search_client.search_recent_tweets(
                query,
                max_results=max_results,
                next_token=resp.meta["next_token"],
                tweet_fields=tweet_fields,
                user_fields=user_fields,
            )
            total_tweets_read += max_results

            if resp.errors:
                raise RuntimeError(resp.errors)

            # successfully got data returned
            if resp.data:
                for tweet in resp.data:
                    tmp = dict(tweet)
                    if str(tmp["id"]) not in client.tweet_id_lst:
                        # print(tweet.__repr__())
                        tmp["created_at"] = str(tmp["created_at"])
                        tmp["city_rule_key"] = city_name
                        # duplicate update check.
                        # we use the tweet ID from twitter as the primary key for rows
                        # this prevents duplicates being written into the database
                        # however it will make couchdb throw an error.
                        try:
                            twitter_stream_search[str(tmp["id"])] = tmp
                        except Exception as e:
                            log(e, args.verbose)
                            pass

                        # twitter_stream_search.save(tmp)
                        (client.tweet_id_lst).append(str(tmp["id"]))
                        # json.dump(tmp, fp)
                        counter += 1
            if counter % 100 == 0:
                log(f"search counter is {str(counter)}", args.debug)
    except KeyboardInterrupt or Exception or RuntimeError:
        log("terminating due to received event", True)
        return [counter, total_tweets_read]


@app.errorhandler(400)
def not_found(error):
    return make_response(jsonify({"error": "Bad request"}), 400)


@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({"error": "Not found"}), 404)


###


def read_stream(client, start_time):
    try:
        # https://developer.twitter.com/en/docs/twitter-api/tweets/filtered-stream/api-reference/get-tweets-search-stream
        client.filter(
            expansions=expansions,
            place_fields=place_fields,
            tweet_fields=tweet_fields,
            user_fields=user_fields,
            threaded=False,
        )
    except KeyboardInterrupt or Exception:
        print("Stop the streaming")
        return


def main_stream(client, city_name="melbourne"):
    """
    Main function for streaming Tweets using the Twitter Streaming API.
    """
    # First obtain the necessary authorization data

    rules = [tweepy.StreamRule(value=city_name)]
    rule_regulation(client, rules)
    # https://developer.twitter.com/en/docs/twitter-api/tweets/filtered-stream/api-reference/get-tweets-search-stream-rules
    print(client.get_rules())
    start_time = time.time()
    read_stream(client, start_time)
    return [client.tweet_id_lst, client.count, client.total_tweets_read]


def do_work(twitter_credentials, args, couchdb_server, mode="stream"):
    """
    Does the main loop for the crawler.
    """
    streaming_no = 0
    search_no = 0
    total_tweets_read = 0
    total_tweets_obtained = 0

    total = []

    client = TweetListener(
        couchdb_server, args.city, twitter_credentials["bearer_token"], wait_on_rate_limit=True
    )

    if mode == "stream":
        log("running the streaming API", args.debug)
        val = main_stream(client, args.city)
        id_lst = val[0]
        log(
            f"Total number of tweets read for streaming API is {str(val[2])}\nTotal number of unique tweets obtained for streaming API is {str(val[1])}",
            args.debug,
        )
        total_tweets_obtained += val[1]
        total_tweets_read += val[2]

    if mode == "search":
        log("running the search API", args.debug)
        search_result = main_search(
            [],
            twitter_credentials["bearer_token"],
            client,
            couchdb_server,
            args.city,
            args,
        )
        log(
            f"Total number of tweets read for search API is {str(search_result[1])}\nTotal number of unique tweets obtained for search API is {str(search_result[0])}",
            args.debug,
        )
        total_tweets_obtained += search_result[0]
        total_tweets_read += search_result[1]
        print("Total number of tweets read", str(search_result[1]))
        print("Total number of unique tweets obtained:", search_result[0])

    # Print the results:
    print("Number of tweets read", str(total_tweets_read))
    print("Number of valid tweets obtained", str(total_tweets_obtained))

    return "todo: result goes here! This might be an error which we can recover from, such as hitting API limits"
