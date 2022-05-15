from main import send_telegram
from pydub import AudioSegment

FILENAME = 'example/cardinal.wav'
export_filename = '/tmp/cardinal.mp3'
res = dict(msg='success', results=[["Cardinalis cardinalis_Northern Cardinal", 0.5]])
AudioSegment.from_wav(FILENAME).export(export_filename, format="mp3", parameters=["-ac", "1", "-vol", "150", "-q:a",  "9"])

result, conf = res['results'][0]
sci_result, result = result.split('_')
count = 1
send_telegram(export_filename, sci_result, result, conf, count, dry=True)
