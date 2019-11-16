import argparse

from webbot import check_weather, check_rain

def get_parser():
    parser = argparse.ArgumentParser(description='instant trigger IFTTT bot via the command line')
    parser.add_argument('option', metavar='OPTION', type=str,
                        help='options: currentweather, rainforcast')
    return parser

def command_line_runner():
    parser = get_parser()
    args = vars(parser.parse_args())

    if not args['option']:
        parser.print_help()
        return

    d = {}
    with open("APIKEY") as f:
        for line in f:
            (key, val) = line.split()
            d[key] = val
        
    IFTTT_KEY = d['ifttt_web_api_key']

    if args['option'] == 'currentweather':
        print(check_weather(IFTTT_KEY))
    elif args['option'] == 'rainforcast':
        print(check_rain(IFTTT_KEY))
    else:
        parser.print_help()

if __name__ == "__main__":
    command_line_runner()