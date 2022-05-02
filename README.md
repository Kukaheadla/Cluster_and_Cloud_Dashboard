# Cluster and Cloud Computing - Assignment 2

`deployment/` contains Ansible files for each of the MRC infrastructure, web apps, databases, crawler, etc.

`harvester/` contains the tweet harvesting code

- to use the text sentiment function the `vaderSentiment` and `contraction` modules need to be imported.

  - One way is to use `python -m pip install vaderSentiment --no-cache-dir`
  -  `python -m pip install contractions --no-cache-dir` respectively as I personally found it difficult to install using pip.

- run the harvester like so: 
  
```bash    
python main.py --credentials-id 0 --couchdb-host 172.26.130.155:5984 --couchdb-username user --city melbourne --mode stream --debug
```

- see help for CLI options:

```bash
python main.py --help
```

*web_application/* contains frontend web app and server

- view on: `http://172.26.128.166/dashapp/`

- query the REST API on: `http://172.26.128.166/api`
    - `/api/tweet?id=<tweet_id>`
        - returns a Tweet with the provided ID
