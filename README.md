# Cluster and Cloud Computing - Assignment 2, Group 29

- Alexander Troup (640478), atroup@student.unimelb.edu.au

- David Liu (893542), tianjianl@student.unimelb.edu.au

- Kevin Y. Yang (815565), yuy15@student.unimelb.edu.au

- Xuan Hung Ho (1276655), xuanhungh@student.unimelb.edu.au


**Video Demo Link**: https://youtu.be/TpWQxotbd_c

--- 
## Directory Navigations

`additional_references/`: consist of Jupyter notebooks that are used in the AURIN comparative analysis and Plotly Dash charts which are experimented for Web front-end.

`couchdb/` consist of all of the MapReduce Algorithms to produce CouchDB views.

`deployment/` contains Ansible files for each of the MRC infrastructure, web apps, databases, crawler, etc. To understand more, follow the Section 2.1 of the report.

`harvester/` contains the tweet harvesting algorithms that utilizes Twitter Streaming and Search API and parse the curated data into CouchDB destinations. This is application code and the deployment is in the **Harvester Deployment** Section

`web_application/` contains the web application logics which consist of Nginx-related files and the flask applications. To interact with the dashboard follow **Frontend Web Application** section.

--- 
## Harvester Deployment

Ansible files for deploying the Twitter Harvester are in [deployment/harvester_deployment](https://github.com/DavidL124/Cluster_and_Cloud_Assign2/tree/main/deployment/harvester_deployment)


To run this, run the file [deployment/harvester_deployment/open_crawler.sh](https://github.com/DavidL124/Cluster_and_Cloud_Assign2/blob/main/deployment/harvester_deployment/open_crawler.sh) as you would any other ansible playbook. You need to have the correct SSH keys set up and the correct openrc.sh file from the MRC.

The [SSH key in crawler.yml](https://github.com/DavidL124/Cluster_and_Cloud_Assign2/blob/main/deployment/harvester_deployment/crawler.yaml#L22) is called demo.pem but you can replace this if setting up a new instance etc.

- run the harvester directly on a local machine like so: 
  
```bash    
python main.py --credentials-id 0 --couchdb-host 172.26.134.34:5984 --couchdb-username user --city melbourne --topic transport --mode stream --debug
```

- see help for CLI options and available topics:

```bash
python main.py --help
```

---
## Frontend Web Application

*web_application/* contains frontend web app and server. [Dashboard.py](https://github.com/DavidL124/Cluster_and_Cloud_Assign2/blob/main/web_application/services/web/flask/dashboard.py) contains the main code for rendering the Dashboard.

- view on: [Click Here](http://45.113.234.122/dashapp/) or go to `http://45.113.234.122/dashapp/`

- query the REST API on: ` http://45.113.234.122/api`
    - `/api/tweet?id=<tweet_id>`
        - returns a Tweet with the provided ID
