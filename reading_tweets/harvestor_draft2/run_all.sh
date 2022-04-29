#Trial of the combined service:
python3 ./crawler.py

#Post to CouchDB
curl -v -XPUT "http://user:pass@localhost:5984/tweets_draft6"
curl -XPOST "http://user:pass@localhost:5984/tweets_draft6/_bulk_docs" --header "Content-Type: application/json" --data @tweets_draft6.json
