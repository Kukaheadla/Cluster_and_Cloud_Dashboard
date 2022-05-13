"""
Author: Alex T
This file is the entrypoint for wsgi (web server gateway interface) initialisation. etc.
See: https://flask.palletsprojects.com/en/2.1.x/deploying/uwsgi/ or with Gunicorn.

To run for development:
export FLASK_APP=wsgi.py
export FLASK_ENV=development
python -m flask run

OR

docker-compose -f ./docker-compose.dev.yml up -d --build
"""

from os import getenv

from app import init_app

# # retrieve our application object, but do not run it.
application = init_app()

# if run directly
if __name__ == "__main__":
    application.run(host="0.0.0.0", port=getenv("port", 5000), debug=True)
