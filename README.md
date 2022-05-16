# Group 29

Alexander Troup, 
David Liu, 
Kevin Y. Yang, 
Xuan Hung Ho

## Harvester Deployment

Ansible files for deploying the Twitter Harvester are in [deployment/harvester_deployment](https://github.com/DavidL124/Cluster_and_Cloud_Assign2/tree/main/deployment/harvester_deployment)
To run this, run the file [deployment/harvester_deployment/open_crawler.sh](https://github.com/DavidL124/Cluster_and_Cloud_Assign2/blob/main/deployment/harvester_deployment/open_crawler.sh) as you would any other ansible playbook. You need to have the correct SSH keys set up and the correct openrc.sh file from the MRC.

The [SSH key in crawler.yml](https://github.com/DavidL124/Cluster_and_Cloud_Assign2/blob/main/deployment/harvester_deployment/crawler.yaml#L22) is called demo.pem but you can replace this if setting up a new instance etc.

# Cluster and Cloud Computing - Assignment 2

`deployment/` contains Ansible files for each of the MRC infrastructure, web apps, databases, crawler, etc.

`harvester/` contains the tweet harvesting code

- to use the text sentiment function the `vaderSentiment` and `contraction` modules need to be imported.

  - One way is to use `python -m pip install vaderSentiment --no-cache-dir`
  -  `python -m pip install contractions --no-cache-dir` respectively as I personally found it difficult to install using pip.

- run the harvester directly on a local machine like so: 
  
```bash    
python main.py --credentials-id 0 --couchdb-host 172.26.134.34:5984 --couchdb-username user --city melbourne --topic transport --mode stream --debug
```

- see help for CLI options and available topics:

```bash
python main.py --help
```


## Frontend Web Application

*web_application/* contains frontend web app and server. [Dashboard.py](https://github.com/DavidL124/Cluster_and_Cloud_Assign2/blob/main/web_application/services/web/flask/dashboard.py) contains the main code for rendering the Dashboard.

- view on: [Click Here](http://45.113.234.122/dashapp/) or go to `http://45.113.234.122/dashapp/`

- query the REST API on: ` http://45.113.234.122/api`
    - `/api/tweet?id=<tweet_id>`
        - returns a Tweet with the provided ID
