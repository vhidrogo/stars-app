'''
Created on Dec 7, 2018

@author: vahidrogo
'''

import tkinter as tk
from tkinter import ttk


class FrameScroll(ttk.Frame):
    '''
       Make a frame scrollable with scrollbar on the right.
       After adding or removing widgets to the scrollable frame, 
       call the update() method to refresh the scrollable area.
    '''

    def __init__(self, parent, scroll_bar_width=16, window_height=100):
        super().__init__(parent)
        
        self.parent = parent
        self.scroll_bar_width = scroll_bar_width
        self.window_height = window_height

        scrollbar = tk.Scrollbar(self.parent, width=self.scroll_bar_width)
        scrollbar.pack(side='right', fill='y', expand=False)

        self.canvas = tk.Canvas(self.parent, yscrollcommand=scrollbar.set)
        self.canvas.pack(side='left', fill='both', expand=True)

        scrollbar.config(command=self.canvas.yview)

        self.canvas.bind('<Configure>', self._fill_canvas)

        super().__init__(parent)      

        # assign this obj (the inner frame) to the windows item of the canvas
        self.windows_item = self.canvas.create_window(
            0,0, window=self, anchor='nw'
            )


    def _fill_canvas(self, event):
        'Enlarge the windows item to the canvas width'
        self.canvas.itemconfig(self.windows_item, width=event.width)
        

    def update(self):
        'Update the canvas and the scrollregion'

        self.update_idletasks()
        self.canvas.config(scrollregion=self.canvas.bbox(self.windows_item))
