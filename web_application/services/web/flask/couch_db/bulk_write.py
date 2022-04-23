from couchdb import Server

import json
import time

# couchDB anonymous server connection
couchserver = Server("http://admin:password@localhost:5984/")
for dbname in couchserver:
    # print(dbname)
    pass

db = couchserver["test"]

i = 0
with open("C:/Users/xander/Downloads//twitter-melb.json.tar//twitter-melb.json//twitter-melb.json", encoding="utf-8") as file_handle:
    for line in file_handle:
        try:
            epoch_time = int(time.time())
            val = json.loads(line[0:-2])
            val["created_at_epoch"] = epoch_time
            key = val["id"]
            db[key] = {'key': val}
        except Exception:
            pass

        i = i + 1
        # if i > 20:
        #     break
