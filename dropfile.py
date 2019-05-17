'''
Created on Jul 20, 2018

@author: vahidrogo
'''

from copy import deepcopy
import re
from TkinterDnD2 import DND_FILES
import threading
import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox as msg
from tkinter import ttk
import traceback

from businessdetailjoin import BusinessDetailJoin
from clearviewdetail import ClearviewDetail
import constants
from datacontroller import DataController
from jurisdiction import Jurisdiction
import progress
from selections import Selections
import utilities


class DropFile:
    '''
    '''
    

    input_file_type = 'csv'
    
    
    def __init__(
            self, main, title, is_detail_join=False, 
            is_prior_period_payments=False):
        
        self.main = main
        self.title = title
        self.is_detail_join = is_detail_join
        self.is_prior_period_payments = is_prior_period_payments
        
        self.path_pattern = re.compile(r'[A-Z]:[^:]+\.[a-z]{3,4}')
        
        self.files = {}
        
        self.end_process = False
        
        self.selections = Selections(self.main)
        
        self.gui = DropFileGui(
            self, self.is_detail_join, self.is_prior_period_payments
            )
        
        self.clearview_detail = ClearviewDetail()
        
        
    def on_file_drop(self, event):
        '''
            When a file is dropped it is checked to make sure that the file
            type is the one that is supported and if it is and it has data
            then the path of where it will be saved will be showing the file
            list widget and the data will be loaded to a dataframe. The data 
            is also added to the file dictionary with the path as the key and 
            a dataframe as the value.
        '''
        input_paths = self._get_input_paths(event.data)
        
        self.add_files(input_paths)
                
                
    def add_files(self, paths):
        for path in paths:
            if self._is_supported_file(path):
                file_type = path.rsplit('.', 1)[1]
                
                if file_type != self.input_file_type:
                    msg.showerror(
                        self.title, 
                        f'Input file must be of type ({self.input_file_type}).',
                        parent=self.gui)
                else:
                    # loads the file in another thread
                    thread = threading.Thread(
                        target=self.load_csv_file, args=(path, )
                        )
                     
                    thread.daemon = True                           
                    thread.start()
            else:
                msg.showerror(
                    self.title, 'Data not supported.', parent=self.gui)
                
                
    def _is_supported_file(self, path):
        return any(i in path for i in self.supported_files)
                
                
    def _get_input_paths(self, input_data):
        '''
            Returns a list of the paths found in the input data of the
            files that where dropped in based on a regular expression 
            path pattern.
        '''
        return [
            re.sub('{|}', '', m) 
            for m in re.findall(self.path_pattern, input_data)
            ]
        
        
    def get_dataframe(self, path):
        self.clearview_detail.get_dataframe(path)
         
         
    def get_tac(self, df):
        '''
            Returns the tac by getting the fist value in the tac column.
        '''
        return df.iloc[:,constants.TAC_COLUMN][0]
    
    
    def get_jurisdiction(self, tac):
        '''
            Args:
                tac: A string representing the 5-digit tax area code.
                
            Returns:
                A jurisdiction() instance.
        '''
        jurisdiction = Jurisdiction(jurisdiction_tac=tac)
        
        if jurisdiction.exists:
            return jurisdiction
        
        else:
            msg.showerror(
                self.title, 
                f'TAC ({tac}) was not found in the database.',
                parent=self.gui
                )
            
            
    def get_file_name(self, jurisdiction, input_path):
        data_type = self.get_data_type(input_path)
        
        return f'{jurisdiction.id} {self.selections.period} {data_type}'
            
            
    def get_data_type(self, input_path):
        for i in self.supported_files:
            if i in input_path:
                return i
        
        
    def on_file_list_double_click(self, event):
        '''
            Removes the path from the file list widget and from the file 
            dictionary.
        '''
        selection = self.gui.file_list.curselection()
        item = self.gui.file_list.get(selection)
        
        if item != self.gui.DEFAULT_LIST_STRING:
            self.gui.file_list.delete(selection)
            
            if self.is_detail_join:
                self.set_quarter_count(self.files[item][1])
            
            del self.files[item]
            
    
    def get_files(self):
        return self.files
    
    
