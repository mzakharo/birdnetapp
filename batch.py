import os, sys
from birdnetapp.app import MDATA, HOST, PORT, sendRequest
import json
import datetime

for x in os.walk(sys.argv[1]):
    files = x[2]
    if not(len(files)):
        continue
    name = x[0].split(os.sep)[-1]
    for f in files:
        if f.endswith('.wav') or f.endswith('.mp3'):
            fname = os.path.join(x[0], f)
            MDATA['week'] = datetime.datetime.now().isocalendar()[1]
            res = sendRequest(HOST, PORT,fname, json.dumps(MDATA))
            rname, conf = res['results'][0]
            sci, rname = rname.split('_')
            print(name,fname, rname, conf)

 

