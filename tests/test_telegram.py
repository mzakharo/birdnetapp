from birdnetapp.app import send_telegram
from pydub import AudioSegment

def test1(dry=True):
    FILENAME = 'example/cardinal.wav'
    export_filename = '/tmp/cardinal.mp3'
    res = dict(msg='success', results=[["Cardinalis cardinalis_Northern Cardinal", 0.5]])
    AudioSegment.from_wav(FILENAME).export(export_filename, format="mp3", parameters=["-ac", "1", "-vol", "150", "-q:a",  "9"])

    result, conf = res['results'][0]
    sci_result, result = result.split('_')
    count = 1
    msg = {'fname' : export_filename,'sci' :  sci_result, 'name' : result, 'conf' : conf, 'count' : count }
    send_telegram(msg, dry=dry)

if __name__ == '__main__':
    test1(dry=False)
