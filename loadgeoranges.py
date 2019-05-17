'''
Created on Feb 6, 2019

@author: vahidrogo
'''

import ntpath
import pandas
import threading
import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox as msg
from tkinter import ttk
import traceback

from comboboxautocomplete import ComboboxAutoComplete
import constants
import utilities
'''
    TODO
    
        - Verify that all required columns are present in file
        - Load the ranges into statewide_datasets.geo_ranges
'''
class Model(threading.Thread):
    '''
    '''
    
    
    def __init__(self):
        super().__init__()
        
        
class View(tk.Toplevel):
    '''
    '''
    
    
    LABEL_WIDTH = 11
    WINDOW_HEIGHT = 350
    WINDOW_WIDTH = 500
    
    
    def __init__(self, controller, window_title):
        super().__init__()
        
        self.controller = controller
        self.window_title = window_title
        
        self.column_index_vars = {}
        
        self.file_path_var = tk.StringVar()
        self.jurisdiction_var = tk.StringVar()
        self.range_id_var = tk.StringVar()
        
        self.jurisdiction_var.trace('w', self.controller.on_jurisdiction_change)
        
        # sets the window title
        self.title(window_title)
        
        self._center_window()
        self._make_file_widgets()
        
    
    def _center_window(self):
        x_offset = (self.winfo_screenwidth() - self.WINDOW_WIDTH) // 2
        y_offset = (self.winfo_screenheight() - self.WINDOW_HEIGHT) // 2
        
        self.geometry(
            f'{self.WINDOW_WIDTH}x{self.WINDOW_HEIGHT}+{x_offset}+{y_offset}'
            )
        
        
    def _make_file_widgets(self):
        choose_frm = ttk.Frame(self)
        
        file_frm = ttk.Frame(choose_frm)
        choose_lbl = ttk.Label(file_frm, text='File:', width=5)
        choose_ent = ttk.Entry(
            file_frm, state='readonly', textvariable=self.file_path_var
            )
        
        choose_btn = ttk.Button(
            choose_frm, text='Choose', command=self.controller.on_choose_click
            )
        
        choose_frm.pack(fill='x', pady=constants.OUT_PAD)
        
        file_frm.pack(side='left', fill='x', expand=1, padx=constants.OUT_PAD)
        choose_lbl.pack(side='left')
        choose_ent.pack(fill='x', expand=1)
        
        choose_btn.pack(padx=constants.OUT_PAD)
        

        
    def make_column_widgets(self):
        column_lbl = ttk.Label(
            self, 
            text='The following columns are required: '
            f'({", ".join(self.controller.required_columns)}).'
            )
        
        index_frm = ttk.Labelframe(self, text='Column Indexes')
        
        for column in self.controller.required_columns:
            var = tk.StringVar()
            var.trace('w', self.controller.on_column_index_change)
            
            self.column_index_vars[column] = var
            
            frm = ttk.Frame(index_frm)
            lbl = ttk.Label(frm, text=f'{column}:', width=self.LABEL_WIDTH)
            ent = ttk.Entry(frm, textvariable=var)
            
            frm.pack(fill='x')
            lbl.pack(side='left')
            ent.pack(fill='x')
        
        column_lbl.pack(anchor='w', padx=constants.OUT_PAD)
        index_frm.pack(fill='x', padx=constants.OUT_PAD, pady=constants.OUT_PAD)
        
        
    def make_button_widgets(self):
        frm = ttk.Frame(self)
        self.load_btn = ttk.Button(frm, text='Load', command=self.controller.on_load_click)
        cancel_btn = ttk.Button(frm, text='Cancel', command=self.destroy)
        
        self.disable_load_button()
        
        frm.pack(anchor='e')
        self.load_btn.pack(side='left')
        cancel_btn.pack(padx=constants.OUT_PAD)
        
        
    def make_select_widgets(self):
        jurisdiction_frm = ttk.Frame(self)
        jurisdiction_lbl = ttk.Label(
            jurisdiction_frm, text='Jurisdiction:', width=self.LABEL_WIDTH
            )
        
        jurisdiction_cbo = ComboboxAutoComplete(
            jurisdiction_frm, value_list=self.controller.jurisdictions
            )
        
        range_id_frm = ttk.Frame(self)
        range_id_lbl = ttk.Label(
            range_id_frm, text='Range Id:', width=self.LABEL_WIDTH
            )
        range_id_cbo = ttk.Combobox(
            range_id_frm, textvariable=self.range_id_var
            )
        
        jurisdiction_frm.pack(anchor='w', padx=constants.OUT_PAD)
        jurisdiction_lbl.pack(side='left')
        jurisdiction_cbo.pack()
        
        range_id_frm.pack(
            anchor='w', padx=constants.OUT_PAD, pady=constants.OUT_PAD
            )
        range_id_lbl.pack(side='left')
        range_id_cbo.pack()
        
        
    def disable_load_button(self):
        self.load_btn.config(state='disabled')
    
    
    def enable_load_button(self):
        self.load_btn.config(state='enabled')
        
        
        
