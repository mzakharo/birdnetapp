import scipy.io
from collections import deque
import numpy as np
import sys
import os
import json
import time
import requests
import datetime
import shutil
import telebot
import tempfile
from pydub import AudioSegment
import subprocess
import logging
import argparse
import warnings
from influxdb_client import Point, WritePrecision
from influxdb_client.client.warnings import MissingPivotFunction
warnings.simplefilter("ignore", MissingPivotFunction)
from .config import *
from .clean import cleanup
from dataclasses import dataclass
import yaml


_LOGGER = logging.getLogger(__name__)


# Make metadata
MDATA = {'lat': LAT, 
         'lon': LON, 
         'num_results': 3,
         'overlap' : OVERLAP,
         'pmode' : PMODE,
         'sensitivity': SENSITIVITY,
         }


@dataclass
class Config:   
    influx_token: str
    influx_url: str
    influx_org: str
    influx_bucket: str
    telegram_token: str
    telegram_chatid: str
    latitude: float
    longitude: float
    microphone: str
    channels: int
    rate: int

    @classmethod
    def load(cls, path: str = os.path.abspath("config.yaml")) -> "Config":
        with open(path, "r") as f:
            config_dict = yaml.safe_load(f)
        return cls(**config_dict)




def send_telegram(token, chatid, msg, dry=False):
    filename = msg['fname']
    sci_result = msg['sci']
    result = msg['name']
    conf = msg['conf']
    count = msg['count']
    _LOGGER.info(f'sending telegram message for {result}')
    with open(filename, 'rb') as audio:
        linkname = sci_result.replace(' ', '+')
        all_species_name = result.replace(' ', '_')
        tb = telebot.TeleBot(token, parse_mode='MARKDOWN')
        title = f'Confidence: {int(conf * 100)}%'
        caption =  f'''{title}  
Count: {count}  
[All About Birds](https://allaboutbirds.org/guide/{all_species_name})  
[Wikimedia](https://commons.wikimedia.org/w/index.php?search={linkname}&title=Special:MediaSearch&go=Go)'''
        if not dry:
            tb.send_audio(chatid, audio, performer=sci_result, title=result, caption=caption)
        else:
            _LOGGER.info(f'telegram {result} {sci_result} {caption}')

def send_notification_delayed(delayed_notifications, ts, res, delay=0):

    #store most confident result, along with detection count
    if res is not None:
        name = res['name']

        if res['notify'] and name not in delayed_notifications:
            res['count'] = 0
            delayed_notifications[name] = res

        if name in delayed_notifications:
            msg = delayed_notifications[name]
            msg['count'] += 1
            msg['ts'] = ts
            if res['conf'] > msg['conf']:
                res['count'] = msg['count']
                res['ts'] = ts
                delayed_notifications[name] = res

    #send delayed notifications
    for name in list(delayed_notifications):
        if ts >= delayed_notifications[name]['ts'] + datetime.timedelta(seconds=delay):
            return delayed_notifications.pop(name)


            

def sendRequest(host, port, fpath, mdata): # pragma: no cover
    url = 'http://{}:{}/analyze'.format(host, port)

    start_time = time.time()
    # Make payload
    _, file_extension = os.path.splitext(fpath)
    with open(fpath, 'rb') as audio:
        multipart_form_data = {
            'audio': ('audio' + file_extension, audio),
            'meta': (None, mdata)
        }
        # Send request
        response = requests.post(url, files=multipart_form_data)

    end_time = time.time()

    _LOGGER.debug('Response: {}, Time: {:.4f}s'.format(response.text, end_time - start_time))

    # Convert to dict
    data = json.loads(response.text)
    
    return data


