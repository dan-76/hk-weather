#!/bin/sh
cd /home/pi/hk-weather &&
apikey=`cut -d ' ' -f 2 "/home/pi/hk-weather/APIKEY"` &&
/home/pi/.local/bin/pipenv run python3 /home/pi/hk-weather/hkweather/webbot.py -p 1137 -k $apikey