class Controller:
    '''
    '''
    
    
    input_file_type = 'xlsx'
    
    required_columns = [
        'street', 'street_type', 'dir', 'pdir', 'side', 'low', 'high'
        ]
    
    title = f'{constants.APP_NAME} - Load Geo Ranges'
    
    
    def __init__(self):
        self.file_path = ''
        self.jurisdiction = ''
        
        self.columns = []
        self.jurisdictions = []
        
        self.df = None
        
        self.widgets_created = False
        
        self._set_jurisdictions()
        
        self.gui = View(self, self.title)
        
        
    def _set_jurisdictions(self):
        tables = [
            constants.JURISDICTIONS_TABLE, constants.ADDONS_TABLE, 
            constants.TRANSITS_TABLE
            ]
        
        for table in tables:
            query = f'''
                SELECT {constants.ID_COLUMN_NAME}
                FROM {table}
                '''
            
            results = utilities.execute_sql(
                sql_code=query, db_name=constants.STARS_DB, fetchall=True
                )
            
            if results:
                for result in results:
                    self.jurisdictions.append(result[0])
    
    
    def on_choose_click(self):
        path = filedialog.askopenfilename(parent=self.gui)
        
        if path:
            extension = ntpath.basename(path).rsplit('.', 1)[1].lower()
            
            if extension == self.input_file_type:
                self.file_path = path
                
                # displays the path in the window
                self.gui.file_path_var.set(path)
                
                try:
                    self.df = pandas.read_excel(self.file_path)
                    
                except Exception:
                    msg.showerror(
                        self.title,
                        'Unhandled exception occurred trying to load:\n\n'
                        f'{self.file_path}\n\n{traceback.format_exc()}',
                        parent=self.gui
                        )
                
                if self.df is not None:
                    self.columns = list(self.df)
                    
                    if not self.widgets_created:
                        self.gui.make_select_widgets()
                        self.gui.make_column_widgets()
                        self.gui.make_button_widgets()
                        
                        self.widgets_created = True
            
            else:
                msg.showinfo(
                    self.title,
                    f'Input file type must be of type ({self.input_file_type})',
                    parent=self.gui
                    )
                
                
    def on_jurisdiction_change(self, *args):
        jurisdiction = self.gui.jurisdiction_var.get()
        
        if jurisdiction != self.jurisdiction:
            self.jurisdiction = jurisdiction
            
            range_ids = self._fetch_range_ids(jurisdiction)
            print('range ids', range_ids)
        
    def _fetch_range_ids(self, jurisdiction):
        query = f'''
            SELECT UNIQUE {constants.GEO_RANGES_TABLE}
            FROM {constants.STATEWIDE_DATASETS_DB}
            WHERE {constants.JURISDICTION_ID_COLUMN}=?
            '''
        
        args = (jurisdiction, )
        
        results = utilities.execute_sql(
            sql_code=query, args=args, fetchll=True,
            db_name=constants.STATEWIDE_DATASETS_DB
            )
        print(results)
        if results:
            ids = [i[0] for i in results]
        
        else:
            ids = []
            
        return ids
                
                
    def on_load_click(self):
        print('load click')
        
        
    def on_column_index_change(self, *args):
        print('index changed')
                
                
                
                
                
                
                
                
                
                
                
                
                
                
                
                
                
                
                
                
                
                
                
                
                
                
                
                
                
                
                
                