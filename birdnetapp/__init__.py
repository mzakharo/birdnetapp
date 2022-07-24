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
import logging

from .secrets import TELEGRAM_TOKEN, TELEGRAM_CHATID, INFLUX_URL, INFLUX_TOKEN
from .config import *
from .clean import cleanup

_LOGGER = logging.getLogger(__name__)

influx_client = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=ORG)
write_api = influx_client.write_api(write_options=SYNCHRONOUS)
query_api = influx_client.query_api()


# Make metadata
MDATA = {'lat': LAT, 
         'lon': LON, 
         'num_results': 3,
         'overlap' : OVERLAP,
         }


def send_telegram(msg, dry=False):
    filename = msg['fname']
    sci_result = msg['sci']
    result = msg['name']
    conf = msg['conf']
    count = msg['count']
    _LOGGER.info(f'sending telegram message for {result}')
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
            _LOGGER.info(f'telegram {result} {sci_result} {caption}')

def send_notification_delayed(delayed_notifications,ts, res, delay=0, dry=False):

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


            
def upload_result(ts, filename, savedir, res, min_confidence, dry=False, force_notify=False):
    if res['msg'] != "success":
        return
    results = res['results']
    if len(results) == 0:
        return

    result, conf = results[0]
    sci_result, result = result.split('_')
    out = None

    if conf >= min_confidence:

        dir_path = os.path.join(savedir, result)

        date_time = ts.strftime("%y-%m-%d_%H-%M-%S")
        export_filename = os.path.join(dir_path, date_time + EXPORT_FORMAT) 
        export_spec = os.path.join(dir_path, date_time + '.png') 
        export_meta = os.path.join(dir_path, date_time + '.json')

        meta = {}
        meta['conf'] = conf
        meta['results'] = results

        _LOGGER.info(f"{result} {export_filename} conf: {conf}")

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

        #send notification if it is a new bird
        query = f'''
                import "influxdata/influxdb/schema"
                schema.fieldKeys(
                    bucket: "{BUCKET}",
                    predicate: (r) => r["_measurement"] == "birdnet",
                    start: -{SEEN_TIME},
                )'''
        df = query_api.query_data_frame(query)

        seen = any(df['_value'].isin([result]))

        notify = not seen or force_notify

        out = {'fname' : export_filename,'sci' :  sci_result, 'name' : result, 'conf' : conf, 'notify' : notify}

        if not dry:
            ts_utc = datetime.datetime.utcfromtimestamp(ts.timestamp())
            point = Point("birdnet") \
                  .field(result, conf) \
                  .time(ts_utc, WritePrecision.NS)
            write_api.write(BUCKET, ORG, point)

    return out


def sendRequest(host, port, fpath, mdata):
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


class MicStream():
    def __init__(self, rate, channels, chunk, card):
        self.rate = rate
        self.chunk = chunk
        self.card = card
        self.stream = None
        self.channels = channels

    def open(self):
        cards = alsaaudio.cards()
        _LOGGER.info(f"Detected cards {cards} configuring: '{self.card}' from config.CARD")
        card_i = cards.index(self.card)
        self.stream = alsaaudio.PCM(alsaaudio.PCM_CAPTURE, channels=self.channels, format=alsaaudio.PCM_FORMAT_S16_LE, rate=self.rate, periodsize=self.chunk, cardindex=card_i)
        got_rate = self.stream.setrate(self.rate)
        if got_rate != self.rate:
            raise ValueError(f"Card was configured with {self.rate}Hz but card returned {got_rate}Hz, adjust config.RATE accordingly. Card's supported rates: {self.stream.getrates()}")
        channels = self.stream.setchannels(self.channels)
        if channels != self.channels:
            raise ValueError(f"Card was configured with {self.channels} channel(s) but card returned {channels} channel(s), adjust config.CHANNELS accordingly. Card's supported channels: {self.stream.getchannels()}")

    def read(self):
        l, data = self.stream.read()
        exp = self.rate * self.channels * 2
        if l == -32:
            raise Exception("Warning: Overflow occured")
        elif l <= 0:
            raise Exception(f"Unknown error occured: {l}")
        elif l != self.chunk:
            raise Exception(f"Warning: incorrect frame length: got {l} expected {self.chunk}")
        elif len(data) !=  exp:
            raise Exception(f"Warning: incorrect frame length: got {len(data)} expected {exp}")

        return data

    def close(self):
        if self.stream is not None:
            self.stream.close()
            self.stream = None
    def __del__(self):
        self.close()

