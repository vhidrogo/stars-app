'''
Created on Dec 17, 2018

@author: vahidrogo
'''

from contextlib import suppress
import math
import pandas as pd
import sqlite3 as sql
import threading
import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox as msg
from tkinter import ttk

import constants
import progress
import utilities


BUSINESS_CODE_TEXT = 'Business Code'
CURRENT_PERIOD_TEXT = 'Current Period'
OLDEST_PERIOD_TEXT = 'Oldest Period'
TAC_TEXT = 'Tax Area Code'


class Model(threading.Thread):
    '''
    '''
    
    
    # the names and indexes of the input columns
    input_columns = {
        'tac' : 2, 
        'business_code' : 4,
        'first_period' : 5
        }
    
    business_code_column_name = 'BUSINESS_CODE'
    tac_column_name = 'TAX_AREA'
    
    
    def __init__(self, df, col_indexes, period):
        super().__init__()
        
        self.df = df
        self.col_indexes = col_indexes
        self.period = period
        
        self.col_names = list(self.df)
        
        # name of table that will be created
        self.table = ''
        
        # name of business code column
        self.bc_col = constants.BUSINESS_CODE_ID_COLUMN_NAME
         
        # name of tax area code column
        self.tac_col = constants.TAC_COLUMN_NAME
        
        self._set_period_cols()
        
        self.column_names = []
        self.column_string_names = []
        self.table_column_names = []
        
        
    def _set_period_cols(self):
        period_count = (
            self.col_indexes['Current Period'] - self.col_indexes['Oldest Period'] + 1
            )
        
        self.period_cols = utilities.get_period_headers(
            count=period_count, 
            period=self.period, 
            prefix=constants.QUARTER_COLUMN_PREFIX
            )
        

    def run(self):
        self._set_column_names()
        self._reduce_columns()
        self._convert_tac_column()
        self._convert_business_code_column()
        self._group_by_business_code()
        self._insert_id_column()
        self._set_table_name()
        self._create_table()

        
    def _set_column_names(self):
        col_names = list(self.df)
        
        col_names[self.col_indexes['Business Code']] = self.bc_col
        col_names[self.col_indexes['Tax Area Code']] = self.tac_col
        
        col_names[
            self.col_indexes['Oldest Period'] : self.col_indexes['Current Period'] + 1
            ] = self.period_cols
        
        self.df.columns = col_names
        
        
    def _reduce_columns(self):
        '''
            Drops all the unneeded columns.
        '''
        cols = [self.tac_col, self.bc_col] + self.period_cols
        
        for col in list(self.df):
            if col not in cols:
                self.df.drop(col, axis=1, inplace=True)
  

    def _convert_tac_column(self):
        '''
            Converts the tax area code column to string and inserts the 
            leading zero if one is needed.
        '''
        self.df[self.tac_col] = self.df[self.tac_col].apply(
            lambda x: utilities.format_tac(x)
            )
        
        
    def _convert_business_code_column(self):
        '''
            Converts the business code column to integer and fills in the 
            blanks with the default business code.
        '''
        self.df[self.bc_col] = self.df[self.bc_col].apply(
            lambda x: 
                int(x) if not math.isnan(x) and x not in ('', 'NULL') else constants.DEFAULT_BUSINESS_CODE
            )
        

    def _set_table_name(self):
        self.table = constants.BUSINESS_CODE_TOTALS_TABLE
        
        if self._is_addon():
            self.table += constants.ADDON_SUFFIX
        
        
    def _is_addon(self):
        # gets the first tac in the data
        tac = self.df[self.tac_col][0]
        
        is_addon = tac[:2] == constants.ADDON_IDENTIFIER
        
        return is_addon
    
        
    def _group_by_business_code(self):
        '''
            Groups by the business code to consolidate the rows with 
            the default business code that was filled in for the 
            blanks.
        '''
        self.df = self.df.groupby(
            [self.tac_col, self.bc_col], as_index=False, sort=False
            )[self.period_cols].sum()
        
            
    def _insert_id_column(self):
        '''
            Inserts a column at index 0 that will serve as the unique 
            identifier and consists of the tax area code and business 
            code number separated by a dash.
        '''
        id_column = self.df.apply(
            lambda row: f'{row[self.tac_col]}-{row[self.bc_col]}', axis=1
            )
         
        self.df.insert(0, constants.ID_COLUMN_NAME, id_column)
        
       
    def _create_table(self):
        con = sql.connect(constants.DB_PATHS[constants.STATEWIDE_DATASETS_DB])

        with con:
            self.df.to_sql(self.table, con, if_exists='replace', index=False)
        
        con.close()
    
    
