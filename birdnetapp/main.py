import alsaaudio
from concurrent.futures import ThreadPoolExecutor
import logging
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
import datetime

from .app import Worker, Config, MDATA

_LOGGER = logging.getLogger(__name__)

class MicStream():
    def __init__(self, rate, channels, periodsize, card):
        self.rate = rate
        self.periodsize = periodsize
        self.card = card
        self.stream = None
        self.channels = channels

    def open(self):
        cards = alsaaudio.cards()
        _LOGGER.info(f"Detected cards {cards} configuring card: '{self.card}'")
        card_i = cards.index(self.card)
        self.stream = alsaaudio.PCM(alsaaudio.PCM_CAPTURE, channels=self.channels, format=alsaaudio.PCM_FORMAT_S16_LE, rate=self.rate, periodsize=self.periodsize, cardindex=card_i)
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
        elif l != self.periodsize:
            raise Exception(f"Warning: incorrect frame length: got {l} expected {self.periodsize}")
        elif len(data) !=  exp:
            raise Exception(f"Warning: incorrect frame length: got {len(data)} expected {exp}")

        return data

    def close(self):
        if self.stream is not None:
            self.stream.close()
            self.stream = None
    def __del__(self):
        self.close()


def runner(args, stream):
    influx_client = InfluxDBClient(url=args.influx_url, token=args.influx_token, org=args.influx_org)
    write_api = influx_client.write_api(write_options=SYNCHRONOUS)
    query_api = influx_client.query_api()
    with ThreadPoolExecutor(max_workers=1) as exc:
        worker = Worker(args, stream, exc, write_api, query_api)
        try:
            worker.init()
            while True:
                try:
                    data = stream.read()
                except Exception as e:
                    _LOGGER.warning(e)
                    continue
                ts = datetime.datetime.now().replace(microsecond=0)
                worker.work(ts, data)
        finally:
            for future in worker.futures:
                future.cancel()

def main():
    
    args = Config.load()
    print('App CONFIG:', args)
    MDATA['lat'] = args.latitude
    MDATA['lon'] = args.longitude
    print('birdNet settings', MDATA)

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    stream = MicStream(args.rate, args.channels, args.rate, args.microphone)
    stream.open()
    try:
        runner(args, stream)
    finally:
        stream.close()
