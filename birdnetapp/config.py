from os import environ
HOME = environ.get('HOME', '.')

# Mic settings

#Audio Card sampling rate
RATE = 48000
#Number of channels to use
CHANNELS = 2
#Card name as it appears in 'arecord -l'
CARD = 'PCH'

#Files saved here
SAVEDIR = f'{HOME}/birdNet'

#Number of most recent files to keep per bird
KEEP_FILES = 300

#whether store longterm results in wav or mp3
EXPORT_FORMAT = '.mp3'

#how long to wait before sending a notification
#used to gather multiple recordings and choose the best
# to send over telegram
NOTIFICATION_DELAY_SECONDS = 60*5

#birdNET settings

#Note: recording length has impact on conf_thresh
#longer recording could lower CONF_THRESH to achieve the same detection rate
RECORD_SECONDS = 6
STRIDE_SECONDS = (RECORD_SECONDS) // 2
CONF_TRHRESH = 0.55
LAT=43.544811
LON=-80.248108
OVERLAP = 0

#birdNet server
HOST='127.0.0.1'
PORT = 8080

#time window of how long the bird must be not seen to trigger a telegram
SEEN_TIME = '14d'

#time window of app result fetch
APP_WINDOW = '14d'

