from birdnetapp import upload_result

FILENAME = 'example/cardinal.wav'
SAVEDIR = '/tmp/birdnetapp_test'
res = dict(msg='success', results=[["Cardinalis cardinalis_Northern Cardinal", 0.5]])
upload_result(FILENAME, SAVEDIR, res, confidence=0, dry=True, debug=True)
