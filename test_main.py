from main import upload_result, send_telegram_delayed
import datetime

DRY=True

FILENAME = 'example/cardinal.wav'
SAVEDIR = '/tmp/birdnetapp_test'
res = dict(msg='success', results=[["Cardinalis cardinalis_Northern Cardinal", 0.5]])

delayed_telegrams = {}
ts = datetime.datetime.now().replace(microsecond=0)
res = upload_result(ts, FILENAME, SAVEDIR, res, min_confidence=0, dry=DRY, debug=True, force_telegram=True)
send_telegram_delayed(delayed_telegrams, ts, res, 1, dry=DRY)

#update but not send
ts += datetime.timedelta(seconds=1)
send_telegram_delayed(delayed_telegrams, ts, res, 1, dry=DRY)

# send message
ts += datetime.timedelta(seconds=1)
send_telegram_delayed(delayed_telegrams, ts, None, 1, dry=DRY)
