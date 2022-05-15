import alsaaudio
import scipy.io
from collections import deque
import numpy as np
import sys
import os
import json
import time
import requests
import argparse
import datetime
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
import shutil
import telebot
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pydub import AudioSegment
import subprocess

from .secrets import TELEGRAM_TOKEN, TELEGRAM_CHATID, INFLUX_URL, INFLUX_TOKEN
from .config import *
from .clean import cleanup


influx_client = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=ORG)
write_api = influx_client.write_api(write_options=SYNCHRONOUS)
query_api = influx_client.query_api()


# Make metadata
MDATA = {'lat': LAT, 
         'lon': LON, 
         'num_results': 3,
         'overlap' : OVERLAP,
         }


def send_telegram(filename, sci_result, result, conf, count=1,dry=False):
    print('sending telegram message for', result)
    with open(filename, 'rb') as audio:
        linkname = sci_result.replace(' ', '+')
        all_species_name = result.replace(' ', '_')
        tb = telebot.TeleBot(TELEGRAM_TOKEN, parse_mode='MARKDOWN')
        title = f'Confidence: {int(conf * 100)}%'
        caption =  f'''{title}  
Count: {count}  
[All About Birds](https://allaboutbirds.org/guide/{all_species_name})  
[Wikimedia](https://commons.wikimedia.org/w/index.php?search={linkname}&title=Special:MediaSearch&go=Go)'''
        if not dry:
            tb.send_audio(TELEGRAM_CHATID, audio, performer=sci_result, title=result, caption=caption)
        else:
            print('telegram', result, sci_result, caption)

def send_telegram_delayed(delayed_telegrams,ts, res, delay=0, dry=False):

    #store most confident result, along with detection count
    if res is not None:
        name = res['name']
        conf = res['conf']
        count = 1
        old_conf = 0
        if name in delayed_telegrams:
            msg = delayed_telegrams[name]
            msg['count'] += 1
            count = msg['count']
            old_conf = msg['conf']
        if conf >= old_conf: 
            res['count'] = count
            res['ts'] = ts
            delayed_telegrams[name] = res

    #send delayed telegrams
    for name in list(delayed_telegrams):
        if ts >= delayed_telegrams[name]['ts'] + datetime.timedelta(seconds=delay):
            msg = delayed_telegrams.pop(name)
            send_telegram(msg['fname'], msg['sci'], msg['name'], msg['conf'], msg['count'], dry=dry)


            
def upload_result(ts, filename, savedir, res, min_confidence, dry=False, debug=False, force_telegram=False):
    if res['msg'] != "success":
        return
    results = res['results']
    if len(results) == 0:
        return
    out = None
    result, conf = results[0]
    
    n = 1000
    if isinstance(conf, (list, tuple)):
        conf, n = conf

    sci_result, result = result.split('_')

    if conf >= min_confidence or n < 2:
        dir_path = os.path.join(savedir, result)

        if not os.path.exists(dir_path):
            os.makedirs(dir_path)

        cleanup(dir_path, KEEP_FILES) #avoid running out of storage

        date_time = ts.strftime("%y-%m-%d_%H-%M-%S")
        export_filename = os.path.join(dir_path, date_time + EXPORT_FORMAT) 
        export_spec = os.path.join(dir_path, date_time + '.png') 
        export_meta = os.path.join(dir_path, date_time + '.json')

        meta = {}
        meta['conf'] = conf
        meta['results'] = results
        meta['n'] = n

        print(result, export_filename, 'conf', conf, 'n', n)

        if export_filename.endswith('.mp3'):
            AudioSegment.from_wav(filename).export(export_filename, format="mp3", parameters=["-ac", "1", "-vol", "150", "-q:a",  "9"])
        else:
            shutil.copyfile(filename, export_filename)

        subprocess.check_output(['sox', filename, '-n', 'spectrogram', '-o', export_spec])

        with open(export_meta, 'w') as f:
            f.write(json.dumps(meta))

        #send notification if it is a new bird
        query = f'''
                import "influxdata/influxdb/schema"
                schema.fieldKeys(
                    bucket: "main",
                    predicate: (r) => r["_measurement"] == "birdnet",
                    start: -{SEEN_TIME},
                )'''
        df = query_api.query_data_frame(query)

        seen = any(df['_value'].isin([result]))
        if not seen or n < 2 or force_telegram:
            r = result
            if n < 2:
                r = r + f' n={n}'
            out = {'fname' : export_filename,'sci' :  sci_result, 'name' : r, 'conf' : conf}
            #send_telegram(export_filename, sci_result, r, conf, dry=dry)

        if not dry:
            ts_utc = datetime.datetime.utcfromtimestamp(ts.timestamp())
            point = Point("birdnet") \
                  .field(result, conf) \
                  .time(ts_utc, WritePrecision.NS)
            write_api.write(BUCKET, ORG, point)
    return out


