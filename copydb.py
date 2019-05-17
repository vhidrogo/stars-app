'''
Created on Dec 5, 2018

@author: vahidrogo
'''

import ntpath
import sqlite3 as sql
import threading

import constants
from progress import Progress


class CopyDb(threading.Thread):
    '''
    '''
    
    
    def __init__(self, source, target, progress_title):
        super().__init__()
        
        self.source = source
        self.target = target
        self.progress_title = progress_title
        
        self.title = f'{constants.APP_NAME} - {self.progress_title} Progress'
        
        self.db_name = ntpath.basename(self.source)
        
    
    def run(self):
        self.Progress = Progress(self, self.title, abort=False)
        
        con = sql.connect(self.source)
        
        with sql.connect(self.target) as bck:
            con.backup(bck, pages=1, progress=self._update_progress)
              
        con.close()
        
        self.Progress.destroy()
    
    
    def _update_progress(self, status, remaining, total):
        progress = (total - remaining) / total * 100
        
        message = 'Copied {:,} of {:,} pages from {}'.format(
            total - remaining, total, self.db_name
            )
        
        self.Progress.update_progress(progress, message)