class View(tk.Toplevel):
    '''
    '''
    
    
    LABEL_WIDTH = 14
    WINDOW_HEIGHT = 240
    WINDOW_WIDTH = 550
    
    
    def __init__(self, controller, title):
        super().__init__()
        
        self.controller = controller
        
        # sets the window title
        self.title(title)
        
        self.load_btn = None
        
        self.col_index_texts = [
            CURRENT_PERIOD_TEXT,
            OLDEST_PERIOD_TEXT,
            BUSINESS_CODE_TEXT,
            TAC_TEXT,
            ]
        
        self.file_path_var = tk.StringVar()
        self.period_var = tk.StringVar(value=self.controller.selected_period)
        
        self.col_index_vars = {
            text: tk.StringVar() for text in self.col_index_texts
            }
        
        for var in self.col_index_vars.values():
            var.trace('w', self.controller.on_column_index_changed)
        
        self._center_window()
        self._make_widgets()
        
        
    def _center_window(self):
        x_offset = (self.winfo_screenwidth() - self.WINDOW_WIDTH) // 2
        y_offset = (self.winfo_screenheight() - self.WINDOW_HEIGHT) // 2
        
        self.geometry(
            f'{self.WINDOW_WIDTH}x{self.WINDOW_HEIGHT}+{x_offset}+{y_offset}'
            )
    
    
    def _make_widgets(self):
        choose_frm = ttk.Frame(self)
        path_frm = ttk.Frame(choose_frm)
        period_frm = ttk.Frame(self)
        col_indexes_frm = ttk.Labelframe(self, text='Column Indexes (0-indexed integers)')
        button_frm = ttk.Frame(self)
        
        path_lbl = ttk.Label(path_frm, text='File Path:', width=self.LABEL_WIDTH)
        path_ent = ttk.Entry(
            path_frm, state='readonly', textvariable=self.file_path_var
            )
        choose_btn = ttk.Button(
            choose_frm, text='Choose', command=self.controller.on_choose_click
            )
        
        period_lbl = ttk.Label(
            period_frm, text='Current Period:', width=self.LABEL_WIDTH
            )
        
        period_cbo = ttk.Combobox(
            period_frm, justify='right', state='readonly', width=7,
            textvariable=self.period_var, values=self.controller.period_options
            )
        
        period_cbo.bind(
            '<<ComboboxSelected>>', self.controller.on_current_period_selected
            )
        
        self.load_btn = ttk.Button(
            button_frm, text='Load', command=self.controller.on_load_click
            )
        
        cancel_btn = ttk.Button(button_frm, text='Cancel', command=self.destroy)
        
        choose_frm.pack(fill='x', pady=constants.OUT_PAD)
        path_frm.pack(fill='x', expand=1, side='left', padx=constants.OUT_PAD)
        period_frm.pack(anchor='w', padx=constants.OUT_PAD)
        
        col_indexes_frm.pack(
            anchor='w', padx=constants.OUT_PAD, pady=constants.OUT_PAD
            )
        
        button_frm.pack(
            anchor='e', padx=constants.OUT_PAD, pady=constants.OUT_PAD
            )
        
        path_lbl.pack(side='left')
        path_ent.pack(fill='x', expand=1, )
        choose_btn.pack(padx=constants.OUT_PAD)
        period_lbl.pack(side='left')
        period_cbo.pack()
        self.load_btn.pack(side='left', padx=constants.OUT_PAD)
        cancel_btn.pack()
        
        self._make_col_index_widgets(col_indexes_frm)
        
        
    def _make_col_index_widgets(self, frame):
        for text in self.col_index_texts:
            frm = ttk.Frame(frame)
            
            lbl = ttk.Label(frm, text=text + ':', width=self.LABEL_WIDTH)
            ent = ttk.Entry(frm, textvariable=self.col_index_vars[text])
            
            frm.pack()
            lbl.pack(side='left')
            ent.pack(fill='x')
        
        
    def disable_load_button(self):
        self.load_btn.config(state='disabled')
        
        
    def enable_load_button(self):
        self.load_btn.config(state='enabled')
    
    
