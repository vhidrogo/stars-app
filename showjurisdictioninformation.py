'''
Created on Feb 27, 2019

@author: vahidrogo
'''

import tkinter as tk
from tkinter import ttk 

import constants


class ShowJurisdictionInformation(tk.Toplevel):
    '''
        Shows a centered window with a label that contains the information
        for the jurisdiction.
    '''
    
    
    WINDOW_WIDTH = 400
    WINDOW_HEIGHT = 385
    
    
    def __init__(self):
        super().__init__()
        
        self._center_window()
        
        
    def _center_window(self):
        x_offset = (self.winfo_screenwidth() - self.WINDOW_WIDTH) // 2
        y_offset = (self.winfo_screenheight() - self.WINDOW_HEIGHT) // 2
        
        self.geometry(
            f'{self.WINDOW_WIDTH}x{self.WINDOW_HEIGHT}+{x_offset}+{y_offset}'
            )
        
        
    def main(self, jurisdiction):
        lbl = ttk.Label(
            self, justify='left', text=str(jurisdiction).replace(', ', '\n')
            )
        
        lbl.pack(anchor='w', padx=constants.OUT_PAD, pady=constants.OUT_PAD)
        
        btn = ttk.Button(self, text='Done', command=self.destroy)
        btn.pack(anchor='e', padx=constants.OUT_PAD, pady=constants.OUT_PAD)
