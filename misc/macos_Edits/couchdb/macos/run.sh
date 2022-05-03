#!/usr/bin/env bash

echo "== Set variables =="
declare -a nodes=(172.20.0.2 172.20.0.3 172.20.0.4)
declare -a ports=(5984 15984 25984)
export master_node=172.20.0.2
export master_port=5984
export size=${#nodes[@]}
export user=user
echo ${user}
export pass=pass
echo ${pass}

echo "== Start the containers =="
docker-compose up -d

sleep 30

echo "== Enable cluster setup =="
for (( i=0; i<${size}; i++ )); do
  curl -X POST "http://${user}:${pass}@localhost:${ports[${i}]}/_cluster_setup" -H 'Content-Type: application/json' \
    -d "{\"action\": \"enable_cluster\", \"bind_address\":\"0.0.0.0\", \"username\": \"${user}\", \"password\":\"${pass}\", \"node_count\":\"${size}\"}"
done

sleep 10

echo "== Add nodes to cluster =="
for (( i=0; i<${size}; i++ )); do
  if [ "${nodes[${i}]}" != "${master_node}" ]; then
    curl -X POST -H 'Content-Type: application/json' http://${user}:${pass}@127.0.0.1:${master_port}/_cluster_setup \
      -d "{\"action\": \"enable_cluster\", \"bind_address\":\"0.0.0.0\", \"username\": \"${user}\", \"password\":\"${pass}\", \"port\": 5984, \"node_count\": \"${size}\", \
           \"remote_node\": \"${nodes[${i}]}\", \"remote_current_user\": \"${user}\", \"remote_current_password\": \"${pass}\"}"
    curl -X POST -H 'Content-Type: application/json' http://${user}:${pass}@127.0.0.1:${master_port}/_cluster_setup \
      -d "{\"action\": \"add_node\", \"host\":\"${nodes[${i}]}\", \"port\": 5984, \"username\": \"${user}\", \"password\":\"${pass}\"}"
  fi
done

sleep 10

curl -X POST "http://${user}:${pass}@localhost:${master_port}/_cluster_setup" -H 'Content-Type: application/json' -d '{"action": "finish_cluster"}'

curl http://${user}:${pass}@localhost:${master_port}/_cluster_setup

for port in "${ports[@]}"; do  curl -X GET http://${user}:${pass}@localhost:${port}/_membership; done


##Additions:
#Run all subsequent commands from the directory couchdb.
cd ../

curl -v -XPUT "http://${user}:${pass}@localhost:${master_port}/twitter"
##for node in "${nodes[@]}"; do  curl -v -X GET "http://${user}:${pass}@${node}:5984/_all_dbs"; done
for port in "${ports[@]}"; do  curl -X GET "http://${user}:${pass}@localhost:${port}/_all_dbs"; done
##curl -XPUT "http://user:pass@localhost:5984/twitter"

#Cluster management:
#declare -a conts=(`docker ps --all | grep couchdb | cut -f1 -d' ' | xargs -n${size} -d'\n'`)
#xargs: illegal option -- d

#Starts the containers
declare -a conts=(`docker ps --all | grep couchdb | cut -f1 -d' ' | xargs -n${size}`)
for cont in "${conts[@]}"; do docker start ${cont}; done

#Loading of sample data
curl -XPOST "http://${user}:${pass}@localhost:${master_port}/twitter/_bulk_docs" --header "Content-Type: application/json" --data @./twitter/data.json

#MapReduce views and list/show functions
export dbname='twitter'
grunt couch-compile
grunt couch-push

#Request a map-reduce view:
curl -XGET "http://${user}:${pass}@localhost:${master_port}/twitter/_design/language/_view/language?reduce=true&group_level=1"

#Request a show function returning HTML:
docid=`curl -XGET "http://${user}:${pass}@localhost:${master_port}/twitter/_all_docs?limit=1" | jq '.rows[].id' | sed 's/"//g'`
curl -XGET "http://${user}:${pass}@localhost:${master_port}/twitter/_design/language/_show/html/${docid}"

#Reqest a list function returning HTML:
curl -XGET "http://${user}:${pass}@localhost:${master_port}/twitter/_design/language/_list/html/language?reduce=true&group_level=2"

#Request a list function returning GeoJSON
curl -XGET "http://${user}:${pass}@localhost:${master_port}/twitter/_design/language/_list/geojson/language?reduce=false&include_docs=true" | jq '.' > /tmp/twitter.geojson

#You can now load the GeoJSON in a text editor, or display them on a map using QGIS.

##Mango queries and indexes
#Mango query request:
curl -XPOST "http://${user}:${pass}@localhost:${master_port}/twitter/_find" \
--header "Content-Type: application/json" --data '{
   "fields" : ["_id", "text", "user.screen_name"],
   "selector": {
      "user.lang": {"$eq": "ja"}
   }
}'  | jq '.' -M

#Mango query explanation (use of indexes, or lack-there-of, etc)
curl -XPOST "http://${user}:${pass}@localhost:${master_port}/twitter/_explain" \
--header "Content-Type: application/json" --data '{
   "fields" : ["_id", "text", "user.screen_name"],
   "selector": {
      "user.lang": {"$eq": "ja"}
   }
}'  | jq '.' -M

#More complex Mango query, with tweets sorted by screen_name (it should return a warning, 
#because no index has been defined for the sort field):
curl -XPOST "http://${user}:${pass}@localhost:${master_port}/twitter/_find" --header "Content-Type: application/json" --data '{
   "fields" : ["_id", "user.lang", "user.screen_name", "text"],
   "selector": {
      "$and": [
        {"user.lang": {"$eq": "en"}},
        {"user.screen_name": {"$gt": "pin"}}
      ]
   }, 
   "sort": [{"user.screen_name": "asc"}]
}' | jq '.' -M

