from birdnetapp import upload_result, send_notification_delayed
import datetime
from copy import deepcopy

DRY=True

def test1():

    FILENAME = 'example/cardinal.wav'
    SAVEDIR = '/tmp/birdnetapp_test'
    res = dict(msg='success', results=[["Cardinalis cardinalis_Northern Cardinal", 0.5]])

    delayed_notifications = {}
    ts = datetime.datetime.now().replace(microsecond=0)
    msg = upload_result(ts, FILENAME, SAVEDIR, res, min_confidence=0, dry=DRY, force_notify=True)

    out = send_notification_delayed(delayed_notifications, ts, deepcopy(msg), 1, dry=DRY)
    assert len(delayed_notifications) == 1
    assert len(out) == 0

    #update but not send
    ts += datetime.timedelta(seconds=1)
    out = send_notification_delayed(delayed_notifications, ts, deepcopy(msg), 1, dry=DRY)
    assert len(delayed_notifications) == 1
    assert len(out) == 0

    #update lower conf but not send
    ts += datetime.timedelta(seconds=1)
    msg['conf'] = 0.1 #lower confidence, should increment count, ts
    out = send_notification_delayed(delayed_notifications, ts, deepcopy(msg), 1, dry=DRY)
    assert len(delayed_notifications) == 1
    assert len(out) == 0

    # send message
    ts += datetime.timedelta(seconds=1)
    out = send_notification_delayed(delayed_notifications, ts, None, 1, dry=DRY)
    assert len(delayed_notifications) == 0
    assert len(out) == 1
    assert out[0]['count'] == 3

    
