"""
Author: Alex T

This file contains endpoints and functions relating to serving the application directly to users.
Here we register the blueprints (routes and their handlers) at an overall application level.

Note well: this is not the file to run with flask, you want to run wsgi.py.
"""

from os import getenv
from flask import Flask, url_for, render_template, redirect
from client_api import api_bp
# from dashboard import init_dashboard

from dashboard import init_dashboard


def init_app():
    """
    Returns a Flask application with a Plotly Dash app initialised.
    Does not start the Flask app.
    """
    app = Flask(__name__)

    app.register_blueprint(api_bp, url_prefix="/api")

    # init plotly Dash as a Flask component
    app = init_dashboard(app)

    @app.route("/")
    @app.route("/recent_tweet_list")
    @app.route("/about")
    def root(name=None):
        return redirect("/dashapp/")

    return app