#Outputs the following:
# {
#  "error": "no_usable_index",
#  "reason": "No index exists for this sort, try indexing by the sort fields."
#}

#Create index for lang and screen_name, hence the above query runs faster, but, still,
#it cannot efficiently sort by screen_name, since this index order documents for the combination
#of lang and screen_name, not for either field taken in isolation (same as SQL DBSMes) 
curl -XPOST "http://${user}:${pass}@localhost:${master_port}/twitter/_index" \
--header "Content-Type: application/json" --data '{
   "ddoc": "indexes",
   "index": {
      "fields": ["user.lang", "user.screen_name"]
   },
   "name": "lang-screen-index",
   "type": "json"
}'

## {"result":"created","id":"_design/indexes","name":"lang-screen-index"}

#Create index for just the screen_name, now the query should be faster 
#(not that one can notice with just 1,000 documents withoud instrumentation, but you get the idea):
curl -XPOST "http://${user}:${pass}@localhost:${master_port}/twitter/_index" \
--header "Content-Type: application/json" --data '{
   "ddoc": "indexes",
   "index": {
      "fields": ["user.screen_name"]
   },
   "name": "screen-index",
   "type": "json"
}'
## {"result":"created","id":"_design/indexes","name":"screen-index"}

#Get the list of indexes:
curl -XGET "http://${user}:${pass}@localhost:${master_port}/twitter/_index" | jq '.' -M
#(Partial indexes selector may be used to exclude some documents from indexing, in order to speed up indexing.)

#Indexes can be deleted as well:
curl -XDELETE "http://${user}:${pass}@localhost:${master_port}/twitter/_index/indexes/json/lang-screen-index"

## Spatial indexes
#Index by location (works only for points, and it is higly inefficient, but it works for small datasets).
curl -XPOST "http://${user}:${pass}@localhost:${master_port}/twitter/_index" \
--header "Content-Type: application/json" --data '{
   "ddoc": "indexes",
   "index": {
      "fields": ["coordinates.coordinates"]
   },
   "name": "coordinates",
   "type": "json"
}'
# {"result":"created","id":"_design/indexes","name":"coordinates"}

#Query data by their longitude (the index is now built, analogously to the MapReduce views)
curl -XPOST "http://${user}:${pass}@localhost:${master_port}/twitter/_find" --header "Content-Type: application/json" --data '{
   "fields" : ["_id", "user.lang", "user.screen_name", "text", "created_at", "coordinates"],
   "selector": {
      "$and": [
        {"coordinates.coordinates": {"$gt": [115.3]}},
        {"coordinates.coordinates": {"$lt": [115.6]}}
      ]
   }
}' | jq '.' -M
#(Only the longitude is part of the query since Mango indexes only the first element of an array
#-`coordinates.coordinates` is an array.)

## Full-text search (search indexes)

#Create a search index:
curl -XPUT "http://${user}:${pass}@localhost:${master_port}/twitter/_design/textsearch"\
  --header 'Content-Type:application/json'\
  --data @./twitter/textsearch/text.json

#Warning: Couldn't read data from file 
#Warning: "./couchdb/twitter/textsearch/text.json", this makes an empty POST.
# {"error":"bad_request","reason":"invalid UTF-8 JSON"}

#After changing --data @./couchdb/twitter/textsearch/text.json to --data @./twitter/textsearch/text.json:

# {"ok":true,"id":"_design/textsearch","rev":"1-5d5fdefe82e83529c6cddc06c30821b7"}

#Query all the tweets in Japanese:
curl -XPOST "http://${user}:${pass}@localhost:${master_port}/twitter/_design/textsearch/_search/text"\
  --header 'Content-Type:application/json'\
  --data '{"q": "language:ja"}' | jq '.'

# Query all the tweets in English that contains the words 'weekend' and 'days';
curl -XPOST "http://${user}:${pass}@localhost:${master_port}/twitter/_design/textsearch/_search/text"\
  --header 'Content-Type:application/json'\
  --data '{"q": "language:en AND (text:weekend AND text:days)"}' | jq '.'

## Creation and use of partitioned database
# Create a partitioned database:
curl -XPUT "http://${user}:${pass}@localhost:${master_port}/twitterpart?partitioned=true"

#Transfer the tweets to the partitioned database partitioning by user's screen name:
#node ./couchdb/transfer.js
node ./transfer.js
#(The program above is a simplified code that is not optimized for large databases.)

#Get some information on a partition:
curl -XGET "http://${user}:${pass}@localhost:${master_port}/twitterpart/_partition/T-ABCrusader" | jq '.'

#List all the documents in a given partition (should return all the tweets of user `ABCrusader`):
curl -XGET "http://${user}:${pass}@localhost:${master_port}/twitterpart/_partition/T-ABCrusader/_all_docs" | jq '.'

#Since partitioned databases cannot use custom `reduce` functions, we cannot just use the design document of the other database.
 
#Add a design document with MapReduce Views, Lists and Shows functions
export dbname='twitterpart'
curl -X PUT http://${user}:${pass}@localhost:${master_port}/${dbname}/_design/language\
   --data '{"views":{"language":{"map":"function(doc) { emit([doc.user.lang], 1); }", "reduce":"_count"}}}'\
   --header 'Content-Type:application/json'

#Executes a partitioned query:
curl -XGET "http://${user}:${pass}@localhost:${master_port}/twitterpart/_partition/T-ABCrusader/_design/language/_view/language?reduce=true&group_level=2" | jq '.'

#Non-partitioned views have to be explicitly declared during the creation of a design document, by adding `partitioned: false` to their `options` property.
#(By default, all views in a partitioned database are partitioned.)