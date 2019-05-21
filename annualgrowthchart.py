'''
Created on May 21, 2019

@author: vahidrogo
'''

from tkinter import messagebox as msg
import xlsxwriter

import constants
import utilities

OUTPUT_NAME = 'Annualized Growth by Economic Category'
OUTPUT_TYPE = 'xlsx'

MIN_YEARS = 2


class AnnualizedGrowthChart:
    '''
        Outputs the "Annualized Growth by Economic Category" Excel chart.
    '''
    
    
    def __init__(self, controller, selections):
        self.controller = controller
        self.selections = selections
        
        self.jurisdiction_query = ''
        self.region_query = ''
        self.output_path = ''
        
        self.output_saved = False
        
        self.year_strings = []
        
        
    def main(self, jurisdiction):
        if self.selections.years >= MIN_YEARS:
            self.jurisdiction = jurisdiction
            
            self._set_year_strings()
            self._set_jurisdiction_query()
            self._set_region_query()
            print('jurisdiction_query', self.jurisdiction_query)
            self._set_output_path()
            self._output()
            print('region query', self.region_query)
            if self.output_saved and self.selections.open_output:
                utilities.open_file(self.output_path)
                
        else:
            msg.showinfo(
                self.selections.title, 
                f'A minimum of ({MIN_YEARS}) are required to calculate growth.'
                )
            
            
    def _set_year_strings(self):
        period_count = (self.selections.years * 4)
        
        period_headers = utilities.get_period_headers(
            count=period_count,
            selections=self.selections,
            prefix=constants.QUARTER_COLUMN_PREFIX
            )
        
        # tuple with list of periods making up oldest and newest years
        year_periods = (period_headers[:4], period_headers[-4:])
        
        self.year_strings = [
            '+'.join([f'SUM({period})' for period in periods])
            for periods in year_periods
            ]
            
            
    def _set_jurisdiction_query(self):
        self.jurisdiction_query = f'''
            SELECT {constants.CATEGORY_ID_COLUMN_NAME},
                {self.year_strings[0]},{self.year_strings[-1]}
            
            FROM {constants.CATEGORY_TOTALS_TABLE}
             
            WHERE {constants.TAC_COLUMN_NAME}={self.jurisdiction.tac}
            
            ORDER BY {constants.CATEGORY_ID_COLUMN_NAME}
            '''
        
        
    def _set_region_query(self):
        self.region_query = f'''
            SELECT {constants.CATEGORY_ID_COLUMN_NAME},
                {self.year_strings[0]},{self.year_strings[-1]}
            
            FROM {constants.CATEGORY_TOTALS_TABLE}{constants.REGION_SUFFIX}
             
            WHERE {constants.REGION_ID_COLUMN_NAME}={self.jurisdiction.region_id}
            
            ORDER BY {constants.CATEGORY_ID_COLUMN_NAME}
            '''
        
        
    def _set_output_path(self):
        name = (
            f'{self.jurisdiction.id} {self.selections.period} {OUTPUT_NAME}'
            )
        
        self.output_path = f'{self.jurisdiction.folder}{name}.{OUTPUT_TYPE}'
        
        
    def _output(self):
        pass