# birdnetapp

BirdNET App for Raspberry Pi/BeagleBone

 - 24/7 recording from a USB microphone
 - local [BirdNET](https://github.com/kahst/BirdNET-Analyzer) analysis
 - Influx2 Database support
 - Telegram alerts
 - Web App for listening & visualizing captured audio

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
 - cd `$HOME`
 ```bash
 git clone --recurse-submodules https://github.com/mzakharo/birdnetapp.git
 ```
 - Copy `config.example.yaml` to  `config.yaml`  and fill in the details according to your hardware and environment


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
 - for Beaglebone: Use BirdNET-Analyzer @ `5b6d1c3`. As this is the last model that is fast enough for this platform
 - for BeagleBone: `sudo apt instal llvm-dev libatlas-base-dev libsndfile1`
 - for BeagleBone: `pip3 install numba==0.56.4`
 - for BeagleBone: `pip3 install beaglebone/tflite_runtime-2.16.0-cp39-cp39-linux_armv7l.whl`
 - Install dependencies via `pip3 install -r requirements.txt`
 - Run the server:  `cd $HOME/birdnetapp/BirdNET-Analyzer && python3 server.py`
 - Run the app: `cd $HOME/birdnetapp && python3 main.py`

 - Optional: install systemd services to run on startup via `birdnet_main.service` and `birdnet_server.service`
  ```
sudo cp birdnet_server@.service  /lib/systemd/system/
sudo cp birdnet_main@.service  /lib/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable birdnet_server@$USER.service 
sudo systemctl start birdnet_server@$USER.service 
sudo systemctl status birdnet_server@$USER.service
sudo systemctl enable birdnet_main@$USER.service 
sudo systemctl start birdnet_main@$USER.service 
sudo systemctl status birdnet_main@$USER.service 
  ```

 ## Web App 
  - install deps in system: `sudo pip3 install flask tzlocal gunicorn`
  - Serve the Web App by running `./flask.sh` 
  - Optional: install a systemd service file to run on startup via `birdnet_app@.service`

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
