# # Filename: test_simple.py
# coding=utf-8

# Standard library imports
import os
import datetime
import unittest 
from unittest.mock import patch

# Third-party imports
import dateutil.parser
from dateutil.tz import tzutc

# Application-specific imports
from hkweather import weatherchecker as checker

def join_file_link(file_link):
    THIS_DIR = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(THIS_DIR, file_link)
    return 'file://' + file_path

class checkerTests(unittest.TestCase): 
    def setUp(self):
        self.test_page_file_link = {
            "en": "tests/data/CurrentWeather.xml",
            "uc": "tests/data/CurrentWeather_uc.xml",
            "td": "tests/data/LocalWeatherForecast_uc.xml",
            "9d": "tests/data/SeveralDaysWeatherForecast_uc.xml"
        }
        
        self.test_pages = {k: join_file_link(v) for k, v in self.test_page_file_link.items()}

    def test_search_result_or_empty(self):
        test_string = 'Air temperature is 100C degrees Celsius'
        good_pattern = r'Air temperature.* (\d+).*degrees Celsius'
        bad_pattern = r'abc'

        self.assertEqual(checker._search_result_or_empty(good_pattern, test_string), '100') 
        self.assertEqual(checker._search_result_or_empty(bad_pattern, test_string), '')

    def test_get_soup_from_url(self):
        for link in self.test_pages.values():
            self.assertIsNotNone(checker._get_soup_from_url(link).title)

    def test_get_soup_for_cdata(self):
        self.assertIn('http://rss.weather.gov.hk/img/pic50.png', 
            checker._get_soup_for_cdata(checker._get_soup_from_url(self.test_pages["en"])).find('img')['src'])
        self.assertIn(u'天 文 台 錄 得', 
            checker._get_soup_for_cdata(checker._get_soup_from_url(self.test_pages["uc"])).get_text())
        self.assertIn(u'天 氣 概 況', 
            checker._get_soup_for_cdata(checker._get_soup_from_url(self.test_pages["9d"])).get_text())
        self.assertIn(u'天氣預測', 
            checker._get_soup_for_cdata(checker._get_soup_from_url(self.test_pages["td"])).get_text())

    def test_format_strip_all_whitespace(self):
        test_string = u'過 去 一 小 時 ， 京 士 柏 錄 得 的 平 均 紫 外 線 指 數 ： 0.0紫 外 線 強 度 ： 低'
        expected_string = u'過去一小時，京士柏錄得的平均紫外線指數：0.0紫外線強度：低'
        self.assertEqual(checker._format_strip_all_whitespace(test_string), expected_string)

    def test_format_weather_msg(self):
        expected_string = u'\n氣溫: 100 度\n相對濕度: 百分之 75\n曝曬級數: low\n紫外線指數: 0.0\ntesting warning\ntesting prediction\ntesting days description\n本日預測: testing summary\n報告時間: 2019-11-17 18:02:00\n'
        self.assertEqual(checker._format_weather_msg(dateutil.parser.parse("Sun, 17 Nov 2019 10:02:00 GMT"),'100','75','0.0','low','testing warning','testing prediction','testing days description','testing summary'),
                            expected_string)
    
    def test_get_current_weather(self):
        expected_dict = {'author': 'hkowm@hko.gov.hk', 'publication_date_text': 'Sun, 17 Nov 2019 09:02:00 GMT', 'publication_date': datetime.datetime(2019, 11, 17, 9, 2, tzinfo=tzutc()), 'weather_img_url': 'http://rss.weather.gov.hk/img/pic50.png', 'weather_img_number': '50', 'temperature': '25', 'relative_humidity': '74', 'uv_index': '0', 'uv_level': 'low', 'rainfall_exist': '', 'prediction': '', 'warning': '', 'days_description': '天氣概況：預料一道冷鋒在華中形成，並於明晚橫過華南沿岸。與其相關的強烈東北季候風會在未來兩三日為華南帶來清涼的天氣。而季候風將在本週中後期緩和，廣東沿岸氣溫逐漸回升。此外，熱帶氣旋海鷗會在未來兩三日移向呂宋一帶並橫過南海中部。', 'short_summary_msg': '大致天晴。早上最低氣溫約22度，日間乾燥，最高氣溫約28度。明晚顯著轉涼，氣溫下降至約19度。吹微風，明日轉吹和緩北風，稍後風勢逐漸增強。', 'long_summary_msg': '\n氣溫: 25 度\n相對濕度: 百分之 74\n曝曬級數: low\n紫外線指數: 0\n天氣概況：預料一道冷鋒在華中形成，並於明晚橫過華南沿岸。與其相關的強烈東北季候風會在未來兩三日為華南帶來清涼的天氣。而季候風將在本週中後期緩和，廣東沿岸氣溫逐漸回升。此外，熱帶氣旋海鷗會在未來兩三日移向呂宋一帶並橫過南海中部。\n本日預測: 大致天晴。早上最低氣溫約22度，日間乾燥，最高氣溫約28度。明晚顯著轉涼，氣溫下降至約19度。吹微風，明日轉吹和緩北風，稍後風勢逐漸增強。\n報告時間: 2019-11-17 17:02:00\n'}
        with patch.dict(checker.current_weather_url, self.test_pages, clear=True):
            self.assertEqual(checker.get_current_weather(), expected_dict)

if __name__ == "__main__": 
    unittest.main()