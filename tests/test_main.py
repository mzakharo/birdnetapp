import telebot
from main import upload_result

FILENAME = 'example/cardinal.wav'

res = dict(msg='success', results=[["Cardinalis cardinalis_Northern Cardinal", 0.5]])
upload_result(FILENAME, res, True)
