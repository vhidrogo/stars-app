'''
Created on Oct 5, 2018

@author: vahidrogo
'''

import ntpath
import pandas as pd
from pathlib import Path
from pyexcelerate import Workbook
from tkinter import messagebox as msg

import constants


class Output:
    '''
        Class to output data to various formats from pandas dataframe
        or nested list.
    '''
    
    
    def output(self, data, path, header, sheet_name='Data'):
        file_type = self._file_type(path)
        
        if file_type == 'csv':
            saved = self._to_csv(data, path, header)
        
        else:
            saved = self._to_excel(data, path, header, sheet_name)
            
        return saved
    
    
    def _file_type(self, path):
        file_name = ntpath.basename(path)
        
        file_type = file_name.rsplit('.', 1)[1]
        
        return file_type
    
    
    def _to_excel(self, data, path, header=[], sheet_name='Data'):
        values = data.values.tolist() if self._is_dataframe(data) else data
                
        sheet_data = [header, ] + values if header else values
        
        wb = Workbook()
        wb.new_sheet(sheet_name, data=sheet_data)
        
        saved = False
        cancel = False
        
        while not saved and not cancel:
            try:
                wb.save(path)
                saved = True
                
            except PermissionError:
                retry = msg.askretrycancel(
                    constants.APP_NAME, 
                    f'Could not save file to ({path}) because there is '
                    'a file with that name currently open. To continue, '
                    'close the file and retry.')
                
                if not retry:
                    cancel = True
                    
        return saved
    
    
    def _to_csv(self, data, path, header):
        path_object = Path(path)
        
        # if the csv file already exists it is deleted
        if path_object.is_file():
            path_object.unlink()
            
        df = data if self._is_dataframe(data) else pd.DataFrame(data)
            
        # creates the csv file
        df.to_csv(
            path, encoding='utf-16', header=header, index=None, 
            sep=',', mode='a'
            )
        
        return True
        
        
    def _is_dataframe(self, data):
        return isinstance(data, pd.DataFrame)