class DropFileGui(tk.Toplevel):
    '''
    '''
    
    
    def __init__(
            self, controller, is_detail_join=False, 
            is_prior_period_payments=False):
        
        super().__init__()
        
        self.controller = controller
        self.is_detail_join = is_detail_join
        self.is_prior_period_payments = is_prior_period_payments
        
        self.protocol('WM_DELETE_WINDOW', self._window_closed)

        constants.OUT_PAD = 10
        self.list_width = 85
        
        self.DEFAULT_LIST_STRING = 'Drop Here...'
        
        if self.is_prior_period_payments:
            self.open_chk_state = tk.IntVar()
        
        self._window_setup()
        self._make_widgets()
        
        self.config(menu=Menu(self))
        
        self.focus()
        
        
    def _window_setup(self):
        self.title(self.controller.title)
        
        app_w = 550
        app_h = 320
        
        x_offset = (self.winfo_screenwidth() - int(app_w))//2
        y_offset = (self.winfo_screenheight() - int(app_h))//2
        
        self.geometry(f'{app_w}x{app_h}+{x_offset}+{y_offset}')
        
        
    def _make_widgets(self):
        text = 'Files{}'.format(
            ' (0 Quarters)' if self.is_detail_join else ''
            )
        
        self.file_frame = ttk.LabelFrame(self, text=text)
        
        self.file_frame.pack(
            fill='both', expand=1, padx=constants.OUT_PAD, 
            pady=constants.OUT_PAD
            )
        
        self.file_list = tk.Listbox(self.file_frame, width=self.list_width)
        self.file_list.pack(fill='both', expand=1)
        
        bottom_frame = ttk.Frame(self)
        bottom_frame.pack(fill='x')
        
        if self.is_prior_period_payments:
            open_chk = ttk.Checkbutton(
                bottom_frame, text='Open', var=self.open_chk_state)
            
            open_chk.pack(padx=constants.OUT_PAD, side='left')
        
        button_frame = ttk.Frame(bottom_frame)
        button_frame.pack(
            padx=constants.OUT_PAD, pady=constants.OUT_PAD, side='right'
            )
        
        left_button_text = 'Save' if self.is_prior_period_payments else 'Load'
        
        self.left_btn = ttk.Button(
            button_frame, text=left_button_text, 
            command=self.controller.left_button_clicked
            )
        
        self.left_btn.pack(side='left', padx=constants.OUT_PAD)
        
        btn = ttk.Button(button_frame, text='Cancel', command=self.destroy)
        btn.pack()
        
        self.file_list.insert(0, self.DEFAULT_LIST_STRING)
        
        self.file_list.dnd_bind('<<Drop>>', self.controller.on_file_drop)
        
        self.file_list.drop_target_register(DND_FILES)
        
        self.file_list.bind(
            '<Double-Button-1>', self.controller.on_file_list_double_click
            )
        
        
    def _window_closed(self):
        self.destroy()
        self.controller.gui = None
        
        
    def disable_left_btn(self):
        self.left_btn.config(state='disabled')
    
    
    def enable_left_button(self):
        self.left_btn.config(state='enabled')
        
        
class Menu(tk.Menu):
    '''
    '''
    
    
    def __init__(self, parent):
        super().__init__()
        
        self.parent = parent
        
        self._make_file_menu()
        
        self.browse_folder = utilities.get_downloads_folder()
        
        
    def _make_file_menu(self):
        '''
            File menu.
            Browse For File sub menu allows the user to browse for a file.
        '''
        file_menu = tk.Menu(self, tearoff=False)
        
        self.add_cascade(label='File', underline=0, menu=file_menu)
        
        file_menu.add_command(
            label='Browse For File', underline=1, 
            command=self._browse_for_file
            )     
        
    
    def _browse_for_file(self):
        '''
            Opens a window that allows the user to choose a file.
        '''
        paths = filedialog.askopenfilenames(
            initialdir=self.browse_folder, parent=self.parent)
        
        if paths:
            self.parent.controller.add_files(paths)
            

