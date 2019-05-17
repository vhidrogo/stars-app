'''
Created on Dec 17, 2018

@author: vahidrogo
'''

import pandas as pd
import sqlite3 as sql
import threading
import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox as msg
from tkinter import ttk

import constants
from progress import Progress
import utilities


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
    
    
    def __init__(self, file_path, period, title):
        super().__init__()
        
        self.file_path = file_path
        self.period = period
        self.title = title
        
        self.file_type = self.file_path.rsplit('.', 1)[1]
        self.year, self.quarter = self.period.split('Q')
        
        self.last_period_index = 0
        self.period_count = 0
        
        self.df = None
        
        self.abort = False
        
        self.column_names = []
        self.column_string_names = []
        self.table_column_names = []
        
        # converts the tac to a string and inserts the leading zero if 
        # it is missing it, it is missing it if it only has four digits
        # converts the business code to an int and fills in the default 
        # business code if it is NULL
        self.converters = {
            self.input_columns[
                'tac'] : lambda x: '0' + str(x) if len(str(x)) == 4 else str(x),
            
            self.input_columns[
                'business_code'] : lambda x: int(x) if x not in ('', 'NULL') else constants.DEFAULT_BUSINESS_CODE
            }
        
        # dictionary with input type as tkey and pandas function that read the 
        # file type as value
        self.supported_input_types = {
            'csv' : pd.read_csv, 'xlsx' : pd.read_excel
            }
        

    def run(self):
        self.progress = Progress(self, self.title, abort=False)
        
        if self._supported_input_type():
            self.progress.update_progress(0, f'Reading {self.file_path}.')
            
            # reads file into pandas dataframe
            self._set_df()
            #self.df.to_csv('business_code_totals_initial_load.csv', index=False)
            if self.df is not None:
                self._set_table_name()
                 
                self.column_names = list(self.df)
                #print('column names:', self.column_names)
                '''
                    TODO
                     
                    Alert the user if the index entered is greater than the 
                    number of columns
                '''
                self._set_last_period_index()
                self._set_period_count()
                #print('last period index:', self.last_period_index)
                #print('period count:', self.period_count)
                self.progress.update_progress(20, 'Processing data.')
                 
                self._drop_unneeded_columns()
                self.column_names = list(self.df)
                #print('column names after dropped unneeded:', self.column_names)
                utilities.FillNa.fill_na(self.df)
                 
                #self._fill_business_code_blanks()
                    
                self._group_by_business_code()
                #self.df.to_csv('business_code_totals_after_group_by_bc.csv', index=False)
                self._set_table_column_names()
                
                # sets the column names in the dataframe to the columns that 
                # will be in the table 
                self.df.columns = self.table_column_names
                 
                #self._convert_business_code_column_to_int()
                 
                self.progress.update_progress(25, 'Inserting id column.')
                
                self._insert_id_column()
                #self.df.to_csv('business_code_totals_after_id_column.csv', index=False)
                self.progress.update_progress(85, 'Creating table.')
                 
                self._create_table()
                 
                self.progress.update_progress(100, 'Finished.')
                
        self.progress.destroy()
        
        
    def _supported_input_type(self):
        supported = False
        
        if self.file_type in self.supported_input_types:
            supported = True
            
        else:
            msg.showinfo(
                self.title, 'Input file type must be one of:\n\n'
                f'{list(self.supported_input_types.keys())}.'
                )
        
        return supported
        
        
    def _set_df(self):
        '''
            Reads the file into a pandas dataframe using the function stored
            for the file type.
        '''
        self.df = self.supported_input_types[self.file_type](
            self.file_path, converters=self.converters
            )
        
        
    def _set_table_name(self):
        self.table_name = constants.BUSINESS_CODE_TOTALS_TABLE
        
        if self._is_addon():
            self.table_name += constants.ADDON_SUFFIX
        
        
    def _is_addon(self):
        # gets the first tac in the data
        tac = self.df.iloc[:, self.input_columns['tac']][0]
        
        is_addon = tac[:2] == constants.ADDON_IDENTIFIER
        
        return is_addon
    
    
    def _set_last_period_index(self):
        column_name = f'{constants.QUARTER_COLUMN_PREFIX}{self.year}{self.quarter}'.upper()
        
        if column_name in self.column_names:
            self.last_period_index = self.column_names.index(column_name)
            
            
    def _set_period_count(self):
        self.period_count = self.last_period_index - self.input_columns['first_period'] + 1
        

    def _drop_unneeded_columns(self):
        '''
            Drops the column from the pandas dataframe that are not needed.
        '''
        drop_columns = self._get_drop_column_names()
        
        for column in drop_columns:
            self.df.drop(column, axis=1, inplace=True)
        
        
    def _get_drop_column_names(self):
        drop_columns = []
        
        for i, name in enumerate(self.column_names):
            if (
                i != self.input_columns['tac'] and i != self.input_columns['business_code'] 
                and
                not (
                    self.input_columns['first_period'] <= i 
                    <= self.last_period_index
                    )
                ):
                drop_columns.append(name)
                
        return drop_columns
    
        
    def _group_by_business_code(self):
        # tac and business code column will be used to group the data
        group_columns = [self.tac_column_name, self.business_code_column_name]
        
        # all periods will be summed
        sum_columns = [
            column_name for column_name in self.column_names 
            if constants.QUARTER_COLUMN_PREFIX in column_name.lower()
            ]
        
        self.df = self.df.groupby(
            group_columns, as_index=False, sort=False
            )[sum_columns].sum()
            
            
    def _set_table_column_names(self):
        names = [
            constants.TAC_COLUMN_NAME, constants.BUSINESS_CODE_ID_COLUMN_NAME
            ]
        
        period_headers = utilities.get_period_headers(
            count=self.period_count, year=int(self.year), quarter=int(self.quarter)
            )
        
        period_names = [
            f'{constants.QUARTER_COLUMN_PREFIX}{i}'.lower() 
            for i in period_headers
            ]
        
        self.table_column_names = names + period_names
        
            
    def _insert_id_column(self):
        # tac and business code column
        key_columns = [0, 1]
            
        id_column = self.df.iloc[
            :, key_columns].apply(lambda x: '-'.join(x.map(str)), axis=1)
        
        self.df.insert(0, constants.ID_COLUMN_NAME, id_column)
        
       
    def _create_table(self):
        con = sql.connect(
            constants.DB_PATHS[constants.STATEWIDE_DATASETS_DB]
            )

        with con:
            self.df.to_sql(
                self.table_name, con, if_exists='replace', index=False
                )
        
        con.close()
    
    
