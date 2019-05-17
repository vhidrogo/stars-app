'''
Created on Jul 20, 2018

@author: vahidrogo
'''

from copy import deepcopy
import threading
from tkinter import messagebox as msg
import traceback

from loaddetail import LoadDetail
from progress import Progress


class DataController(threading.Thread):
    '''
    '''
    
    
    def __init__(self, process):
        super().__init__()
        
        self.process = process
        
        self.main = self.process.main
        self.selections = self.process.selections
        
        self.files = deepcopy(self.process.get_files())
        self.file_count = len(self.files)
        
        self.counter = 0
        
        self.progress = Progress(self, self.process.title)
        
        self.abort = False
        self.con = None
        
        
    def run(self):
        try:
            self._process_files()
            
        except Exception:
            msg.showerror(
                self.process.title, 
                f'Unhandled exception occurred:\n\n{traceback.format_exc()}',
                parent=self.process.gui)
            
        finally:
            self.progress.destroy()
                    
                    
    def _process_files(self):
        for i, item in enumerate(self.files.items(), start=1):
            if self.main.end_processes or self.abort:
                break
            
            self.counter = i
            
            name, data = item
            
            jurisidiction, df = data
            
            load_detail = LoadDetail(self, df, name)
               
            load_detail.load(jurisidiction)
            
        
    def update_progress(self, progress, message):
        self.progress.update_progress(
            progress, message, self.counter, self.file_count
            )
                
                
        
