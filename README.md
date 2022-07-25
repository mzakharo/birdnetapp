# birdnetapp
BirdNET App for raspberry Pi 3/4+ that saves bird sightings to Influx, alerts over Telegram

## Assumptions
 - User has access to an InfluxDB instance (you can get a free one at [influxdata.com](https://cloud2.influxdata.com/signup)
 - User has a telegram bot token and a chat id [Instructions](https://nocodeapi.com/telegram-bot-with-nocode-and-get-notifications)

## Installation
 - Clone BirdNet-Analyzer repository https://github.com/kahst/BirdNET-Analyzer.git  to `/home/pi`
 - Follow BirdNet-Analyzer [README](https://github.com/kahst/BirdNET-Analyzer#setup-ubuntu) instructions for Ubuntu/Linux.
 - Clone this repository to `/home/pi`
 - In  the `birdnetapp/birdnetapp` folder, create a `secrets.py` with the following contents: 
 ```
TELEGRAM_TOKEN = 'blah'
TELEGRAM_CHATID = 'XXXXX'

INFLUX_URL = "http://host:PORT"
INFLUX_TOKEN= "XXXXXX"
INFLUX_ORG = "my_org"
INFLUX_BUCKET = "my_bucket"
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
 - Install requirements via `sudo apt install sox ffmpeg libasound2-dev`
 - Install dependencies via `sudo pip3 install -r requirements.txt`
 - Run the server:  `cd /home/pi/BirdNET-Analyzer && python3 server.py`
 - Edit [config.py](https://github.com/mzakharo/birdnetapp/blob/main/birdnetapp/config.py) and adjust Microphone (`RATE`, `CARD`, `CHANNELS`), and birdnet (`LON`/`LAT`) settings
 - Run the app: `cd /home/pi/birdnetapp && python3 main.py`
 - NOTE: for raspberry Pi 3, the command is `python3 main.py --stride_seconds 5`
 - Optional: install systemd services to run on startup `birdnet_main.service` and `birdnet_server.service`

## Tips
 - Telegram notification cooldown is controlled by `SEEN_TIME` variable in [config.py](https://github.com/mzakharo/birdnetapp/blob/main/birdnetapp/config.py). If a bird has been seen within this time window, it will not trigger notificaitons
 - Telegram messages are sent after the bird stops tweeting and `NOTIFICATION_DELAY_SECONDS` elapses (from [config.py](https://github.com/mzakharo/birdnetapp/blob/main/birdnetapp/config.py)).  This allows for the 'best' recording to be sent, not the first.
 - To test Telegram capability in isolation, run `PYTHONPATH=. python3 tests/test_telegram.py`
 - Default recording save directory is specified in [config.py](https://github.com/mzakharo/birdnetapp/blob/main/birdnetapp/config.py), `SAVEDIR` variable
 - User can expose `SEVEDIR` directory over web broser through `birdnet_browser.service`