def process(args, ts, data, mdata):
    tic = time.time()
    mdata['week'] = ts.isocalendar()[1]
    data = np.frombuffer(data, dtype=np.int16)
    data = data.reshape((-1, CHANNELS))
    with tempfile.NamedTemporaryFile(suffix='.wav') as tmp:
        fname = tmp.name
        scipy.io.wavfile.write(fname, RATE, data)
        res = sendRequest(HOST, PORT, fname, json.dumps(mdata))
        up = upload_result(ts, fname, SAVEDIR, res, args.min_confidence, args.dry)
        _LOGGER.debug(f'proces took: {time.time() - tic} seconds')
        return up

def work(args, stream, exc, futures):
    stride = 0
    buf = deque(maxlen=RECORD_SECONDS)
    delayed_notifications = {}

    #birdNet Analyzer can have a very large first-time prediction delay. 
    #Avoid real-time sensitive code by sending a dummy processing message
    _LOGGER.info(f'Sending dummy message to birdNetAnalyzer....')
    ts = datetime.datetime.now()
    data = bytearray(buf.maxlen * 2 * stream.channels * stream.chunk)
    process(args, ts, data, MDATA)
    end = datetime.datetime.now()
    _LOGGER.info(f'Initial birdNetAnalyzer process took {end - ts}')
    _LOGGER.info("Started")
    while True:
        try:
            data = stream.read()
        except Exception as e:
            _LOGGER.warning(e)
            continue
        stride += 1
        _LOGGER.debug(f"{stride} {len(data)}")

        buf.append(data)
        if stride == args.stride_seconds:
            stride = 0
            if len(buf) != buf.maxlen:
                continue
            data = b''.join(buf)
            ts = datetime.datetime.now().replace(microsecond=0)
            futures.append(exc.submit(process, args, ts,  data, MDATA))
            _LOGGER.debug(f'futures={len(futures)}')
            assert len(futures) < 10 , "Processing not keeping up with incoming data"
            for f in futures:
                if f.done():
                    res = f.result()
                    futures.remove(f)
                    msg = send_notification_delayed(delayed_notifications,ts, res, delay=args.notification_delay, dry=args.dry)
                    if msg is not None:
                        futures.append(exc.submit(send_telegram, msg, args.dry))


def runner(args, stream):
    futures = []
    with ThreadPoolExecutor(max_workers=1) as exc:
        try:
            work(args, stream, exc, futures)
        finally:
            for future in futures:
                future.cancel()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--min_confidence', type=float, default=CONF_TRHRESH, help='minimum confidence threshold')
    parser.add_argument('--dry', action='store_true', help='do not upload to influx, send notifications')
    parser.add_argument('--debug', action='store_true', help='enable debug logs')
    parser.add_argument('--card', default=CARD, help='microphone card to look for')
    parser.add_argument('--channels', default=CHANNELS, type=int, help='microphone number of channels')
    parser.add_argument('--rate', default=RATE, type=int, help='microphone sampling rate (Hz)')
    parser.add_argument('--stride_seconds', default=STRIDE_SECONDS, help='buffer stride (in seconds) -> increase for RPi-3', type=int)
    parser.add_argument('--notification_delay', type=int, default=NOTIFICATION_DELAY_SECONDS, help='notificaiton delay')
    args = parser.parse_args()

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    stream = MicStream(args.rate, args.channels, CHUNK, args.card)
    stream.open()
    try:
        runner(args, stream)
    finally:
        stream.close()
