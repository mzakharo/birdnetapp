# birdnetapp
BirdNET App for raspberry Pi that saves bird sightings to Influx, alerts over Telegram

## Assumptions
 - User has access to an InfluxDB instance
 - User has a telegram bot token and a chat id

## Installation
 - Clone BirdNet-Analyzer repository https://github.com/kahst/BirdNET-Analyzer.git  to `/home/pi`
 - Follow BirdNet-Analyzer [README](https://github.com/kahst/BirdNET-Analyzer#setup-ubuntu) instructions for Ubuntu/Linux.
 - Clone this repository to `/home/pi`
 - In  the `birdnetapp/birdnetapp` folder, create a `secrets.py` with the following contents: 
 ```
TELEGRAM_TOKEN = 'blah'
TELEGRAM_CHATID = '-XXXXX'

INFLUX_URL = "http://host:PORT"
INFLUX_TOKEN= "XXXXXX"
 ```
 - setup `/tmp` as ramdisk:
```
sudo cp /usr/share/systemd/tmp.mount /etc/systemd/system/tmp.mount
sudo systemctl enable tmp.mount
sudo systemctl start tmp.mount
```
 - Disable rsyslog filliup up the SD card:  `sudo apt remove rsyslog`
 - Move journal to ram edit `/etc/systemd/journald.conf`:
 ```
 Storage=volatile
RuntimeMaxUse=64M
```
 - `sudo systemctl restart systemd-journald`
 - Install requirements via `sudo apt install sox ffmpeg libasound-dev`
 - Install dependencies via `pip3 install -r requirements.txt`
 - Run the server:  `cd /home/pi/BirdNET-Analyzer && python3 server.py`
 - Edit [config.py](https://github.com/mzakharo/birdnetapp/blob/main/birdnetapp/config.py) and adjust Microphone (`RATE`, `CARD`, `CHANNELS`), and birdnet (`LON`/`LAT`) settings
 - Run the app: `cd /home/pi/birdnetapp && python3 main.py`
 - Optional: install systemd services to run on startup `birdnet_main.service` and `birdnet_server.service`

## Tips
 -  Default influx bucket is `main`, org `home`. Change this with `ORG` and `BUCKET` variables in [config.py](https://github.com/mzakharo/birdnetapp/blob/main/birdnetapp/config.py)
 - Telegram notification cooldown is controlled by `SEEN_TIME` variable in [config.py](https://github.com/mzakharo/birdnetapp/blob/main/birdnetapp/config.py). If a bird has been seen within this time window, it will not trigger notificaitons
 - Default recording save directory is specified in [config.py](https://github.com/mzakharo/birdnetapp/blob/main/birdnetapp/config.py), `SAVEDIR` variable
 - User can expose `SEVEDIR` directory over web broser through `birdnet_browser.service`
