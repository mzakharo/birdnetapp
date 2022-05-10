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

from secrets import TELEGRAM_TOKEN, TELEGRAM_CHATID, INFLUX_URL, INFLUX_TOKEN

#Mic settings

#PS-Eye
RATE = 16000
CHANNELS = 4
CARD = 'CameraB409241'
CHUNK = RATE * 1 # 1 second buffer

#Files saved here
SAVEDIR = '/home/pi/birdNet'

#birdNET settings
RECORD_SECONDS = 9
CONF_TRHRESH = 0.5
LAT=43.544811
LON=-80.248108
OVERLAP = 1 # 2.4
PMODE = 'avg' # 'max'
SF_THRESH = 0.05 #reduce false positives

#birdNet server
HOST='127.0.0.1'
PORT = 8080

#influx
ORG = "home"
BUCKET = "main"


influx_client = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=ORG)
write_api = influx_client.write_api(write_options=SYNCHRONOUS)
query_api = influx_client.query_api()


# Make metadata
mdata = {'lat': LAT, 
         'lon': LON, 
         'num_results': 3,
         'overlap' : OVERLAP,
         'pmode' : PMODE,
         'sf_thresh': SF_THRESH,
         }




def send_telegram(filename, sci_result, result, conf, dry=False):
    with open(filename, 'rb') as audio:
        linkname = sci_result.replace(' ', '+')
        all_species_name = result.replace(' ', '_')
        tb = telebot.TeleBot(TELEGRAM_TOKEN, parse_mode='MARKDOWN')
        title = f'conf: {int(conf * 100)}%'
        caption =  f'''[All About Birds](https://allaboutbirds.org/guide/{all_species_name})  
[Wikimedia](https://commons.wikimedia.org/w/index.php?search={linkname}&title=Special:MediaSearch&go=Go)'''
        if not dry:
            tb.send_audio(TELEGRAM_CHATID, audio, performer=result, title=title, caption=caption)


def upload_result(filename, res, confidence, dry, debug):
    if res['msg'] != "success":
        return
    results = res['results']
    if len(results) == 0:
        return
    result, conf = results[0]

    sci_result, result = result.split('_')

    if conf >= confidence:
        dir_path = os.path.join(SAVEDIR, result)

        if not os.path.exists(dir_path):
            os.makedirs(dir_path)

        date_time = datetime.datetime.now().strftime("%Y%m%d_%H")
        file_name = os.path.join(dir_path, date_time + '.wav')
        file_name_meta = os.path.join(dir_path, date_time + '.json')

        meta = {}
        if os.path.exists(file_name_meta):
            with open(file_name_meta, 'r') as f:
                try:
                    meta = json.loads(f.read())
                except json.decoer.JSONDecodeError:
                    pass

        old_conf = meta.get('conf', 0)
        count = meta.get('count', 0)

        count += 1
        print(result, file_name,'conf', conf, 'old_conf', old_conf, 'count', count)
        meta['count'] = count
        if conf >= old_conf:
            meta['conf'] = conf
            meta['results'] = results
            shutil.copyfile(filename, file_name)

            #send notification if it is a new bird
            df = query_api.query_data_frame(
            '''import "influxdata/influxdb/schema"
             schema.fieldKeys(
                    bucket: "main",
                    predicate: (r) => r["_measurement"] == "birdnet",
                    start: -14d,
                    )''')

            seen = any(df['_value'].isin([result]))
            if not seen:
                send_telegram(filename, sci_result, result, conf, dry=dry)

        with open(file_name_meta, 'w') as f:
            f.write(json.dumps(meta))

        if not dry:
            ts = datetime.datetime.utcnow()
            point = Point("birdnet") \
                  .field(result, conf) \
                  .time(ts, WritePrecision.NS)
            write_api.write(BUCKET, ORG, point)



def sendRequest(host, port, fpath, mdata, debug):
    url = 'http://{}:{}/analyze'.format(host, port)

    start_time = time.time()
    # Make payload
    with open(fpath, 'rb') as audio:
        multipart_form_data = {
            'audio': ('audio.wav', audio),
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
    def __init__(self, rate, chunk):
        self.rate = rate
        self.chunk = chunk

    def open(self):
        cards = alsaaudio.cards()
        card_i = cards.index(CARD)
        self.stream = alsaaudio.PCM(alsaaudio.PCM_CAPTURE, channels=CHANNELS, format=alsaaudio.PCM_FORMAT_S16_LE, rate=self.rate, periodsize=self.chunk, cardindex=card_i)

    def read(self):
        l, data = self.stream.read()
        if l == -32:
            raise Exception("Warning: Overflow occured")
        elif l != self.chunk:
            raise Exception("Warning: incorrect frame length", l//2, self.chunk//2)

        return data

    def active(self):
        return True

    def close(self):
        if os.name == 'nt':
            self.stream.stop_stream()
            self.stream.close()
            self.p.terminate()
        else:
            self.stream.close()

def process(args, data, mdata):
    data = np.frombuffer(data, dtype=np.int16)
    data = data.reshape((-1, CHANNELS))
    with tempfile.NamedTemporaryFile() as tmp:
        scipy.io.wavfile.write(tmp.name, RATE, data)
        res = sendRequest(HOST, PORT, tmp.name, json.dumps(mdata), args.debug)
        upload_result(tmp.name, res, args.confidence, args.dry, args.debug)


def main(args):
    stream = MicStream(RATE, CHUNK)
    stream.open()
    buf = deque(maxlen=RECORD_SECONDS)
    stride = 0


    print("started", flush=True)

    futures = []
    with ThreadPoolExecutor(max_workers=1) as exc:
        while stream.active():
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
                mdata['week'] = datetime.datetime.now().isocalendar()[1]
                futures.append(exc.submit(process,args, data, mdata))
                assert len(futures) < 10 , "Processing not keeping up with incoming data"
                for f in futures:
                    if f.done():
                        f.result()
                        futures.remove(f)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--confidence', type=float, default=CONF_TRHRESH, help='confidence threshold')
    parser.add_argument('--dry', action='store_true', help='do not upload to influx, send telegram')
    parser.add_argument('--debug', action='store_true', help='enable debug prints')
    args = parser.parse_args()
    main(args)
