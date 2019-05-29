'''
Created on Feb 13, 2019

@author: vahidrogo
'''

import unittest

import utilities


class StarsAppTests(unittest.TestCase):
    '''
        Tests for functions throughout StarsApp.
    '''
    
    def test_user_exists(self):
        # is the user successfully found?
        self.assertTrue(utilities.user_exists('vahidrogo'))
        
        
    def test_user_does_not_exist(self):
        # is the user successfully not found?
        self.assertFalse(utilities.user_exists('not_a_user'))
        
        
    def test_format_permit_number_eight_digits(self):
        # is the leading zero and dash put in?
        self.assertEqual(
            utilities.format_permit_number('12345678'), '012-345678'
            )
    
    
    def test_format_permit_number_nine_digits(self):
        # is the dash put in?
        self.assertEqual(
            utilities.format_permit_number('123456789'), '123-456789'
            )
        
        
    def test_next_older_period_quarter_one(self):
        # is the next older period returned when the quarter is 1?
        self.assertEqual(
            utilities.next_period((2019, 1), newer=False), (2018, 4)
            )
        
        
    def test_next_older_period(self):
        # is the next older period returned?
        self.assertEqual(
            utilities.next_period((2019, 2), newer=False), (2019, 1)
            )
        
    
    def test_next_newer_period_quarter_four(self):
        # is the next newer period returned when the quarter is 1?
        self.assertEqual(
            utilities.next_period((2018, 4), newer=True), (2019, 1)
            )
        
        
    def test_next_newer_period(self):
        # is the next newer period returned?
        self.assertEqual(
            utilities.next_period((2019, 1), newer=True), (2019, 2)
            )


if __name__ == '__main__':
    unittest.main()