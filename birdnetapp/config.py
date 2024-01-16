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

#segment length for analysis 
RECORD_SECONDS = 6

#birdNET settings
LAT=-1
LON=-1
# number of seconds of overlap within a segment. increases chance of detection at the expense of CPU usage
OVERLAP = 0
#pool mode -> max or average -> how to pool confidence of multiple results from one segment
# max has a higher detection rate at the expense of increased false detect rate
PMODE = 'max' # 'avg'
#sensitivity of detection. Values in [0.5, 1.5]. Defaults to 1.0. higher value is lower sensitivity
SENSITIVITY=1.0
#minimum prediction confidence threshold 
CONF_THRESH = 0.70

#birdNet server
HOST='127.0.0.1'
PORT = 8080

#time window of how long the bird must be not seen to trigger a telegram
SEEN_TIME = '14d'

# minimum detection count threshold for sending telegram notification
# setting to higher than 1 reduces false alarm rate
MIN_NOTIFICATION_COUNT = 1

#time window of app result fetch
APP_WINDOW = '14d'

