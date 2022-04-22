"""
This file is the entrypoint for wsgi (web server gateway interface) initialisation.
See: https://flask.palletsprojects.com/en/2.1.x/deploying/uwsgi/
"""

from os import getenv

from app import init_app

app = init_app()

# if run directly
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=getenv("port", 105), debug=True)
