#Trial of the combined service:
python3 ./crawler.py

#Post to CouchDB
curl -v -XPUT "http://172.26.130.230:5984/tweets_draft6"
curl -XPOST "http://172.26.130.230:5984/tweets_draft6/_bulk_docs" --header "Content-Type: application/json" --data @tweets_draft6.json
