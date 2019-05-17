'''
Created on Jan 10, 2019

@author: vahidrogo
'''

import tkinter as tk
from tkinter import ttk

import time


class EntryPrompt(tk.Toplevel):
    '''
        ttk Entry that waits for the user to enter a value.
    '''
    
    
    WIDGET_PAD = 10
    
    WINDOW_HEIGHT = 100
    WINDOW_WIDTH = 500
    
    
    def __init__(self, title, prompt, parent=None):
        super().__init__()
        
        self.title(title)
        
        self.prompt = prompt
        self.parent = parent
        
        self.waiting_for_prompt = True
        
        self.value = tk.StringVar()
        
        self._set_geometry()
        self._make_widgets()
        
        while self.waiting_for_prompt:
            time.sleep(.5)
            
        self.destroy()
        
        self = self.value.get()
        
        return self
        
    def _set_geometry(self):
        x_offset = (self.winfo_screenwidth() - self.WINDOW_WIDTH) // 2
        y_offset = (self.winfo_screenheight() - self.WINDOW_HEIGHT) // 2
        
        self.geometry(
            f'{self.WINDOW_WIDTH}x{self.WINDOW_HEIGHT}+{x_offset}+{y_offset}'
            )
        
        
    def _make_widgets(self):
        prompt_frm = ttk.Frame(self)
        prompt_lbl = ttk.Label(prompt_frm, text=self.prompt)
        entry = ttk.Entry(prompt_frm, textvariable=self.value)
        
        button_frm = ttk.Frame(self)
        ok_btn = ttk.Button(button_frm, text='Ok', command=self._on_ok_click)
        cancel_btn = ttk.Button(
            button_frm, text='Cancel', command=self._on_cancel_click
            )
        
        prompt_frm.pack(fill='x', padx=self.WIDGET_PAD, pady=self.WIDGET_PAD)
        prompt_lbl.pack(anchor='w')
        entry.pack(fill='x')
        
        button_frm.pack(anchor='e', padx=self.WIDGET_PAD, pady=self.WIDGET_PAD)
        ok_btn.pack(side='left', padx=self.WIDGET_PAD)
        cancel_btn.pack()
        
        
    def _on_ok_click(self):
        self.waiting_for_prompt = False
        
        
    def _on_cancel_click(self):
        self.value.set('')
        
        self.waiting_for_prompt = False