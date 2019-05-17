'''
Created on Sep 20, 2018

@author: vahidrogo
'''

import pandas as pd
from pyexcelerate import Workbook
import threading
import tkinter as tk
from tkinter import filedialog 
from tkinter import messagebox as msg
from tkinter import ttk

from addressparser import AddressParser
import constants
import progress

'''
    TODO check that the column is in the file
'''


class Controller:
    '''
    '''
    
    
    def __init__(self):
        self.title = 'StarsApp - Parse Addresses'
        
        self.output_file_suffix = '(parsed_address)'
        
        self.address_column_identifier = 'address'
        
        self.file_df = None
        
        self.parse_enabled = False
        
        self.gui = View(self)
        self.gui.disable_parse_button()
        
        self.address_parser = AddressParser()
        
        
    def set_file(self, path):
        extension = path.rsplit('.', 1)[1]
        
        '''
            TODO add support for csv and other file types
        '''
        
        if extension in ['xlsx', 'xls']:
            try:
                self.file_df = pd.read_excel(path)
                self.file_df = self.file_df.fillna('')
                
            except Exception as e:
                print('let the user that the file did not load')
                # also check which exceptions will happen here to use
                # that instead of the generic one
                
        else:
            msg.showerror(
                self.title, f'File type {extension} is currently not supported.'
                )
        
        
    def get_output_path(self, input_path):
        parts = input_path.rsplit('.', 1)
        
        output_path = f'{parts[0]} {self.output_file_suffix}.{parts[1]}'
        
        return output_path
    
    
    def get_found_address_column(self):
        column_names = list(self.file_df)
        
        for i, name in enumerate(column_names):
            if self.address_column_identifier in name.lower():
                return i
        
    '''
        TODO check for the items in the widgets like the output path
        and the address column before doing anything else
        
        also if the file is open or already exists handle that 
    '''
    def _on_parse_click(self):
        address_column = self.gui.address_column.get()
        
        thread = threading.Thread(
            target=self._parse, args=(address_column,)
            )
        
        thread.daemon = True
        thread.start()
            

    def _parse(self, address_column):
        loading_circle = progress.LoadingCircle(self.gui, text='Parsing')
        loading_circle.start()
        
        self.address_parser.set_address_column(address_column)
            
        self.address_parser.parse_addresses(self.file_df)
        
        self._write_output_file()
        
        loading_circle.end()
        
        self.gui.destroy()
    
    
    def _write_output_file(self):
        column_names = list(self.file_df)
        
        data = [column_names, ] + self.file_df.values.tolist()
        
        wb = Workbook()
        wb.new_sheet('parsed addresses', data=data)
        
        output_path = self.gui.output_file.get()
        wb.save(output_path)
        
        
    def on_address_column_change(self, *args):
        address_column = self.gui.address_column.get()
        
        if address_column and address_column.isdigit():
            self.gui.enable_parse_button()
            
            self.parse_enabled = True
            
        else:
            self.gui.disable_parse_button()
            
            self.parse_enabled = False
        
        
class View(tk.Toplevel):
    '''
    '''
    
    
    DEFAULT_ADDRESS_COLUMN = 0
    ENTRY_WIDTH = 60
    LABEL_WIDTH = 15
    WINDOW_HEIGHT = 100
    WINDOW_WIDTH = 450
    
    
    def __init__(self, controller):
        super().__init__()
        
        self.controller = controller
        
        self.input_file = tk.StringVar()
        self.output_file = tk.StringVar()
        
        self.address_column = tk.StringVar(self.DEFAULT_ADDRESS_COLUMN)
        self.address_column.trace('w', self.controller.on_address_column_change)
        
        self._window_setup()
        
        self._make_widgets()
        
        
    def _window_setup(self):
        x_offset = (self.winfo_screenwidth() - self.WINDOW_WIDTH) // 2
        y_offset = (self.winfo_screenheight() - self.WINDOW_HEIGHT) // 2
        
        # centers the window
        self.geometry(f'+{x_offset}+{y_offset}')
        
        
    def _make_widgets(self):
        frm = ttk.Frame(self)
        frm.pack(fill='x', padx=constants.OUT_PAD, pady=constants.OUT_PAD)
        
        lbl = ttk.Label(frm, text='Input File:', width=self.LABEL_WIDTH)
        lbl.pack(side='left')
        
        ent = ttk.Entry(
            frm, textvariable=self.input_file, state='readonly',
            width=self.ENTRY_WIDTH
            )
        
        ent.pack(fill='x')
        
        frm = ttk.Frame(self)
        frm.pack(fill='x', padx=constants.OUT_PAD)
        
        col_frm = ttk.Frame(frm)
        col_frm.pack(side='left')
        
        lbl = ttk.Label(col_frm, text='Address Column:')
        lbl.pack(side='left')
        
        ent = ttk.Entry(
            col_frm, textvariable=self.address_column, justify='right',
            width=5)
        
        ent.pack()
        
        btn = ttk.Button(
            frm, text='Choose', command=self._on_choose_click)
        btn.pack(anchor='e', padx=constants.OUT_PAD)
        
        frm = ttk.Frame(self)
        frm.pack(fill='x', padx=constants.OUT_PAD, pady=constants.OUT_PAD)
        
        lbl = ttk.Label(frm, text='Output File:', width=self.LABEL_WIDTH)
        lbl.pack(side='left')
        
        ent = ttk.Entry(
            frm, textvariable=self.output_file, width=self.ENTRY_WIDTH)
        
        ent.pack(fill='x')
        
        frm = ttk.Frame(self)
        frm.pack(anchor='e', padx=constants.OUT_PAD, pady=constants.OUT_PAD)
        
        self.parse_btn = ttk.Button(
            frm, text='Parse', command=self.controller._on_parse_click)
        self.parse_btn.pack(side='left', padx=constants.OUT_PAD)
        
        btn = ttk.Button(
            frm, text='Cancel', command=self.destroy)
        btn.pack()
        
        
    def _on_choose_click(self):
        input_path = filedialog.askopenfilename(parent=self)
        
        if input_path:
            self.input_file.set(input_path)
            
            self.controller.set_file(input_path)
            
            output_path = self.controller.get_output_path(input_path)
            self.output_file.set(output_path)
            
            address_column = self.controller.get_found_address_column()
            if address_column:
                self.address_column.set(address_column)
                
                
    def disable_parse_button(self):
        self.parse_btn.config(state='disabled')
        
        
    def enable_parse_button(self):
        self.parse_btn.config(state='enabled')
        