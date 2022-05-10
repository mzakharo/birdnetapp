# birdnetapp
BirdNET App for raspberry Pi that saves bird sightings to Influx, alerts over Telegram

## Assumptions
 - User has access to a InfluxDB instance
 - User has telegram bot token and chat id
 - default recording save directory is specified in main.py, `SAVEDIR` variable
 - User can expose this directory over samba

## Installation
 - clone BirdNet-Analyzer repository https://github.com/kahst/BirdNET-Analyzer.git  to `/home/pi`
 - clone this repository to `/home/pi`
 - in root folder of this repository, create a secrets.py with the following contents: 
 ```
TELEGRAM_TOKEN = 'blah'
TELEGRAM_CHATID = '-XXXXX'

INFLUX_URL = "http://host:PORT"
INFLUX_TOKEN= "some_stuff"
 ```
 - Install dependencies via `pip3 install -r requirements.txt`
 - run the server:  `cd /home/pi/BirdNET-Analyzer && python3 server.py`
 - Edit birdnetapp/main.py and adjust Microphone (RATE, CARD, CHANNELS), and birdnet (LON/LAT) settings
 - run the app: `cd /home/pi/birdnetapp && python3 main.py'
 - Optional: install systemd services to run on startup `birdnet_main.service` and `birdnet_server.service`
