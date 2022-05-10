from birdnetapp import send_telegram

FILENAME = 'example/cardinal.wav'
res = dict(msg='success', results=[["Cardinalis cardinalis_Northern Cardinal", 0.5]])

result, conf = res['results'][0]
sci_result, result = result.split('_')
send_telegram(FILENAME, sci_result, result, conf, dry=True)
