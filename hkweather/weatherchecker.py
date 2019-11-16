# Filename: weatherchecker.py
# coding=utf-8

# Standard library imports
import logging
import re
import json
from textwrap import dedent
import urllib.parse as urlparse
from urllib.parse import urlencode
from urllib.request import urlopen
from subprocess import check_output
# Third-party imports
import dateutil.parser

from bs4 import BeautifulSoup, CData
from dateutil import tz
# Application-specific imports


logging.basicConfig()

current_weather_url = {
    "en": "http://rss.weather.gov.hk/rss/CurrentWeather.xml",
    "uc": "http://rss.weather.gov.hk/rss/CurrentWeather_uc.xml",
    "td": "http://rss.weather.gov.hk/rss/LocalWeatherForecast_uc.xml",
    "9d": "http://rss.weather.gov.hk/rss/SeveralDaysWeatherForecast_uc.xml"
}

def _search_result_or_empty(pattern, string):
    result = re.search(pattern, string)
    if result is None:
        return ''
    return result.group(1)

def _get_soup_from_url(url):
    html = urlopen(url)
    page = html.read()
    return BeautifulSoup(page, 'html.parser')

def _get_soup_for_cdata(htmlsoup):
    des_html = htmlsoup.find(text=lambda tag: isinstance(tag, CData)).string.strip()
    return BeautifulSoup(des_html, 'html.parser')

def _format_strip_all_whitespace(msg):
    return "".join(msg.split())

def _format_weather_msg(pub_date,temp,rel_humidity,uv_index,uv_level,warning_msg,
                        predict,desc9d,summary):
    result = dedent(f"""
    氣溫: {temp} 度
    相對濕度: 百分之 {rel_humidity}""")

    if uv_index:
        result += dedent(f"""
        曝曬級數: {uv_level}
        紫外線指數: {uv_index}""")

    if warning_msg:
        result += dedent(f"""
        {warning_msg}""")

    if predict:
        result += dedent(f"""
        {predict}""")

    if desc9d:
        result += dedent(f"""
        {desc9d}""")
    
    result += dedent(f"""
    本日預測: {summary}
    報告時間: {pub_date.astimezone(tz.tzlocal()):%Y-%m-%d %H:%M:%S}
    """)

    return result

def get_current_weather():
    html_soup = _get_soup_from_url(current_weather_url['en'])
    des_item = _get_soup_for_cdata(html_soup)
    des_text = des_item.get_text()

    weather_dict = {}
    weather_dict['author'] = html_soup.author.text
    weather_dict['publication_date_text'] = html_soup.pubdate.text
    weather_dict['publication_date'] = dateutil.parser.parse(weather_dict['publication_date_text'])
    weather_dict['weather_img_url'] = des_item.find('img')['src']
    weather_dict['weather_img_number'] = _search_result_or_empty(
                                            r'http://rss.weather.gov.hk/img/pic(\d+).png', 
                                            weather_dict['weather_img_url'])
    weather_dict['temperature'] = _search_result_or_empty(
                                    r'Air temperature.* (\d+).*degrees Celsius', 
                                    des_text)
    weather_dict['relative_humidity'] = _search_result_or_empty(
                                            r'Relative Humidity.* (\d+).*per cent', 
                                            des_text)
    weather_dict['uv_index'] = _search_result_or_empty(r"the mean UV Index recorded at King's Park.* (\d+)", des_text)
    weather_dict['uv_level'] = _search_result_or_empty(r'Intensity of UV radiation : (\S*) ', des_text)
    weather_dict['rainfall_exist'] = _search_result_or_empty(r'(.*the rainfall recorded in various regions were.*)', des_text)
    if weather_dict['rainfall_exist']:
        rainfall_table = des_item.find_all('table')[1]
        rainfall_data = [x.text for x in rainfall_table.find_all('tr')]

    html_soup_uc = _get_soup_from_url(current_weather_url['uc'])
    des_item_uc = _get_soup_for_cdata(html_soup_uc)
    weather_dict['prediction'] = _search_result_or_empty(u'(預 料 .*)', 
                                                            des_item_uc.get_text())
    des_text_warning_item = des_item_uc.find('span', {'id':'warning_message'})
    if des_text_warning_item is None:
        weather_dict['warning'] = ""
    else:
        weather_dict['warning'] = des_text_warning_item.text

    html_soup_9d = _get_soup_from_url(current_weather_url['9d'])
    des_item_9d = _get_soup_for_cdata(html_soup_9d)
    des_text_9d = des_item_9d.get_text()
    weather_dict['days_description'] = _format_strip_all_whitespace(
                                            _search_result_or_empty(
                                                u'(天 氣 概 況 ：.*)  ', 
                                                des_text_9d)
                                        )
    
    html_soup_td = _get_soup_from_url(current_weather_url['td'])
    des_item_td = _get_soup_for_cdata(html_soup_td)
    des_text_td = des_item_td.get_text()
    weather_dict['short_summary_msg'] = _format_strip_all_whitespace(
                                            _search_result_or_empty(
                                                u'天氣預測:(.*)', 
                                                des_text_td)
                                        )
    weather_dict['long_summary_msg'] = _format_weather_msg(
                                        pub_date=weather_dict['publication_date'],
                                        temp=weather_dict['temperature'],
                                        rel_humidity=weather_dict['relative_humidity'],
                                        uv_index=weather_dict['uv_index'],
                                        uv_level=weather_dict['uv_level'],
                                        warning_msg=weather_dict['warning'],
                                        predict=weather_dict['prediction'],
                                        desc9d=weather_dict['days_description'],
                                        summary=weather_dict['short_summary_msg']
                                    )

    return weather_dict

