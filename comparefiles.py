'''
Created on Dec 19, 2018

@author: vahidrogo
'''

import pandas
from pathlib import Path
import pathvalidate
from pyexcelerate import Workbook
import threading
import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox as msg
from tkinter import ttk
import traceback

import constants
import progress
import utilities


KEY_COLUMN_NAME = 'key'
PRESENT_IN_COLUMN_NAME = 'present_in'
    

class Model(threading.Thread):
    '''
    '''
    
    
    def __init__(
            self, path_one, path_two, key_columns_one, key_columns_two, 
            output_path, open_output, include_options, title):
        
        super().__init__()
        
        self.paths = {'one' : path_one, 'two' : path_two}
        
        self.key_columns = {
            'one' : self._get_parsed_key_columns(key_columns_one), 
            'two' : self._get_parsed_key_columns(key_columns_two)
            }
        
        self.output_path = output_path
        self.open_output = open_output
        self.include_options = include_options
        self.title = title
        
        self.output_saved = False
        
        self.dfs = {'one' : None, 'two' : None}
        
        self.keys = {'one' : set(), 'two' : set()}
        
        
    def _get_parsed_key_columns(self, key_columns):
        parsed_key_columns = []
        
        if ',' in key_columns:
            for item in key_columns.split(','):
                item = item.strip()
                
                if item:
                    parsed_key_columns.append(int(item) - 1)
        elif ':' in key_columns:
            range_columns = key_columns.split(':')
            
            start = int(range_columns[0].strip())
            
            end = int(range_columns[1].strip())
            
            parsed_key_columns = [i - 1 for i in range(start, end + 1)]
            
        else:
            parsed_key_columns.append(int(key_columns.strip()) - 1)
        
        return parsed_key_columns
    
    
    def run(self):
        # if at least one include option was included
        if any(i for i in self.include_options.values()):
            self._set_dataframes()
            
            self._insert_key_columns()
            
            self._set_keys()
            
            self._insert_present_in_columns()
            
            in_both_data = []
            if not self.include_options['both']:
                for name, df in self.dfs.items():
                    self.dfs[
                        name] = df[
                            df[PRESENT_IN_COLUMN_NAME] != 'both_files']
                
            else:
                if (
                    not self.include_options['one'] 
                    and not self.include_options['two']):
                    
                    in_both_data = self._get_in_both_data()
    
            self._write_xlsx_output(in_both_data)
            
            if self.output_saved and self.open_output:
                utilities.open_file(self.output_path)
        
        
    def _set_dataframes(self):
        for name, path in self.paths.items():
            df = self._get_dataframe(path)
            
            utilities.FillNa.fill_na(df)
            
            self.dfs[name] = df
    
    
    def _get_dataframe(self, path):
        file_extension = path.rsplit('.', 1)[1].lower()
        
        if file_extension in ['xlsx', 'xls']:
            df = pandas.read_excel(path)
        
        elif file_extension == 'csv':
            df = pandas.read_csv(path)
        else:
            df = None
            
        return df
    
    
    def _insert_key_columns(self):
        for name, df in self.dfs.items():
            key_columns = self.key_columns[name]
            
            key_column = df.iloc[
                :, key_columns].apply(
                    lambda x :''.join(x.map(str).map(str.strip)), axis=1)
            
            df.insert(0, KEY_COLUMN_NAME, key_column)
            
            utilities.FillNa.fill_na(df)
            
            
    def _set_keys(self):
        for name, df in self.dfs.items():
            keys = set(df[KEY_COLUMN_NAME].values.tolist())
            
            self.keys[name] = keys
            
            
    def _insert_present_in_columns(self):
        for name, df in self.dfs.items():
            other_file = 'two' if name == 'one' else 'one'
            
            present_in_column = []
            
            for row in df.itertuples(index=False):
                key = row[0]
                
                present_in = (
                    'both_files' if key in self.keys[other_file] 
                    else f'file_{name}')
                
                present_in_column.append(present_in)
                
            df.insert(0, PRESENT_IN_COLUMN_NAME, present_in_column)
            
            
    def _get_in_both_data(self):
        column_names = list(self.dfs['one'])
        
        df = self.dfs['one']
        
        data = df[
            df[PRESENT_IN_COLUMN_NAME] == 'both_files'].values.tolist()
        
        data = [column_names, ] + data
        
        return data
            
            
    def _write_xlsx_output(self, in_both_data=[]):
        wb = Workbook()
        
        if in_both_data:
            wb.new_sheet('in_both', data=in_both_data)
            
        else:
            for name, df in self.dfs.items():
                if self.include_options[name]:
                    sheet_name = f'file_{name}'
                    
                    column_names = list(df)
                    
                    data = [column_names, ] + df.values.tolist()
                
                    wb.new_sheet(sheet_name, data=data)
        
        try_to_save = True
        while try_to_save:
            try:
                wb.save(self.output_path)
                self.output_saved = True
                try_to_save = False
                
            except PermissionError:
                try_to_save = msg.askretrycancel(
                    self.title,
                    f'Could not save file to ({self.output_path}) '
                    'because there is a file with that name currently '
                    'open. Close that file to allow for this one to be '
                    'saved.')


