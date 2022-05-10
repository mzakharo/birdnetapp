from main import TELEGRAM_CHATID, TELEGRAM_TOKEN, send_telegram
import telebot

FILENAME = 'example/cardinal.wav'
tb = telebot.TeleBot(TELEGRAM_TOKEN, parse_mode='MARKDOWN')
res = dict(msg='success', results=[["Cardinalis cardinalis_Northern Cardinal", 0.5]])

result, conf = res['results'][0]
sci_result, result = result.split('_')
send_telegram(FILENAME, sci_result, result, conf)
