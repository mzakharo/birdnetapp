# birdnetapp

BirdNET App for raspberry Pi 3/4+

 - 24/7 recording from a USB microphone
 - local [BirdNET](https://github.com/kahst/BirdNET-Analyzer) analysis
 - saves bird detections to Influx2 Database
 - alerts for new birds over Telegram

- [Grafana](https://grafana.com/get/) visualizing data from Influx2 Database:

<img src="https://github.com/mzakharo/birdnetapp/blob/main/assets/grafana.png" width="850" height="360">

- Sample Telegram Notificaiton:

<img src="https://github.com/mzakharo/birdnetapp/blob/main/assets/telegram.png" width="400" height="200">


- Web App to listen to and visualize recorded content.


<img src="https://github.com/mzakharo/birdnetapp/blob/main/assets/home.jpg" width="250" height="500"><img src="https://github.com/mzakharo/birdnetapp/blob/main/assets/details.jpg" width="250" height="500">


## Assumptions
 - User has access to an Influx2 database instance (you can get a free one at [influxdata.com](https://cloud2.influxdata.com/signup))
 - User has a telegram [bot token](https://www.thewindowsclub.com/how-to-create-a-simple-telegram-bot) and a [chat id](https://stackoverflow.com/questions/32423837/telegram-bot-how-to-get-a-group-chat-id)

## Installation
 - cd to `/home/pi`
 ```bash
 git clone --recurse-submodules https://github.com/mzakharo/birdnetapp.git
 ```
 - In  the `birdnetapp/birdnetapp` folder, create a `secrets.py` with the following contents: 
 ```python
TELEGRAM_TOKEN = 'from_botfather'
TELEGRAM_CHATID = '#######'

INFLUX_URL = "http://host:PORT"
INFLUX_TOKEN= "XXXXXX"
INFLUX_ORG = "my_org"
INFLUX_BUCKET = "my_bucket"
 ```
 
 ### Optional: reduce SD card wear
 - setup `/tmp` as ramdisk:
```bash
sudo cp /usr/share/systemd/tmp.mount /etc/systemd/system/tmp.mount
sudo systemctl enable tmp.mount
sudo systemctl start tmp.mount
```
 - Disable rsyslog  `sudo apt remove rsyslog`
 - Move journal to ram edit `/etc/systemd/journald.conf`:
 ```
 Storage=volatile
RuntimeMaxUse=64M
```
 - `sudo systemctl restart systemd-journald`

## Installation (continued.)

 - Install requirements via `sudo apt install sox ffmpeg libasound2-dev`
 - Install dependencies via `sudo pip3 install -r requirements.txt`
 - Run the server:  `cd /home/pi/BirdNET-Analyzer && python3 server.py`
 - Edit [config.py](https://github.com/mzakharo/birdnetapp/blob/main/birdnetapp/config.py) and adjust Microphone (`RATE`, `CARD`, `CHANNELS`), and birdnet (`LON`/`LAT`) settings
 - Run the app: `cd /home/pi/birdnetapp && python3 main.py`
 - NOTE: for raspberry Pi 3, the command is `python3 main.py --stride_seconds 5`
 - Optional: install systemd services to run on startup via `birdnet_main.service` and `birdnet_server.service`
  ```
sudo cp birdnet_server.service  /lib/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable birdnet_server.service 
sudo systemctl start birdnet_server.service 
sudo systemctl status birdnet_server.service 
  ```

## Tips
 - Telegram notification cooldown is controlled by `SEEN_TIME` variable in [config.py](https://github.com/mzakharo/birdnetapp/blob/main/birdnetapp/config.py). If a bird has already been seen within this time window, it will not trigger Telegram notificaitons
 - Telegram notification is issued after the bird stops tweeting and `NOTIFICATION_DELAY_SECONDS` elapses (from [config.py](https://github.com/mzakharo/birdnetapp/blob/main/birdnetapp/config.py)). This ensures the 'best' recording is notified with, not the first. Set to `0` to disable the delay. 
 - To test Telegram capability in isolation, run `PYTHONPATH=. python3 tests/test_telegram.py`
 - Default recording save directory is specified in [config.py](https://github.com/mzakharo/birdnetapp/blob/main/birdnetapp/config.py), `SAVEDIR` variable
 
 ## Web App 
  - Serve the Web App by running `./flask.sh` 
  - Optional: install a systemd service file to run on startup via `birdnet_app.service`
 
 ## Test the app (Development)
  - Install the test framework
  ```bash
  pip3 install tox
  ```
  - Run unit tests
   ```bash
   tox
   ```
 ## Influx Query for the Bar Gauge Grafana Widget 
 ```influx
  from(bucket: "main")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r["_measurement"] == "birdnet")
  |> count()
  |> group()
  |> sort(desc:true)
  |> keep(columns: ["_field", "_value"])
  |> rename(columns: { _value: ""})
  ```
