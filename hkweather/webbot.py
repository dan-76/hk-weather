# Standard library imports
import argparse
import logging
import os
# Third-party imports
import requests
from bottle import route, run
# Application-specific imports
import weatherchecker


def send_signal_to_ifttt(event, key, values=None):
    URL_FORMAT = 'https://maker.ifttt.com/trigger/{event}/with/key/{key}'
    url = URL_FORMAT.format(event=event, key=key)
    r = requests.post(url, json=values)
    if r.status_code == 200:
        return r.text

def check_weather(ifttt_key):
    message =  'OK! System checking current weather.'
    result_dict = weatherchecker.get_current_weather()
    weather_summary = result_dict['short_summary_msg']
    weather_msg = result_dict['long_summary_msg']
    weather_url = result_dict['weather_img_url']
    result_text = send_signal_to_ifttt('current_weather', ifttt_key, 
                                        {'value1':weather_summary,
                                        'value2': weather_msg, 
                                        'value3': weather_url})
    return message

def check_rain(ifttt_key, location={'lat':22.3236917,'lon':114.1600986}, retry=5, silence=False):
    message =  'OK! System checking 2 hours rainfall.'
    result_dict = weatherchecker.get_rain_forcast(location,retry)
    if result_dict['hv_result']:
        if not silence or not result_dict['no_rain']:
            signal_dict = {'value1':result_dict['short_summary_msg'],
                            'value2': result_dict['long_summary_msg']}
            if result_dict['rain_img_url']:
                signal_dict['value3'] = result_dict['rain_img_url']
            result_text = send_signal_to_ifttt('rain_forcast', ifttt_key, 
                                                signal_dict)
    return message

def _bottle_server_setup(ifttt_key=''):
    # Handle http requests to /iftttbot
    @route('/iftttbot/<option>')
    def ifttt(option=''):
        message = 'Please specify the correct option'

        if len(ifttt_key) == 43:
            if option == 'currentweather':
                message = check_weather(ifttt_key)
                
            elif option == 'rainforcast':
                message = check_rain(ifttt_key)

        return message

    @route('/iftttbot/rainforcast/silence')
    def ifttt(option=''):
        message = check_rain(ifttt_key, silence=True)
        return message + ' (Silence)'

    @route('/iftttbot/<option>/<apikey>')
    def ifttt(option='', apikey=''):
        message = 'Please specify the correct option & Key'
        
        if len(apikey) == 43:
            if option == 'currentweather':
                message = check_weather(apikey)
                
            elif option == 'rainforcast':
                message = check_rain(apikey)

        return message

    @route('/:url#.*#')
    def home(url):
        return 'Error'

def get_parser():
    parser = argparse.ArgumentParser(description='Host webbot server by command line.')
    parser.add_argument('-p', type=int, dest='port', required=True, 
                        help='REQUIRED. Server listen to port.')
    parser.add_argument('-k', type=str, dest='apikey', 
                        help='IFTTT Webhooks API key.')
    return parser

def command_line_runner():
    parser = get_parser()
    args = vars(parser.parse_args())
    
    if args['apikey'] is None:
        IFTTT_KEY = os.environ.get("ifttt_web_api_key")

    IFTTT_KEY = args['apikey']

    if IFTTT_KEY is None:
        print("IFTTT Key is required in either argument or in environment")
        parser.print_help()
        return

    _bottle_server_setup(IFTTT_KEY)
    run(host='0.0.0.0', port=args['port'])

if __name__ == "__main__":
    command_line_runner()