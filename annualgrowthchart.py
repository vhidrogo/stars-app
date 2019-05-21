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

DATA_NAMES = ['jurisdiction', 'region']


class AnnualizedGrowthChart:
    '''
        Outputs the "Annualized Growth by Economic Category" Excel chart.
    '''
    
    
    def __init__(self, controller, selections):
        self.controller = controller
        self.selections = selections
        
        self.output_path = ''
        
        self.output_saved = False
        
        self.period_headers = []
        
        self.year_periods = []
        self.year_strings = []
        
        self.queries = {name: '' for name in DATA_NAMES}
        self.args = {name: () for name in DATA_NAMES}
        self.dfs = {name: None for name in DATA_NAMES}
        
        
    def main(self, jurisdiction):
        if self.selections.years >= MIN_YEARS:
            self.jurisdiction = jurisdiction
            
            self._set_year_periods()
            self._set_period_headers()
            self._set_year_strings()
            
            self._set_queries()
            self._set_args()
            self._set_dfs()
            for name, df in self.dfs.items():
                print(name)
                print(df)
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
        
    def _set_queries(self):
        self.queries['jurisdiction'] = f'''
            SELECT c.Name,{self.year_strings[0]},{self.year_strings[-1]}
            
            FROM {constants.CATEGORY_TOTALS_TABLE} t,
                {constants.CATEGORIES_TABLE} c
             
            WHERE {constants.TAC_COLUMN_NAME}=?
                AND {constants.CATEGORY_ID_COLUMN_NAME}=c.Id
            
            ORDER BY {constants.CATEGORY_ID_COLUMN_NAME}
            '''
        
        self.queries['region'] = f'''
            SELECT c.Name,{self.year_strings[0]},{self.year_strings[-1]}
            
            FROM {constants.CATEGORY_TOTALS_TABLE}{constants.REGION_SUFFIX} t,
                {constants.CATEGORIES_TABLE} c
             
            WHERE {constants.REGION_ID_COLUMN_NAME}=?
                AND {constants.CATEGORY_ID_COLUMN_NAME}=c.Id
            
            ORDER BY {constants.CATEGORY_ID_COLUMN_NAME}
            '''
        
    def _set_args(self):
        self.args['jurisdiction'] = (self.jurisdiction.tac, )
        self.args['region'] = (self.jurisdiction.region_id, )
        
        
    def _set_dfs(self):
        for name in DATA_NAMES:
            data = utilities.execute_sql(
                sql_code=self.queries[name],
                args=self.args[name],
                db_name=constants.STATEWIDE_DATASETS_DB,
                fetchall=True,
                attach_db=constants.STARS_DB
                )
            
            self.dfs[name] = pd.DataFrame(
                data, columns=['Category'] + self.period_headers
                )
        
        
    def _set_output_path(self):
        name = (
            f'{self.jurisdiction.id} {self.selections.period} {OUTPUT_NAME}'
            )
        
        self.output_path = f'{self.jurisdiction.folder}{name}.{OUTPUT_TYPE}'
        
        
    def _output(self):
        pass