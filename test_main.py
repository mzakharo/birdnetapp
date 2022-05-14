from main import upload_result
import datetime

FILENAME = 'example/cardinal.wav'
SAVEDIR = '/tmp/birdnetapp_test'
res = dict(msg='success', results=[["Cardinalis cardinalis_Northern Cardinal", 0.5]])

ts = datetime.datetime.now().replace(microsecond=0)
upload_result(ts, FILENAME, SAVEDIR, res, min_confidence=0, dry=False, debug=True)