class DropDetail(DropFile):
    '''
        Logic for DataGui().
    '''
    
    
    def __init__(self, main):
        self.title = f'{constants.APP_NAME} - Load Business Detail'
        super().__init__(main, self.title)
        
        self.supported_files = ['QE', 'QC']
        
        
    def left_button_clicked(self):
        '''
            Creates an object of the SaveController class which runs
            in another class and passes a deep copy of the file dictionary. 
            The deepcopy is so that the original dictionary can be cleared, 
            so that if the user clicks the button again, the same files 
            will not be saved again.
        '''
        if self.files:
            self.gui.file_list.delete(1, 'end')
            
            data_controller = DataController(self)
            
            self.files.clear()
            data_controller.start()
        
        
    def load_csv_file(self, path):
        '''
            Loads the csv file into a dataframe and gets the needed data 
            from it if it is found in the database to get the path of where 
            it will be saved.
        '''
        df = self.clearview_detail.get_dataframe(path)
        
        if not df is None:
            tac = self.get_tac(df)
            
            jurisdiction = self.get_jurisdiction(tac)
            
            if jurisdiction:
                file_name = self.get_file_name(jurisdiction, path)
                 
                if file_name not in self.files:
                    self.gui.file_list.insert('end', file_name)
                    
                    self.files[file_name] = (jurisdiction, df)
                    
                    
