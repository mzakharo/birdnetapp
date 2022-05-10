#Mic settings

#PS-Eye
RATE = 16000
CHANNELS = 4
CARD = 'CameraB409241'
CHUNK = RATE * 1 # 1 second buffer

#Files saved here
SAVEDIR = '/home/pi/birdNet'

#birdNET settings
RECORD_SECONDS = 9
CONF_TRHRESH = 0.5
LAT=43.544811
LON=-80.248108
OVERLAP = 1 # 2.4
PMODE = 'avg' # 'max'
SF_THRESH = 0.05 #reduce false positives

#birdNet server
HOST='127.0.0.1'
PORT = 8080

#influx
ORG = "home"
BUCKET = "main"

SEEN_TIME = '14d'


