# Cluster and Cloud Computing - Assignment 2

*deployment/* contains ansible files for each of the web apps, databases, crawler, etc.

*harvester/* contains the tweet harvesting code

- run the harvester like so: 
    
    - $ python main.py --credentials-id 0 --couchdb-host 172.26.130.155:5984 --couchdb-username user --city melbourne --mode search --debug 

*web_application/* contains frontend web app and server

- view on: http://172.26.128.166/dashapp/

- query the REST API on: http://172.26.128.166/api
    - todo