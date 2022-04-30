# run from entrypoint passing in relevant flags
# this is really just an example, make sure it does what you expect!
python main.py --credentials-id 0 --couchdb-host localhost:5984 --couchdb-username admin --city melbourne --mode search --debug 




#Post to CouchDB
# curl -v -XPUT "http://172.26.130.230:5984/tweets_draft6"
# curl -XPOST "http://172.26.130.230:5984/tweets_draft6/_bulk_docs" --header "Content-Type: application/json" --data @tweets_draft6.json
