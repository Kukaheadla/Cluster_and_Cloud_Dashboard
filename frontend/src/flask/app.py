"""
This file contains endpoints and functions relating to serving the application directly to users.
"""

from os import getenv
from flask import Flask, url_for, render_template, redirect
from client_api import api_bp
from dashboard import init_dashboard


def init_app():
    app = Flask(__name__)

    app.register_blueprint(api_bp, url_prefix="/api")

    # init plotly Dash as a Flask component
    app = init_dashboard(app)

    @app.route("/")
    @app.route("/tweet_list")
    @app.route("/about")
    def root(name=None):
        return redirect("/dashapp/")

    return app
