'''
Created on May 21, 2019

@author: vahidrogo
'''

import pandas as pd
from tkinter import messagebox as msg
import xlsxwriter

import constants
import utilities
from numpy.distutils.fcompiler import none

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
        
        self.period_headers = []
        
        self.jurisdiction_data = None
        self.region_data = None
        
        self.year_periods = []
        self.year_strings = []
        
        
    def main(self, jurisdiction):
        if self.selections.years >= MIN_YEARS:
            self.jurisdiction = jurisdiction
            
            self._set_year_periods()
            self._set_period_headers()
            self._set_year_strings()
            
            self._set_jurisdiction_query()
            self._set_region_query()
            
            self._set_jurisdiction_data()
            self._set_region_data()
            
            self._set_output_path()
            self._output()
            
            if self.output_saved and self.selections.open_output:
                utilities.open_file(self.output_path)
                
        else:
            msg.showinfo(
                self.selections.title, 
                f'A minimum of ({MIN_YEARS}) are required to calculate growth.'
                )
            
            
    def _set_year_periods(self):
        period_count = (self.selections.years * 4)
        
        period_headers = utilities.get_period_headers(
            count=period_count,
            selections=self.selections,
            prefix=constants.QUARTER_COLUMN_PREFIX
            )
        
        # tuple with list of periods making up oldest and newest years
        self.year_periods = (period_headers[:4], period_headers[-4:])
            
            
    def _set_year_strings(self):
        self.year_strings = [
            '+'.join(periods) for periods in self.year_periods
            ]
        
        
    def _set_period_headers(self):
        period_headers = [x[-1] for x in self.year_periods]
        self.period_headers = [
            x.replace(
                constants.QUARTER_COLUMN_PREFIX, 
                constants.YEAR_COLUMN_PREFIX.upper()
                )
            for x in period_headers
            ]
            
            
    def _set_jurisdiction_query(self):
        self.jurisdiction_query = f'''
            SELECT c.Name,{self.year_strings[0]},{self.year_strings[-1]}
            
            FROM {constants.CATEGORY_TOTALS_TABLE} t,
                {constants.CATEGORIES_TABLE} c
             
            WHERE {constants.TAC_COLUMN_NAME}=?
                AND {constants.CATEGORY_ID_COLUMN_NAME}=c.Id
            
            ORDER BY {constants.CATEGORY_ID_COLUMN_NAME}
            '''
        
        
    def _set_region_query(self):
        self.region_query = f'''
            SELECT c.Name,{self.year_strings[0]},{self.year_strings[-1]}
            
            FROM {constants.CATEGORY_TOTALS_TABLE}{constants.REGION_SUFFIX} t,
                {constants.CATEGORIES_TABLE} c
             
            WHERE {constants.REGION_ID_COLUMN_NAME}=?
                AND {constants.CATEGORY_ID_COLUMN_NAME}=c.Id
            
            ORDER BY {constants.CATEGORY_ID_COLUMN_NAME}
            '''
        
        
    def _set_jurisdiction_data(self):
        jurisdiction_data = utilities.execute_sql(
            sql_code=self.jurisdiction_query,
            args=(self.jurisdiction.tac, ),
            db_name=constants.STATEWIDE_DATASETS_DB,
            fetchall=True,
            attach_db=constants.STARS_DB
            )
        
        self.jurisdiction_data = pd.DataFrame(
            jurisdiction_data, columns=['Category'] + self.period_headers
            )
        
        
    def _set_region_data(self):
        region_data = utilities.execute_sql(
            sql_code=self.region_query,
            args=(self.jurisdiction.region_id, ),
            db_name=constants.STATEWIDE_DATASETS_DB,
            fetchall=True,
            attach_db=constants.STARS_DB
            )
        
        self.region_data = pd.DataFrame(
            region_data, columns=['Category'] + self.period_headers
            )
        
        
    def _set_output_path(self):
        name = (
            f'{self.jurisdiction.id} {self.selections.period} {OUTPUT_NAME}'
            )
        
        self.output_path = f'{self.jurisdiction.folder}{name}.{OUTPUT_TYPE}'
        
        
    def _output(self):
        pass