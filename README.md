# birdnetapp
BirdNET App for raspberry Pi that saves bird sightings to Influx, alerts over Telegram

## Assumptions
 - User has access to an InfluxDB instance
 - User has telegram bot token and chat id

## Installation
 - clone BirdNet-Analyzer repository https://github.com/kahst/BirdNET-Analyzer.git  to `/home/pi`
 - follow BirdNet-Analyzer [README](https://github.com/kahst/BirdNET-Analyzer#setup-ubuntu) instructions for Ubuntu/Linux.
 - clone this repository to `/home/pi`
 - in root folder of this repository, create a secrets.py with the following contents: 
 ```
TELEGRAM_TOKEN = 'blah'
TELEGRAM_CHATID = '-XXXXX'

INFLUX_URL = "http://host:PORT"
INFLUX_TOKEN= "XXXXXX"
 ```
 - Install dependencies via `pip3 install -r requirements.txt`
 - sudo apt install sox ffmpeg
 - run the server:  `cd /home/pi/BirdNET-Analyzer && python3 server.py`
 - Edit [config.py](https://github.com/mzakharo/birdnetapp/blob/main/birdnetapp/config.py) and adjust Microphone (`RATE`, `CARD`, `CHANNELS`), and birdnet (`LON`/`LAT`) settings
 - run the app: `cd /home/pi/birdnetapp && python3 main.py'
 - Optional: install systemd services to run on startup `birdnet_main.service` and `birdnet_server.service`

## Tips
 -  default influx bucket is `main`, org `home`. Change this with `ORG` and `BUCKET` variables in [config.py](https://github.com/mzakharo/birdnetapp/blob/main/birdnetapp/config.py)
 - Telegram notification cooldown is controlled by `SEEN_TIME` variable in [config.py](https://github.com/mzakharo/birdnetapp/blob/main/birdnetapp/config.py). If a bird has been seen within this time window, it will not trigger notificaitons
 - default recording save directory is specified in [config.py](https://github.com/mzakharo/birdnetapp/blob/main/birdnetapp/config.py), `SAVEDIR` variable
 - User can expose `SEVEDIR` directory over web broser through `birdnet_browser.service`
