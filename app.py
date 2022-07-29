from flask import Flask, Response, send_file
from flask import send_from_directory
from flask import render_template
import pandas as pd
import os
import json

from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

from tzlocal import get_localzone # $ pip install tzlocal
from birdnetapp.secrets import INFLUX_URL, INFLUX_TOKEN, INFLUX_ORG, INFLUX_BUCKET
from birdnetapp.config import APP_WINDOW, SAVEDIR

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

    # get local timezone    
    local_tz = str(get_localzone())
    print('local tz', local_tz)

    df = query_api.query_data_frame(f'''
        m = from(bucket:"{INFLUX_BUCKET}") 
          |> range(start: -{APP_WINDOW})
          |> filter(fn: (r) => r["_measurement"] == "birdnet")
        c = m
          |> count()
        l = m
          |> last()
        join(tables: {{count:c, last:l}}, on: ["_field"])
          |> group()
          |>sort(columns: ["_time"], desc: true)
        ''')
    #df.sort_values(["_time"], inplace=True,  ascending=False)
    #print(df)

    df.set_index(df._time, inplace=True)
    df.index = pd.to_datetime(df.index)
    df.index = df.index.tz_convert(local_tz)
    o = {v['_field'] : {'count' : v['_value_count'], 'time' : i.strftime('%m-%d %H:%M')} for i, v in df.iterrows()}
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


@app.route('/details/<name>')
def details(name):
    files = []
    folder = os.path.join(SAVEDIR, name)
    for x in os.walk(folder):
        contents = x[2]
        for f in contents:
            if f.endswith('.json'):
                files.append(f.split('.')[0])
    return json.dumps(sorted(files, reverse=True))

@app.route('/mp3/<name>/<date>')
def mp3(name, date):
    fname = os.path.join(SAVEDIR, name, date + '.mp3')
    def generate():
        with open(fname, "rb") as f:
            data = f.read(1024)
            while data:
                yield data
                data = f.read(1024)
    return Response(generate(), mimetype="audio/mp3")

@app.route('/png/<name>/<date>')
def png(name, date):
    image = os.path.join(SAVEDIR, name, date + '.png')
    return send_file(image, mimetype='image/png')


if __name__ == '__main__':
    app.run(host='0.0.0.0')