class View(tk.Toplevel):
    '''
    '''
    
    
    LABEL_WIDTH = 7
    WINDOW_HEIGHT = 110
    WINDOW_WIDTH = 550
    
    
    def __init__(self, controller, title):
        super().__init__()
        
        self.controller = controller
        
        # sets the window title
        self.title(title)
        
        self.file_path = tk.StringVar()
        self.period = tk.StringVar(value=self.controller.selected_period)
        
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
        button_frm = ttk.Frame(self)
        
        path_lbl = ttk.Label(path_frm, text='Path:', width=self.LABEL_WIDTH)
        path_ent = ttk.Entry(
            path_frm, state='readonly', textvariable=self.file_path
            )
        choose_btn = ttk.Button(
            choose_frm, text='Choose', command=self.controller.on_choose_click
            )
        
        period_lbl = ttk.Label(period_frm, text='Period:', width=self.LABEL_WIDTH)
        period_cbo = ttk.Combobox(
            period_frm, justify='right', state='readonly', textvariable=self.period,
            values=self.controller.period_options, width=7
            )
        
        self.load_btn = ttk.Button(
            button_frm, text='Load', command=self.controller.on_load_click
            )
        cancel_btn = ttk.Button(button_frm, text='Cancel', command=self.destroy)
        
        choose_frm.pack(fill='x', pady=constants.OUT_PAD)
        path_frm.pack(fill='x', expand=1, side='left', padx=constants.OUT_PAD)
        period_frm.pack(anchor='w', padx=constants.OUT_PAD)
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
        
        
    def disable_load_button(self):
        self.load_btn.config(state='disabled')
        
        
    def enable_load_button(self):
        self.load_btn.config(state='enabled')
    
    
class Controller:
    '''
    '''
    
    
    title = f'{constants.APP_NAME} - Load Business Code Totals'
    
    
    def __init__(self, period_options, selected_period):
        self.period_options = period_options
        self.selected_period = selected_period
        
        self.gui = View(self, self.title)
        self.gui.disable_load_button()
        
        
    def on_choose_click(self):
        file = filedialog.askopenfilename(parent=self.gui)
        
        if file:
            self.gui.file_path.set(file)
            
            self.gui.enable_load_button()
        
        
    def on_load_click(self):
        file_path = self.gui.file_path.get()
        
        if file_path:
            period = self.gui.period.get()
            
            model = Model(file_path, period, self.title)
            model.start()