class Controller:
    '''
    '''
    
    key_columns_example = '4; 4,7; 4:7'
    
    key_column_series_separator = ','
    key_column_range_separator = ':'
    
    output_type = 'xlsx'
    
    
    def __init__(self):
        self.path_one = ''
        self.path_two = ''
        
        self._setup_view()
        
        
    def _setup_view(self):
        self.gui = View(self)
        
        self.gui.choose_button_one.configure(
            command=self._on_choose_button_one_click)
        
        self.gui.choose_button_two.configure(
            command=self._on_choose_button_two_click)
        
        self.gui.compare_button.configure(command=self._on_compare_click)
        
        
    def _on_choose_button_one_click(self):
        file_path = filedialog.askopenfilename(parent=self.gui)
        
        if file_path:
            self.gui.path_one.set(file_path)
            
            self.path_one = file_path
            
            if self.path_two:
                self._set_output_path()
            
            
    def _on_choose_button_two_click(self):
        file_path = filedialog.askopenfilename(parent=self.gui)
        
        if file_path:
            self.gui.path_two.set(file_path)
            
            self.path_two = file_path
            
            if self.path_one:
                self._set_output_path()
                
                
    def _on_compare_click(self):
        if self._input_files_chosen():
            if self._input_files_unique():
                key_columns_one = self.gui.key_columns_one.get()
                
                key_columns_two = self.gui.key_columns_two.get()
                
                if self._key_columns_valid(key_columns_one, key_columns_two):
                    output_path = self.gui.output_path.get()
                    
                    if self._output_path_valid(output_path):
                        thread = threading.Thread(
                            target=self._compare, args=(key_columns_one, key_columns_two, output_path)
                            )
                        
                        thread.daemon = True
                        
                        # compare the files in another thread
                        thread.start()
                        
                        
    def _compare(self, key_columns_one, key_columns_two, output_path):
        loading_circle = progress.LoadingCircle(self.gui, text='Comparing')
        loading_circle.start()
        
        open_output_state = self.gui.open_output_state.get()
                            
        include_options = self._get_inlclude_options()
        
        self.Model = Model(
            self.path_one, self.path_two, key_columns_one,
            key_columns_two, output_path, open_output_state,
            include_options, self.gui.window_title
            )
        
        try:
            self.Model.run()
            
        except Exception:
            msg.showerror(
                self.gui.window_title,
                f'Unhandled exception occurred:\n\n{traceback.format_exc()}',
                parent=self.gui
                )
        
        finally:
            loading_circle.end()
            
            
    def _input_files_chosen(self):
        input_files_chosen = False
        
        if self.path_one and self.path_two:
            input_files_chosen = True
        else:
            input_files_chosen = False
            
            msg.showerror(
                self.gui.window_title, 'Both files must be chosen.',
                parent=self.gui)
            
        return input_files_chosen
    
    
    def _input_files_unique(self):
        if self.path_one != self.path_two:
            input_files_unique = True
        else:
            input_files_unique = False
            
            msg.showerror(
                self.gui.window_title, 'Files are the same.', 
                parent=self.gui)
            
        return input_files_unique
    
    
    def _key_columns_valid(self, key_columns_one, key_columns_two):
        key_columns_valid = True
        
        for key_columns in [key_columns_one, key_columns_two]:
            if key_columns_valid:
                if self._is_column_series(key_columns):
                    separator = self.key_column_series_separator
                    
                elif self._is_column_range(key_columns):
                    separator = self.key_column_range_separator
                    
                else:
                    separator = ''
                    
                if separator:
                    columns = key_columns.split(separator)
                    
                    for item in columns:
                        item = item.strip()
                        
                        if not item.isdigit():
                            key_columns_valid = False
                            
                    if key_columns_valid and self._is_column_range(key_columns):
                        if len(columns) > 2:
                            key_columns_valid = False
                            
                        else:
                            start = int(columns[0])
                            
                            end = int(columns[1])
                            
                            if end <= start:
                                key_columns_valid = False
                            
                else:
                    if not key_columns.strip().isdigit():
                        key_columns_valid = False
                            
        if not key_columns_valid:
            msg.showerror(
                self.gui.window_title, 
                'Key columns must be like one of '
                f'[{self.key_columns_example}]',
                parent=self.gui)
            
        return key_columns_valid
    
    
    def _is_column_series(self, key_columns):
        return self.key_column_series_separator in key_columns
    
    
    def _is_column_range(self, key_columns):
        return self.key_column_range_separator in key_columns
    
            
    def _output_path_valid(self, output_path):
        try:
            pathvalidate.validate_filepath(output_path)
            
            output_path_valid = True
        except:
            output_path_valid = False
            
            msg.showerror(
                self.gui.window_title, 'Output path is not a valid path.',
                parent=self.gui)
            
        return output_path_valid
        
            
    def _set_output_path(self):
        output_path = self._get_output_path()
        
        self.gui.output_path.set(output_path)
        
        
    def _get_output_path(self):
        name_one = self._get_file_name(self.path_one)
        
        name_two = self._get_file_name(self.path_two)
        
        file_name = f'{name_one} & {name_two} comparison.{self.output_type}'
        
        folder = Path(self._get_folder(self.path_one))
        
        output_path = str(folder.joinpath(file_name))
        
        return output_path
        
        
    def _get_file_name(self, file_path):
        name = Path(file_path).name
        
        # gets the name without the extension
        name = name.rsplit('.', 1)[0]
        
        return name
    
    
    def _get_folder(self, path):
        return Path(path).parent
    
    
    def _get_inlclude_options(self):
        return {
            'one' : self.gui.only_in_one_state.get(),
            'two' : self.gui.only_in_two_state.get(),
            'both' : self.gui.in_both_state.get()
            }
                
                