def _parse_png_str_2_number(rpath):
    result_dict_num = {
        'noRain' : 0,
        'rain01' : 1,
        'rain02' : 2,
        'rain03' : 3,
        'none' : -100
    }

    p = re.search(r'images/(.*).png', rpath)
    if p is None:
        return -100
    else:
        try:
            return result_dict_num[p.group(1)]
        except KeyError:
            return -1000

def _run_node_js_and_parse_result(url,retry):
    js_command = ["node","./hkweather/get_rain.js",url,str(retry)]
    result = check_output(js_command)
    try:
        d = json.loads(result, encoding='utf-8')

        src_orig = []
        alt_orig = []
        for item in d:
            src_orig.append(item[u'src'])
            alt_orig.append(item[u'alt'])
        
        return list(map(_parse_png_str_2_number, src_orig)), alt_orig
    except:
        return None, None

def _get_nearest_rain_time(rlist, threshold=0):
    for i, element in enumerate(rlist):
        if element > threshold:
            return i

    return -1

def _get_nearest_stop_time(rlist, start, threshold=0):
    for i, element in enumerate(rlist[start:]):
        if rlist[i] == threshold:
            return start + i

    return -1

def _format_rain_msg(time,short_summary,rain_time_list):
    result = dedent(f"""
    {time}降雨預報:""")

    for item in rain_time_list:
        result += dedent(f"""
        {item}""")

    result += dedent(f"""
    {short_summary}""")

    return result

def get_rain_forcast(location={'lat':22.2911095,'lon':114.2003418}, retry=5):
    base_url = r'https://www.weather.gov.hk/m/nowcast/hk_rainfall_uc.htm'
    if location:
        params = {'lat':str(location['lat']),'lon':str(location['lon'])}
        url_parts = list(urlparse.urlparse(base_url))
        query = dict(urlparse.parse_qsl(url_parts[4]))
        query.update(params)
        url_parts[4] = urlencode(query)
        url = urlparse.urlunparse(url_parts)
    else:
        url = base_url

    rain_num_list, rain_details_list = _run_node_js_and_parse_result(url=url, retry=str(retry))

    rain_map_time = {
        0 : u'半個鐘內',
        1 : u'一個鐘內',
        2 : u'個半鐘內',
        3 : u'兩個鐘內'
    }
    rain_map_url = {
        1 : 'https://www.weather.gov.hk/m/nowcast/images/rain01.png',
        2 : 'https://www.weather.gov.hk/m/nowcast/images/rain02.png',
        3 : 'https://www.weather.gov.hk/m/nowcast/images/rain03.png'
    }

    rain_dict = {}
    if rain_num_list:
        rain_dict['hv_result'] = True
        rain_dict['report_time'] = rain_details_list[0][:5]
        rain_dict['rain_nearest'] = _get_nearest_rain_time(rain_num_list)
        rain_dict['no_rain'] = not any(i > 0 for i in rain_num_list)
        rain_dict['inaccurate_result'] = sum(rain_num_list) < 0
        rain_dict['rain_img_url'] = ''
        if not rain_dict['no_rain']:
            rain_dict['stop_nearest'] = _get_nearest_stop_time(rain_num_list, rain_dict['rain_nearest'])
            rain_dict['rain_img_url'] = rain_map_url[max(rain_num_list)]
        rain_dict['big_rain'] = any(i == 3 for i in rain_num_list)
        if rain_dict['big_rain']:
            rain_dict['big_rain_nearest'] = _get_nearest_rain_time(rain_num_list,threshold=3)

        if rain_dict['no_rain']:
            rain_dict['short_summary_msg'] = u'兩個鐘內無雨'
            rain_dict['long_summary_msg'] = u''
        else: #not rain_dict['no_rain']
            short_summary_list = [u'記得帶遮，',
                                    rain_map_time[rain_dict['rain_nearest']],
                                    u'開始落雨。']
            if rain_dict['big_rain']:
                short_summary_list.insert(0, u'會落大雨!')
                short_summary_list.append([rain_map_time[rain_dict['big_rain_nearest']], u'落到最大。'])
            if rain_dict['stop_nearest'] > 0:
                short_summary_list.append([rain_map_time[rain_dict['stop_nearest']],u'停雨。'])
            rain_dict['short_summary_msg'] = ''.join(short_summary_list)
            rain_dict['long_summary_msg'] = _format_rain_msg(rain_dict['report_time'], 
                                                    rain_dict['short_summary_msg'],
                                                    rain_details_list)
    else:
        rain_dict['hv_result'] = False
    
    return rain_dict
    

def main():
    print(get_current_weather())
    print(get_rain_forcast())


if __name__ == '__main__':
    main()