class DropDetailJoin(DropFile):
    '''
    '''
    
    
    title = f'{constants.APP_NAME} - Load Business Detail (Join)'
    
    
    def __init__(self, main):
        super().__init__(main, self.title, is_detail_join=True)
        
        self.supported_files = ['QE', 'QC']
        
        self.jurisdiction_loaded = False
        self.load_enabled = False
        
        self.period_count = 0
        
        self.data_type = ''
        self.tac = ''
        
        self.file_name = ''
        
        self.gui.disable_left_btn()
        
        
    def left_button_clicked(self):
        self._set_quarters()
        
        if not self._duplicate_periods_exist():
            if not self._period_gaps_exist():
                self.gui.file_list.delete(1, 'end')
                
                business_detail_join = BusinessDetailJoin(
                    self.jurisdiction, deepcopy(self.files), self.selections
                    )
                
                business_detail_join.start()
                   
                self.files.clear()
                   
                self.period_count = 0
                self._set_period_count_label()
                    
    
    def load_csv_file(self, path):
        loading_circle = progress.LoadingCircle(
            parent=self.gui, text='Reading', bg_color='white'
            )
        loading_circle.start()
        
        try:
            df = self.clearview_detail.get_dataframe(path)
            
        except Exception:
            msg.showerror(
                self.title, 
                f'Unhandled exception occurred:\n\n{traceback.format_exc()}'
                )
            
        finally:
            loading_circle.end()
        
        if not df is None:
            file_count = self._get_file_count()
            # if a jurisdiction has already been loaded but all the files
            # were removed then the flag to load the jurisdiction will be reset
            if self.jurisdiction_loaded and not file_count:
                self.jurisdiction_loaded  = False
            
            check_new_file = True
            if not self.jurisdiction_loaded:
                self.tac = self.get_tac(df)
                
                data_type = self.get_data_type(path)
                self.data_type = data_type
                
                self.jurisdiction = self.get_jurisdiction(self.tac)
                
                if self.jurisdiction:
                    self._set_file_name()
                    
                    self.jurisdiction_loaded = True
                    check_new_file = False
            else:
                tac = self.get_tac(df)
                data_type = self.get_data_type(path)
                
            if data_type in self.supported_files:
                same_juri = True
                same_data_type = True
                if check_new_file:
                    if self.tac and tac != self.tac:
                        same_juri = False
                        
                        msg.showerror(
                            self.title, 
                            'Can only join one jurisdiction at a time. '
                            f'Data for ({self.tac}) has already been '
                            f'loaded. To join files for ({tac}) either '
                            'open another window or clear all the files.',
                            parent=self.gui)
                    
                    if same_juri and self.data_type and data_type != self.data_type:
                        same_data_type = False
                        
                        msg.showerror(
                            self.title, 
                            'Can only join one data type at a time. '
                            f'Data for ({self.data_type}) has already been '
                            f'loaded. To join files for ({data_type}) either '
                            'open another window or clear all the files.',
                            parent=self.gui)
                        
                if same_juri and same_data_type:
                    quarter_range = self._get_quarter_range(df)
                    
                    display_name = (
                        f'{self.jurisdiction.id} {data_type}: {quarter_range}'
                        )
                    
                    if not display_name in self.files:
                        self.gui.file_list.insert('end', display_name)
                        
                        self.files[display_name] = (self.jurisdiction, df)
                        
                        period_count = self._get_period_count(df)
                        
                        self.period_count += period_count
                        
                        self._set_period_count_label()
                        
                        if not self.load_enabled and len(self.files) >= 2:
                            self.gui.enable_left_button()
                            
                            self.load_enabled = True
            else:
                msg.showerror(
                self.title, 
                'Data type not supported. Supported data types are:'
                f'\n\n({self.supported_files}) \n\nIf this is '
                'one of those files, make sure that it is reflected '
                'in the name of the file.', parent=self.gui)
                
                
    def _set_file_name(self):
        self.file_name = (
            f'{self.main.get_period()} {self.jurisdiction.id} {self.data_type}'
            )
                
                
    def on_file_list_double_click(self, event):
        DropFile.on_file_list_double_click(self, event)
        
        file_count = self._get_file_count()
        
        # resets the tac and file type
        if not file_count:
            self.tac = ''
            self.data_type = ''
            
            if self.load_enabled:
                self.gui.disable_left_btn()
                
                self.load_enabled = False
            
            
    def _get_file_count(self):
        return len(self.files)
            
            
    def _get_quarter_range(self, df):
        columns = list(df)
        return f'{columns[constants.FIRST_QUARTER_COLUMN]} - {columns[-1]}'
    
    
    def _set_quarters(self):
        self.quarters = [
            f'{q[-4:]}{q[0]}' for i in self.files.values() 
            for q in list(i[1])[constants.FIRST_QUARTER_COLUMN:]
            ]
        
        
    def _duplicate_periods_exist(self):
        duplicates = False
        if len(self.quarters) != len(set(self.quarters)):
            duplicates = True
            
            msg.showerror(
                self.title, 
                'Duplicate quarters in files. Please make sure there '
                'are no overlapping quarters in the files to join.',
                parent=self.gui) 
            
        return duplicates
    
    
    def _period_gaps_exist(self):
        gaps = False
        
        # oldest quarter
        quarters = sorted(self.quarters)
        current_quarter = quarters[0]
        
        for q in quarters[1:]:
            # more recent that follows the current quarter
            next_quarter = self._get_next_quarter(current_quarter)
            
            if q != next_quarter:
                gaps = True
                
                msg.showerror(
                    self.title, 
                    'Quarters are not continuous. Please make sure that '
                    'the quarters in the files result in a continuous '
                    'range when joined.',
                    parent=self.gui)
                
                break
            else:
                current_quarter = q
            
        return gaps
    
    
    def _get_next_quarter(self, quarter):
        quarter_number = int(quarter[-1])
        year = int(quarter[:4])
        if quarter_number == 4:
            quarter_number = 1
            year += 1 
        else:
            quarter_number += 1
       
        return f'{year}{quarter_number}'
    
    
    def set_period_count(self, df):
        period_count = self._get_period_count(df)
                
        self.period_count -= period_count
        
        self._set_period_count_label()
        
        
    def _get_period_count(self, df):
        return len(list(df)[constants.FIRST_QUARTER_COLUMN:])
        
        
    def _set_period_count_label(self):
        self.gui.file_frame.configure(
            text=f'Files ({self.period_count} Quarters)')