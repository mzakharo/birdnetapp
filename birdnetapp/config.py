#Mic settings

#PS-Eye
RATE = 48000
CHANNELS = 2
CARD = 'Device'
CHUNK = RATE * 1 # 1 second buffer

#Files saved here
SAVEDIR = '/home/pi/birdNet'

#Number of most recent files to keep per bird
KEEP_FILES = 300

#whether store longterm results in wav or mp3
EXPORT_FORMAT = '.mp3'

#how long to wait before sending a notification
NOTIFICATION_DELAY_SECONDS = 60*5

#birdNET settings

#Note: recording length has impact on conf_thresh
#longer recording could lower CONF_THRESH to achieve the same detection rate
RECORD_SECONDS = 6
CONF_TRHRESH = 0.55
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