class Worker:
    def __init__(self, args, stream, exc, write_api, query_api):
        self.futures = []
        self.args = args
        self.exc = exc
        self.stream = stream
        self.write_api = write_api
        self.query_api = query_api
        self.sendRequest = sendRequest
        self.stride = 0

        self.buf = deque(maxlen=RECORD_SECONDS)
        self.delayed_notifications = {}


    def upload_result(self, ts, filename, savedir, res):
        if res['msg'] != "success":
            return
        results = res['results']
        if len(results) == 0:
            return
        result, conf = results[0]
        sci_result, result = result.split('_')
        if conf < CONF_THRESH:
            return

        dir_path = os.path.join(savedir, result)

        date_time = ts.strftime("%y-%m-%d_%H-%M-%S")
        export_filename = os.path.join(dir_path, date_time + EXPORT_FORMAT) 
        export_spec = os.path.join(dir_path, date_time + '.png') 
        export_meta = os.path.join(dir_path, date_time + '.json')

        meta = {}
        meta['conf'] = conf
        meta['results'] = results 

        #send notification if it is a new bird
        query = f'''
                import "influxdata/influxdb/schema"
                schema.fieldKeys(
                    bucket: "{self.args.influx_bucket}",
                    predicate: (r) => r["_measurement"] == "birdnet",
                    start: -{SEEN_TIME},
                )'''
        df = self.query_api.query_data_frame(query)

        seen = any(df['_value'].isin([result]))

        notify = not seen

        out = {'fname' : export_filename,'sci' :  sci_result, 'name' : result, 'conf' : conf, 'notify' : notify}
        _LOGGER.info(out)
        
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
        cleanup(dir_path, KEEP_FILES) #avoid running out of storage     

        if export_filename.endswith('.mp3'):
            AudioSegment.from_wav(filename).export(export_filename, format="mp3", parameters=["-ac", "1", "-vol", "150", "-q:a",  "9"])
        else:
            shutil.copyfile(filename, export_filename)

        subprocess.check_output(['sox', filename, '-n', 'spectrogram', '-o', export_spec])

        with open(export_meta, 'w') as f:
            f.write(json.dumps(meta))
        

        ts_utc = datetime.datetime.utcfromtimestamp(ts.timestamp())
        point = Point("birdnet") \
              .field(result, conf) \
              .time(ts_utc, WritePrecision.NS)
        self.write_api.write(self.args.influx_bucket, self.args.influx_org, point)
        return out


    def process(self, ts, data, mdata):
        tic = time.time()
        mdata['week'] = ts.isocalendar()[1]
        data = np.frombuffer(data, dtype=np.int16)
        data = data.reshape((-1, self.stream.channels))
        with tempfile.NamedTemporaryFile(suffix='.wav') as tmp:
            fname = tmp.name
            scipy.io.wavfile.write(fname, self.stream.rate, data)
            res = self.sendRequest(HOST, PORT, fname, json.dumps(mdata))
            up = self.upload_result(ts, fname, SAVEDIR, res)
            _LOGGER.debug(f'proces took: {time.time() - tic} seconds')
            return up

    def init(self):
        #birdNet Analyzer can have a very large first-time prediction delay. 
        #Avoid real-time sensitive code by sending a dummy processing message
        _LOGGER.info(f'Sending a dummy message to BirdNETAnalyzer....')
        ts = datetime.datetime.now()
        data = bytearray(self.buf.maxlen * 2 * self.stream.channels * self.stream.periodsize)
        self.process(ts, data, MDATA)
        end = datetime.datetime.now()
        _LOGGER.info(f'Initial BirdNETAnalyzer process took {end - ts}')

        _LOGGER.info("Started")

    def send_buffer(self, ts, data):
        self.futures.append(self.exc.submit(self.process, ts,  data, MDATA))

    def post_process(self, ts):
        for f in self.futures:
            if not f.done():
                continue
            self.futures.remove(f)
            res = f.result()
            msg = send_notification_delayed(self.delayed_notifications, ts, res, delay=NOTIFICATION_DELAY_SECONDS)
            if msg is not None:
                self.futures.append(self.exc.submit(send_telegram, self.args.telegram_token, self.args.telegram_chatid, msg, False))
            return msg

    def work(self, ts, data):
        self.stride += 1
        _LOGGER.debug(f"{self.stride} {len(data)}")
        self.buf.append(data)
        if len(self.futures) <= 1 and len(self.buf) == self.buf.maxlen:            
            buf = b''.join(self.buf)
            self.send_buffer(ts, buf)
            self.stride = 0
        else:
            if self.stride >= self.buf.maxlen:
                _LOGGER.warning('dropping buffer')
        return self.post_process(ts)


