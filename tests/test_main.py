from birdnetapp.app import Worker, send_notification_delayed, send_telegram, get_parser
import datetime
from copy import deepcopy
import pandas as pd
from concurrent.futures import Future, Executor
from threading import Lock




class Query:
    def __init__(self):
        self.data = ["foo"]
    def query_data_frame(self, foo):
        df = pd.DataFrame(self.data, columns=['_value'])
        return df
    def write(self, bucket, org, point): pass

class Args:pass

class MocStream:
    channels = 2
    periodsize = 48000
    rate = 48000


class DummyExecutor(Executor):

    def __init__(self):
        self._shutdown = False
        self._shutdownLock = Lock()

    def submit(self, fn, *args, **kwargs):
        with self._shutdownLock:
            if self._shutdown:
                raise RuntimeError('cannot schedule new futures after shutdown')

            f = Future()
            try:
                result = fn(*args, **kwargs)
            except BaseException as e:
                f.set_exception(e)
            else:
                f.set_result(result)

            return f

    def shutdown(self, wait=True):
        with self._shutdownLock:
            self._shutdown = True


def test1():

    q = Query()

    args = Args()
    args.min_confidence = 0
    args.dry = False

    w = Worker(args, None, None, q, q)

    FILENAME = 'example/cardinal.wav'
    SAVEDIR = '/tmp/birdnetapp_test'
    res = dict(msg='success', results=[["Cardinalis cardinalis_Northern Cardinal", 0.5]])
    delayed_notifications = {}

    ts = datetime.datetime.now().replace(microsecond=0)
    msg = w.upload_result(ts, FILENAME, SAVEDIR, res)
    assert msg['notify'] == True
    
    #test not sending notification if the bird already exists
    q.data = ['Northern Cardinal']
    msg_mute = w.upload_result(ts, FILENAME, SAVEDIR, res)
    assert msg_mute['notify'] == False

    out = send_notification_delayed(delayed_notifications, ts, deepcopy(msg_mute), 0)
    assert len(delayed_notifications) == 0
    assert out is None

    args.min_confidence = 1
    msg2 = w.upload_result(ts, FILENAME, SAVEDIR, res)
    assert msg2 is None

    res['results'] = []
    msg2 = w.upload_result(ts, FILENAME, SAVEDIR, res)
    assert msg2 is None

    res['msg'] = 'fail'
    msg2 = w.upload_result(ts, FILENAME, SAVEDIR, res)
    assert msg2 is None

    out = send_notification_delayed(delayed_notifications, ts, deepcopy(msg), 1)
    assert len(delayed_notifications) == 1
    assert out is None

    #update but not send
    ts += datetime.timedelta(seconds=1)
    out = send_notification_delayed(delayed_notifications, ts, deepcopy(msg_mute), 1)
    assert len(delayed_notifications) == 1
    assert out is None

    #update lower conf but not send
    ts += datetime.timedelta(seconds=1)
    msg_mute['conf'] = 0.1 #lower confidence, should increment count, ts
    out = send_notification_delayed(delayed_notifications, ts, deepcopy(msg_mute), 1)
    assert len(delayed_notifications) == 1
    n = delayed_notifications['Northern Cardinal']
    assert n['conf'] == 0.5
    assert out is None

    ts += datetime.timedelta(seconds=1)
    msg_mute['conf'] = 0.99 #higher confidence, should increment count, ts
    out = send_notification_delayed(delayed_notifications, ts, deepcopy(msg_mute), 1)
    assert len(delayed_notifications) == 1
    n = delayed_notifications['Northern Cardinal']
    assert n['conf'] == 0.99
    assert out is None

    # send message
    ts += datetime.timedelta(seconds=1)
    out = send_notification_delayed(delayed_notifications, ts, None, 1)
    assert len(delayed_notifications) == 0
    assert out is not None
    assert out['count'] == 4
    so = send_telegram(out, dry=True)
    assert so is None


def test_worker():
    q = Query()
    args = get_parser().parse_args("")
    args.dry = True
    args.notification_delay = 0
    stream = MocStream()
    exc = DummyExecutor()
    w = Worker(args, stream, exc, q, q)
    w.sendRequest = lambda host, port, fpath, mdata :  dict(msg='success', results=[["Cardinalis cardinalis_Northern Cardinal", 0.6]])
    w.init()

    ts = datetime.datetime.now().replace(microsecond=0)
    data = bytearray(48000)

    #process data until telegram message is queued
    while  (msg := w.work(ts, data)) is None: pass
    assert 'Cardinal' in msg['name']

    #make sure there is a pending telegram
    assert len(w.futures)

    #send the pending telegram
    while w.futures:
        w.work(ts, data)