class Controller:
    '''
    '''
    
    
    title = f'{constants.APP_NAME} - Load Business Code Totals'
    
    business_code_col_name = 'BUSINESS_CODE'
    tac_col_name = 'TAX_AREA'
    
    
    def __init__(self, period_options, selected_period):
        self.period_options = period_options
        self.selected_period = selected_period
        
        self.df = None
        
        self.load_enabled = False
        
        self.file_path = ''
        self.file_type = ''
        
        self.file_columns = []
        
        # dictionary where the keys are file extensions and they're associated
        # values are pandas methods for opening that file type
        self.supported_input_types = {
            'csv' : pd.read_csv, 'xlsx' : pd.read_excel
            }
        
        self.view = View(self, self.title)
        self.view.disable_load_button()
        
        
    def on_choose_click(self):
        self.file_path = filedialog.askopenfilename(parent=self.view)
        
        if self.file_path:
            self.file_type = self.file_path.rsplit('.', 1)[1].lower()
            
            if self._is_supported_file_type():
                self.view.file_path_var.set(self.file_path)
                
                self._set_df()
                
                if self.df is not None:
                    self.file_columns = list(self.df)
                    
                    self._set_current_period_column_index()
                    self._set_oldest_period_column_index()
                    self._set_business_code_column_index()
                    self._set_tac_column_index()
                    
            else:
                msg.showinfo(
                    self.title, 
                    f'Unsupported file type: ({self.file_type}).\n.'
                    'Supported file types are:\n '
                    f'{tuple(self.supported_input_types)}.',
                    parent=self.view
                    )
            
            
    def _is_supported_file_type(self):
        return self.file_type in self.supported_input_types
        
        
    def _set_df(self):
        '''
            Reads the file into a pandas dataframe using the function stored
            for the file type.
        '''
        self.df = self.supported_input_types[self.file_type](self.file_path)
        

    def _set_current_period_column_index(self):
        '''
            Populates the index of the current period input column if one 
            is able to be determined based on the selected year and quarter.
        '''
        period = self.view.period_var.get()
        
        year, quarter = period.split('Q')
        
        for i, name in enumerate(self.file_columns):
            if year + quarter in name:
                self.view.col_index_vars[CURRENT_PERIOD_TEXT].set(i)
                
                
    def _set_oldest_period_column_index(self):
        '''
            Populates the index of the oldest period input column if one 
            is able to be determined based on the first column that has 
            the quarter column prefix.
        '''
        for i, name in enumerate(self.file_columns):
            if constants.QUARTER_COLUMN_PREFIX in name.lower():
                self.view.col_index_vars[OLDEST_PERIOD_TEXT].set(i)
                break
            
            
    def _set_business_code_column_index(self):
        '''
            Populates the index of the business code input column if one 
            is able to be determined based on the index of the stored 
            name.
        '''
        with suppress(ValueError):
            index = self.file_columns.index(self.business_code_col_name)
            self.view.col_index_vars[BUSINESS_CODE_TEXT].set(index)
            
            
    def _set_tac_column_index(self):
        '''
            Populates the index of the tax area code input column if one 
            is able to be determined based on the index of the stored 
            name.
        '''
        with suppress(ValueError):
            index = self.file_columns.index(self.tac_col_name)
            self.view.col_index_vars[TAC_TEXT].set(index)
            
            
    def on_current_period_selected(self, event):
        if self.df is not None:
            self._set_current_period_column_index()
            
            
    def on_column_index_changed(self, *args):
        if self.df is not None:
            if self._valid_input_columns():
                if not self.load_enabled:
                    self.view.enable_load_button()
                    self.load_enabled = True
            else:
                if self.load_enabled:
                    self.view.disable_load_button()
                    self.load_enabled = False
        
        
    def on_load_click(self):
        self.view.destroy()
        
        col_indexes = {
            name: int(var.get()) 
            for name, var in self.view.col_index_vars.items()
            }
        
        model = Model(
            self.df, col_indexes, self.view.period_var.get()
            )
        
        model.start()
        
        msg.showinfo(self.title, 'Finished!')
            
            
    def _valid_input_columns(self):
        col_count = len(self.file_columns)
        
        for var in self.view.col_index_vars.values():
            value = var.get()
            
            if not value.isdigit() or not 0 < int(value) < col_count:
                return False
                
        return True