class View(tk.Toplevel):
    '''
    '''
    
    
    window_title = f'{constants.APP_NAME} - Compare Files'
    
    LABEL_WIDTH = 12    
    
    
    def __init__(self, controller):
        super().__init__()
        
        self.controller = controller
        
        self.path_one = tk.StringVar()
        
        self.path_two = tk.StringVar()
        
        self.key_columns_one = tk.StringVar()
        
        self.key_columns_two = tk.StringVar()
        
        self.output_path = tk.StringVar()
        
        self.only_in_one_state = tk.IntVar(value=1)
        
        self.only_in_two_state = tk.IntVar(value=1)
        
        self.in_both_state = tk.IntVar(value=1)
        
        self.open_output_state = tk.IntVar(value=1)
        
        self._window_setup()
        
        self._make_file_one_widgets()
        
        self._make_file_two_widgets()
        
        self._make_output_widgets()
        
        self._make_include_widgets()
        
        self._make_button_widgets()
    
    
    def _window_setup(self):
        self.title(self.window_title)
        
        app_w = 700
        app_h = 350
        
        x_offset = (self.winfo_screenwidth() - int(app_w))//2
        y_offset = (self.winfo_screenheight() - int(app_h))//2
        
        self.geometry(f'{app_w}x{app_h}+{x_offset}+{y_offset}')
        
        
    def _make_file_one_widgets(self):
        lbl_frm = ttk.Labelframe(self, text='File 1')
        lbl_frm.pack(
            fill='x', padx=constants.OUT_PAD, pady=constants.OUT_PAD)
        
        choose_frm = ttk.Frame(lbl_frm)
        choose_frm.pack(
            fill='x', padx=constants.IN_PAD, pady=constants.IN_PAD)
        
        frm = ttk.Frame(choose_frm)
        frm.pack(expand=1, fill='x', side='left')
        
        lbl = ttk.Label(frm, text='Path:', width=self.LABEL_WIDTH)
        lbl.pack(side='left')
        
        ent = ttk.Entry(
            frm, state='readonly', textvariable=self.path_one)
        ent.pack(fill='x')
        
        self.choose_button_one = ttk.Button(choose_frm, text='Choose')
        self.choose_button_one.pack(
            anchor='e', side='right', padx=constants.IN_PAD)
        
        key_columns_frm = ttk.Frame(lbl_frm)
        key_columns_frm.pack(anchor='w')
        
        frm = ttk.Frame(key_columns_frm)
        frm.pack(anchor='w', padx=constants.IN_PAD, side='left')
        
        lbl = ttk.Label(frm, text='Key Columns:', width=self.LABEL_WIDTH)
        lbl.pack(side='left')
        
        ent = ttk.Entry(frm, textvariable=self.key_columns_one)
        ent.pack()
        
        lbl = ttk.Label(
            key_columns_frm, text=f'Ex: {self.controller.key_columns_example}')
        lbl.pack()
        
        
    def _make_file_two_widgets(self):
        lbl_frm = ttk.Labelframe(self, text='File 2')
        lbl_frm.pack(
            fill='x', padx=constants.OUT_PAD, pady=constants.OUT_PAD)
        
        choose_frm = ttk.Frame(lbl_frm)
        choose_frm.pack(
            fill='x', padx=constants.IN_PAD, pady=constants.IN_PAD)
        
        frm = ttk.Frame(choose_frm)
        frm.pack(expand=1, fill='x', side='left')
        
        lbl = ttk.Label(frm, text='Path:', width=self.LABEL_WIDTH)
        lbl.pack(side='left')
        
        ent = ttk.Entry(
            frm, state='readonly', textvariable=self.path_two)
        ent.pack(fill='x')
        
        self.choose_button_two = ttk.Button(choose_frm, text='Choose')
        self.choose_button_two.pack(
            anchor='e', side='right', padx=constants.IN_PAD)
        
        key_columns_frm = ttk.Frame(lbl_frm)
        key_columns_frm.pack(anchor='w')
        
        frm = ttk.Frame(key_columns_frm)
        frm.pack(anchor='w', padx=constants.IN_PAD, side='left')
        
        lbl = ttk.Label(frm, text='Key Columns:', width=self.LABEL_WIDTH)
        lbl.pack(side='left')
        
        ent = ttk.Entry(frm, textvariable=self.key_columns_two)
        ent.pack()
        
        lbl = ttk.Label(
            key_columns_frm, text=f'Ex: {self.controller.key_columns_example}')
        lbl.pack()
        
        
    def _make_output_widgets(self):
        output_frm = ttk.Frame(self)
        
        frm = ttk.Frame(output_frm)
        
        lbl = ttk.Label(frm, text='Output Path:', width=self.LABEL_WIDTH)
        
        ent = ttk.Entry(frm, textvariable=self.output_path)
        
        chk = ttk.Checkbutton(output_frm, text='Open', var=self.open_output_state)
        
        output_frm.pack(fill='x', padx=constants.OUT_PAD)
        
        frm.pack(expand=1, fill='x', side='left', padx=constants.IN_PAD)
        
        lbl.pack(side='left')
        
        ent.pack(fill='x')
        
        chk.pack(anchor='e')
        
        
    def _make_include_widgets(self):
        frm = ttk.Labelframe(self, text='Included in Output')
        frm.pack(anchor='w', padx=constants.OUT_PAD, pady=constants.OUT_PAD)
        
        chk = ttk.Checkbutton(
            frm, text='Only in File 1', var=self.only_in_one_state)
        chk.pack(anchor='w', padx=constants.IN_PAD)
        
        chk = ttk.Checkbutton(
            frm, text='Only in File 2', var=self.only_in_two_state)
        chk.pack(anchor='w', padx=constants.IN_PAD)
        
        chk = ttk.Checkbutton(
            frm, text='In both', var=self.in_both_state)
        chk.pack(anchor='w', padx=constants.IN_PAD)
        
        
    def _make_button_widgets(self):
        frm = ttk.Frame(self)
        
        self.compare_button = ttk.Button(frm, text='Compare')
        
        cancel_btn = ttk.Button(
            frm, text='Cancel', command=self.destroy)
        
        frm.pack(anchor='e')
        
        self.compare_button.pack(side='left')
        
        cancel_btn.pack(padx=constants.OUT_PAD, pady=constants.IN_PAD)
        
            
        
