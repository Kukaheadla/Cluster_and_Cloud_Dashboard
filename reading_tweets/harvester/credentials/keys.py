"""
Contains some user functions.
"""


class User:
    def __init__(
        self,
        id,
        bearer_token,
        consumer_key,
        consumer_secret,
        access_token,
        access_token_secret,
    ):
        self.id = id
        self.bearer_token = bearer_token
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.access_token = access_token
        self.access_token_secret = access_token_secret
