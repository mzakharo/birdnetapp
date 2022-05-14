#Mic settings

#PS-Eye
RATE = 16000
CHANNELS = 4
CARD = 'CameraB409241'
CHUNK = RATE * 1 # 1 second buffer

#Files saved here
SAVEDIR = '/home/pi/birdNet'

#Number of most recent files to keep per bird
KEEP_FILES = 200

#whether store longterm results in wav or mp3
EXPORT_FORMAT = '.wav'

#birdNET settings
RECORD_SECONDS = 6
CONF_TRHRESH = 0.6
LAT=43.544811
LON=-80.248108
OVERLAP = 0

#birdNet server
HOST='127.0.0.1'
PORT = 8080

#influx
ORG = "home"
BUCKET = "main"

SEEN_TIME = '14d'


