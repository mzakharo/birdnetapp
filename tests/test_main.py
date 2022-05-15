from birdnetapp import upload_result, send_telegram_delayed
import datetime

DRY=True

def test1():

    FILENAME = 'example/cardinal.wav'
    SAVEDIR = '/tmp/birdnetapp_test'
    res = dict(msg='success', results=[["Cardinalis cardinalis_Northern Cardinal", 0.5]])

    delayed_telegrams = {}
    ts = datetime.datetime.now().replace(microsecond=0)
    res = upload_result(ts, FILENAME, SAVEDIR, res, min_confidence=0, dry=DRY, force_telegram=True)
    send_telegram_delayed(delayed_telegrams, ts, res, 1, dry=DRY)
    assert len(delayed_telegrams) == 1

    #update but not send
    ts += datetime.timedelta(seconds=1)
    send_telegram_delayed(delayed_telegrams, ts, res, 1, dry=DRY)
    assert len(delayed_telegrams) == 1

    # send message
    ts += datetime.timedelta(seconds=1)
    send_telegram_delayed(delayed_telegrams, ts, None, 1, dry=DRY)
    assert len(delayed_telegrams) == 0
