'''
Created on Oct 4, 2018

@author: vahidrogo
'''

from contextlib import suppress
import re


class FillNa:
    '''
    '''
    
    
    def __init__(self):
        self._set_quarter_column_patterns()
    
    
    def _set_quarter_column_patterns(self):
        quarter_column_patterns = [
            # pattern to match the quarter like "2nd Quarter 2018"
            r'[1-4](st|nd|rd|th) Quarter \d{4}', 
            
            # pattern for matching quarter columns like 2018Q2 or 2018 Q2
            r'\d{2,4} ?Q[1-4]{1}',
            
            # pattern for matching dates with format "mm/dd/yyy"
            r'1?[0-9]/3[0|1]/\d{4}',
            
            # pattern to match columns with the word "total" in them
            r'.*total.*',
            
            # pattern to match columns like "QTR_2018Q2" and "QTR_20182"
            r'\w{3}_\d{4}Q?\d'
            ]
        
        self.quarter_column_patterns = [
            re.compile(pattern, re.IGNORECASE) 
            for pattern in quarter_column_patterns
            ]
        
    
    def fill_na(self, df):
        self.df = df
        
        for column_name in self.df:
            self._remove_commas(column_name)
            
            if self._is_quarter_column(column_name):
                self._convert_column_to_int(column_name)
            else:
                self._fill_with_blanks(column_name)
        
        
    def _remove_commas(self, column_name):
        # if the column is of type string
        if self.df[column_name].dtype == 'object':
            # in case the value is not a string
            with suppress(ValueError):
                self.df[column_name] = self.df[
                    column_name].str.replace(',', '')
        
        
    def _is_quarter_column(self, column_name):
        '''
            Returns TRUE if the given column name matches the patterns 
            for column headers.
        '''
        return any(
            re.match(pattern, column_name) 
            for pattern in self.quarter_column_patterns)
                        
                        
    def _convert_column_to_int(self, column_name):
        '''
            Converts column c of dataframe df to type integer and fills
            the "NaN" errors with zeroes. In the case that the numbers 
            are formatted, these characters are replace with empty
            strings: (",", ")", "$") and the "(" characters are replaced 
            with "-" to make the number negative when converting to int.
        '''
        try:
            # remove string formatting and fill blanks with zeroes 
            # before converting the column to integer type
            self.df[column_name] = self.df[column_name].str.replace(
                '\$|\)', '').str.replace('\(', '-').fillna(0).astype('int64')
                
        except AttributeError:
            # if the column is already of type integer, only fill in 
            # the blanks with zeroes
            self.df[column_name] = self.df[column_name].fillna(0)
            
            
    def _fill_with_blanks(self, column_name):
        self.df[column_name] = self.df[column_name].fillna('')
            
            
    