def sendRequest(host, port, fpath, mdata, debug):
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

    if debug:
        print('Response: {}, Time: {:.4f}s'.format(response.text, end_time - start_time), flush=True)

    # Convert to dict
    data = json.loads(response.text)
    
    return data


class MicStream():
    def __init__(self, rate, channels, chunk, card):
        self.rate = rate
        self.chunk = chunk
        self.card = card
        self.stream = None
        self.channels = channels

    def open(self):
        cards = alsaaudio.cards()
        print("detected cards", cards, "configuring:", self.card)
        card_i = cards.index(self.card)
        self.stream = alsaaudio.PCM(alsaaudio.PCM_CAPTURE, channels=self.channels, format=alsaaudio.PCM_FORMAT_S16_LE, rate=self.rate, periodsize=self.chunk, cardindex=card_i)

    def read(self):
        l, data = self.stream.read()
        if l == -32:
            raise Exception("Warning: Overflow occured")
        elif l < 0:
            raise Exception(f"Unknown error occured: {l}")
        elif len(data) != self.chunk * self.channels * 2:
            raise Exception(f"Warning: incorrect frame length: got {len(data)} expected {self.chunk * self.channels * 2}")

        return data

    def close(self):
        if self.stream is not None:
            self.stream.close()
            self.stream = None
    def __del__(self):
        self.close()

def process(args, ts, data, mdata):
    mdata['week'] = ts.isocalendar()[1]
    data = np.frombuffer(data, dtype=np.int16)
    data = data.reshape((-1, CHANNELS))
    with tempfile.NamedTemporaryFile(suffix='.wav') as tmp:
        fname = tmp.name
        if args.debug:
            fname = '/tmp/foo.wav'
        scipy.io.wavfile.write(fname, RATE, data)
        res = sendRequest(HOST, PORT, fname, json.dumps(mdata), args.debug)
        return upload_result(ts, fname, SAVEDIR, res, args.min_confidence, args.dry, args.debug)


def runner(args, stream):
    buf = deque(maxlen=RECORD_SECONDS)
    stride = 0
    futures = []

    delayed_telegrams = {}

    print("started", flush=True)
    with ThreadPoolExecutor(max_workers=1) as exc:
        while True:
            try:
                data = stream.read()
            except Exception as e:
                print(e)
                continue
            stride += 1
            if args.debug:
                print(stride, len(data))
            buf.append(data)
            if stride == RECORD_SECONDS//2:
                stride = 0
                if len(buf) != buf.maxlen:
                    continue
                data = b''.join(buf)

                ts = datetime.datetime.now().replace(microsecond=0)
                futures.append(exc.submit(process, args, ts,  data, MDATA))
                assert len(futures) < 10 , "Processing not keeping up with incoming data"
                for f in futures:
                    if f.done():
                        res = f.result()
                        futures.remove(f)
                        send_telegram_delayed(delayed_telegrams,ts, res, delay=TELEGRAM_DELAY_SECONDS, dry=args.dry)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--min_confidence', type=float, default=CONF_TRHRESH, help='minimum confidence threshold')
    parser.add_argument('--dry', action='store_true', help='do not upload to influx, send telegram')
    parser.add_argument('--debug', action='store_true', help='enable debug prints')
    parser.add_argument('--card', default=CARD, help='microphone card to look for')
    args = parser.parse_args()

    stream = MicStream(RATE, CHANNELS, CHUNK, args.card)
    stream.open()
    try:
        runner(args, stream)
    finally:
        stream.close()
