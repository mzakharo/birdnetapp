from flask import Flask
from flask import send_from_directory
from flask import render_template
import os
import json

from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

from birdnetapp.secrets import INFLUX_URL, INFLUX_TOKEN, INFLUX_ORG, INFLUX_BUCKET

FLUTTER_WEB_APP = 'flutter/build/web'

influx_client = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
write_api = influx_client.write_api(write_options=SYNCHRONOUS)
query_api = influx_client.query_api()



app = Flask(__name__, template_folder=FLUTTER_WEB_APP)

@app.route('/<path:name>')
def return_flutter_doc(name):

    datalist = str(name).split('/')
    DIR_NAME = FLUTTER_WEB_APP

    if len(datalist) > 1:
        for i in range(0, len(datalist) - 1):
            DIR_NAME += '/' + datalist[i]

    return send_from_directory(DIR_NAME, datalist[-1])

@app.route('/birds')
def birds():

    df = query_api.query_data_frame(f'''
            from(bucket:"{INFLUX_BUCKET}") 
            |> range(start: -24h)
            |> filter(fn: (r) => r["_measurement"] == "birdnet")
            |> count()
            ''')
    #print(df)
    o = {v['_field'] : v['_value'] for i, v in df.iterrows()}
    '''
    files = []
    folder = '/home/user/birdNet/'
    for x in os.walk(folder):
        files.append(x[2])
    '''
    return json.dumps(o)

@app.route('/')
def render_page():
    return render_template('/index.html')

if __name__ == '__main__':
    app.run()
