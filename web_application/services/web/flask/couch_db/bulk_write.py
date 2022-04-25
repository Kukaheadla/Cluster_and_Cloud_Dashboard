from couchdb import Server, Document

import json
import time

# couchDB anonymous server connection
couchserver = Server("http://admin:password@172.26.132.25:5984/")
for dbname in couchserver:
    # print(dbname)
    pass

db = couchserver["test"]

i = 0
docs_to_send = []
with open(
    "C:/Users/xander/Downloads/twitter-melb.json.tar/twitter-melb.json/twitter-melb.json",
    encoding="utf-8",
) as file_handle:
    for line in file_handle:
        if i <= 1539998:
            i = i + 1
            continue
        try:
            if i % 5000 == 0:
                db.update(docs_to_send)
                docs_to_send = []
            epoch_time = int(time.time())
            val = json.loads(line[0:-2])
            val["created_at_epoch"] = epoch_time
            key = val["id"]

            docs_to_send.append(val)
            # db[key] = {"key": val}
        except Exception as e:
            print(str(e))
            pass

        i = i + 1
        # if i > 20:
        #     break
print(str(i))