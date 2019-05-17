'''
Created on Nov 7, 2018

@author: vahidrogo
'''

from contextlib import suppress
import pandas as pd
from tkinter import messagebox as msg

import constants


class ClearviewDetail:
    '''
        Class to read CSV input data downloaded from "Clearview" and
        insert into pandas DataFrame. Various columns are converted 
        during the reading process.
    '''
    
    
    skiprows = [0,1,3]
    
    
    def __init__(self):
        self.converters = {
            constants.NAICS_COLUMN: str,
            constants.PERMIT_COLUMN: lambda x: f'{str(x)[:3]}-{str(x)[3:]}',
            constants.TAC_COLUMN: str,
            constants.SUB_COLUMN: lambda x: int(x) if x else constants.MISSING_SUB_PLACE_HOLDER,
            constants.ZIP_COLUMN: str
            }
    
    
    def get_dataframe(self, path):
        '''
            Returns the dataframe created from reading the csv file,
            if the file has data.
        '''
        with suppress(ValueError):
            df = pd.read_csv(
                path, engine='c', converters=self.converters, 
                skiprows=self.skiprows, encoding='utf-16', low_memory=False
                )
                
        # if there is only one column
        if df is None or len(list(df)) == 1:
            msg.showerror(
                constants.APP_NAME, 
                'There seems to be a problem with the data, '
                f'please make sure that the file at {path} '
                'was able to export successfully.'
                )
            
        else:
            if df.empty:
                msg.showinfo(constants.APP_NAME, f'{path} does not contain any data.')
                
            else:
                return df