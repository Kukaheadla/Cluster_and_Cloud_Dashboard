from couchdb import Server, Document

import json
import time

# couchDB anonymous server connection
couchserver = Server("http://admin:password@172.26.132.25:5984/")
for dbname in couchserver:
    # print(dbname)
    pass

db = couchserver["test2"]

i = 0
docs_to_send = []
with open(
    "C:/Users/xander/Downloads/twitter-melb.json.tar/twitter-melb.json/twitter-melb.json",
    encoding="utf-8",
) as file_handle:
    for line in file_handle:
        if i <= 892249:
            i = i + 1
            continue
        try:
            if i % 250 == 0:
                db.update(docs_to_send)
                docs_to_send = []
            epoch_time = int(time.time())
            val = json.loads(line[0:-2])
            del val["key"]
            val["created_at_epoch"] = epoch_time
            key = val["id"]
            print(val["doc"]["created_at"])

            docs_to_send.append(val)
            # db[key] = {"key": val}
        except Exception as e:
            print(str(e))
            pass

        i = i + 1
print(str(i))
