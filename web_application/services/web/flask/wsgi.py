"""
This file is the entrypoint for wsgi (web server gateway interface) initialisation. etc.
See: https://flask.palletsprojects.com/en/2.1.x/deploying/uwsgi/
"""

from os import getenv

from app import init_app

application = init_app()

# if run directly
if __name__ == "__main__":
    application.run(host="0.0.0.0", port=getenv("port", 5000), debug=True)
