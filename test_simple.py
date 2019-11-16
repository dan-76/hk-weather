# # Filename: test_simple.py
# coding=utf-8

# Standard library imports
import unittest 

# Third-party imports

# Application-specific imports
from hkweather import weatherchecker as checker

class checkerTests(unittest.TestCase): 
    def test_search_result_or_empty(self):
        test_string = 'Air temperature is 100C degrees Celsius'
        good_pattern = r'Air temperature.* (\d+).*degrees Celsius'
        bad_pattern = r'abc'

        self.assertEqual(checker._search_result_or_empty(good_pattern, test_string), '100') 
        self.assertEqual(checker._search_result_or_empty(bad_pattern, test_string), '')
 
 
if __name__ == "__main__": 
    unittest.main()