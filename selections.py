'''
Created on May 22, 2018

@author: vahidrogo
'''

from pathlib import Path

import constants
from jurisdiction import Jurisdiction
import utilities


class Selections:
    '''
        Holds the user selections from the main window. An instance of
        this class will be created each time the user clicks the "Run"
        button to allow the user to run other processes with different 
        selections and make each run independent of each other.
    '''
    
    
    def __init__(self, main):
        self.main = main 
        
        self.period = self.main.get_period()
        
        self.quarter = int(self.period[-1])
        self.year = int(self.period[:4])
        
        self.basis = self.main.get_basis()
        self.period_count = self.main.get_count()
        
        self.ascending = self.main.get_ascending()
        self.exclude_files = self.main.get_exclude_files_state()
        self.include_estimates = self.main.get_estimates_state()
        self.interval = self.main.get_interval()
        self.is_fifo = self.main.get_is_fifo_state()
        self.include_geos = self.main.get_geos_state()
        self.open_output = self.main.get_open_state()
        self.order = self.main.get_order()
        self.output_type = self.main.get_output_type().lower()
        self.pdf_only = self.main.get_pdf_only_state()
        self.process_name = self.main.get_process_name()
        self.type_option = self.main.get_type_option()
        
        self.title = f'{constants.APP_NAME} - {self.process_name}'
        
        self._set_jurisdiction_list()
        
        self.jurisdiction_count = len(self.jurisdiction_list)
        
        self._set_jurisdiction_folders()
        
        
    def _set_jurisdiction_list(self):
        jurisdiction_list = self.main.get_queue_list()
        
        if self.is_fifo:
            jurisdiction_list = jurisdiction_list[::-1]
        
        self.jurisdiction_list = [
            Jurisdiction(jurisdiction_id=jurisdiction_id) 
            for jurisdiction_id in jurisdiction_list
            ]
        
        
    def _set_jurisdiction_folders(self):
        for jurisdiction in self.jurisdiction_list:
            folder = jurisdiction.folder
            
            folder = utilities.get_current_path(
                folder, quarter=self.quarter, year=self.year
                )
            
            path_object = Path(folder)
             
            if not path_object.exists():
                path_object.mkdir(parents=True)
                
            jurisdiction.folder = folder
    
    