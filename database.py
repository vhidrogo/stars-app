'''
Created on Dec 3, 2018

@author: vahidrogo
'''

from collections import namedtuple
from entrysearch import EntrySearch
import getpass
import ntpath
import numpy as np
import pandas as pd
from pandas.errors import ParserError
from pathlib import Path
from pyexcelerate import Workbook
import re
from recordclass import recordclass
import sqlite3 as sql
import threading
import time
import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox as msg
from tkinter import ttk

from comboboxautocomplete import ComboboxAutoComplete
import constants
from copydb import CopyDb
from framescroll import FrameScroll
import progress
from tooltip import ToolTip
import utilities


'''
    TODO 
    
    Finish implementing alter column functionality
    Finish implementing insert column functionality
    
    Add functionality for entering default values when setting column to NULL
'''

Column = recordclass(
    'Column', 
    'index name data_type not_null default primary_key constraint '
    'ref_table ref_column is_foreign_key'
    )
    
    
Reference = namedtuple('Reference', 'ref_table ref_column')


class Controller:
    '''
    '''
    
    
    export_types = {0 : 'CSV', 1 : 'TXT', 2 : 'XLSX'}
    
    DEFAULT_EXPORT_TYPE = 2
    
    DEFAULT_CBO_WIDTH = 40
    MIN_CBO_WIDTH = DEFAULT_CBO_WIDTH / 2
    MAX_CBO_WIDTH = DEFAULT_CBO_WIDTH * 2
    
    import_table_types = ['csv', 'xlsx']
    
    new_table_column_limit = 500
    
    
    def __init__(self, mode):
        self.backups = {}
        self.foreign_keys = {}
        
        self.search_matches = []
        
        self.columns = {}
        self.column_names = []
        self.table_info = []
        self.table_names = []
        
        self.column_name = ''
        self.db_name = ''
        self.table_name = ''
        self.table_sql = ''
        
        self.column_count = 0
        self.row_count = 0
        
        self.new_table_column_count = 0
        
        self.value_label_len = 0
        
        self.mouse_x = 0
        
        self.dragging = False
        
        # flags that indicate whether or not the respective widgets have 
        # been created
        self.column_widgets = False
        self.db_widgets = False
        self.renaming_table = False
        self.table_widgets = False
        self.value_widgets = False
        
        # flags that indicate whether or not the respective buttons have 
        # been enabled
        self.alter_column_enabled = False
        self.alter_record_enabled = False
        self.alter_table_enabled = False
        self.insert_record_enabled = False
        self.search_enabled = False
        
        self.id_column_tooltip = False
        
        self.new_table_df = None
        self.primary_key_index = None
        
        self.between_parenthesis_pattern = re.compile(r'\((.*)\)')
        
        self.foreign_key_pattern = re.compile(
            r'FOREIGN KEY\([^\)]+\) REFERENCES [^\(]+\([^\)]+\)'
            )
        
        self.version_pattern = re.compile(r'(\(\d\d?\))$')
        
        self.user_id = utilities.fetch_user_id(getpass.getuser())
        
        self._set_default_widths()
        
        # 0 for alter, 1 for insert
        self.mode = mode
        
        self.gui = View(self)
        
        self._set_title()
        
        
    def _set_title(self):
        self.title = f'{constants.APP_NAME} - Database {constants.DB_MODES[self.mode]}'
        
        self.gui.title(self.title)
        
        
    def _set_default_widths(self):
        '''
            Sets the default widths of the combobox and entry widgets.
        '''
        db_cbo_width = utilities.fetch_default(
            'db_cbo_width', self.user_id
            )
        
        self.db_cbo_width = (
            db_cbo_width if db_cbo_width else self.DEFAULT_CBO_WIDTH
            )
        
        table_cbo_width = utilities.fetch_default(
            'table_cbo_width', self.user_id
            )
        
        self.table_cbo_width = (
            table_cbo_width if table_cbo_width else self.DEFAULT_CBO_WIDTH
            )
        
        self.table_ent_width = self.table_cbo_width + 3
        
        column_cbo_width = utilities.fetch_default(
            'column_cbo_width', self.user_id
            )
        
        self.column_cbo_width = (
            column_cbo_width if column_cbo_width else self.DEFAULT_CBO_WIDTH
            )
        
        self.column_ent_width = self.column_cbo_width + 3
        

    def on_mode_change(self):
        mode = self.gui.mode.get()
        
        # if the mode changes
        if mode != self.mode:
            self.mode = mode
            
            self._set_title()
            
            if self.is_insert_mode():
                if self.db_widgets:
                    self.gui.hide_alter_db_buttons()
                    
                if self.table_widgets:
                    self.gui.hide_alter_table_buttons()
                    self.gui.show_insert_table_buttons()
                    
                    self.gui.show_insert_table_widgets()
                    
                if self.column_widgets:
                    self.gui.hide_alter_column_buttons()
                    self.gui.show_insert_column_buttons()
                    
                if self.value_widgets:
                    self.gui.hide_search_widgets()
                    self.gui.search_ent.hide_value_list()
                    self.gui.hide_alter_record_buttons()
                    
                    self.gui.show_insert_record_buttons()
                        
                    self._check_alter_to_insert_value()
                    
                else:
                    # if a table a has been selected
                    if self.table_name:
                        self.gui.make_value_widgets()
                        self.value_widgets = True
                        
                        self.gui.make_row_value_widgets()
                        self.gui.show_insert_record_buttons()
                        
                if self.value_widgets and not self.insert_record_enabled:
                    self.gui.enable_insert_record_button()
                    
                    self.insert_record_enabled = True
            else:
                # if a database has been selected
                if self.db_name:
                    self.gui.show_alter_db_buttons()
                
                if self.table_widgets:
                    self.gui.hide_insert_table_buttons()
                    self.gui.show_alter_table_buttons()
                    
                    self.gui.hide_insert_table_widgets()
                    
                if self.column_widgets:
                    self.gui.hide_insert_coulmn_buttons()
                    self.gui.show_alter_column_buttons()
                    
                if self.value_widgets:
                    self.gui.hide_insert_record_buttons()
                    
                    self.gui.show_search_widgets()
                    self.gui.show_alter_record_buttons()
                    
                    self._check_insert_to_alter_value()
                    
            if self.value_widgets:
                self._set_record_label('')
                self.gui.match_count_label.config(text='')
        
                    
    def is_insert_mode(self):
        '''
            Returns whether the mode is set to "Insert" which is true
            if mode is 1, the other mode is 0.
        '''
        return bool(self.mode)
    
    
    def _check_insert_to_alter_value(self):
        primary_key_value = self.gui.value_vars[self.primary_key_index].get()
        
        if primary_key_value and self.column_name:
            values = self._fetch_row_values_by_column(primary_key_value)
            
            if values:
                self._set_value_widgets(values)
        

    def _check_alter_to_insert_value(self):
        value = self.gui.search_ent.get()
        
        if value and self.column_name:
            column_index = self.column_names.index(self.column_name)
            
            self._clear_value_widgets()
            
            # populates the entry for the selected column with the value 
            # from the search entry
            self.gui.value_vars[column_index].set(value)
                    
        
    def on_db_select(self, event):
        db_name = self.gui.db_cbo.get()
        
        if db_name != self.db_name:
            self.db_name = db_name
        
            self._set_backups()
            self._set_backup_widget()
            
            self._set_table_names()
            self._set_table_count_label()
            
            if not self.db_widgets and not self.is_insert_mode():
                self.gui.show_alter_db_buttons()
                
                self.db_widgets = True
            
            # if the table widgets have not been created
            if not self.table_widgets:
                self.gui.make_table_widgets()
                  
                self.table_widgets = True
                
                if self.is_insert_mode():
                    self.gui.show_insert_table_buttons()
                    
                    self.gui.show_insert_table_widgets()
                    
                else:
                    self.gui.show_alter_table_buttons()
                
            if self.column_widgets:
                self._config_ref_table_widget()
                
            if self.value_widgets:
                # deletes the value widgets
                self.gui.value_frm.destroy()
                  
            # indicates whether or not to clear the selected table 
            # based on whether it is already empty
            reset_table = bool(self.table_name)
             
            self._set_table_select_widget(clear_value=reset_table)
             
            self.gui.table_cbo.focus()
                
                
    def _set_backups(self):
        self.backups = {
            ntpath.basename(path) : path 
            for path in constants.BACKUP_DB_FOLDER.iterdir()
            if self.db_name in str(path)
            }
        
        
    def _set_backup_widget(self):
        values = sorted([name for name in self.backups], reverse=True)
        self.gui.backup_cbo.config(values=values)
        
        value = values[0] if values else ''
        self.gui.backup_cbo.set(value)
        
        
    def _set_table_names(self):
        table_names = utilities.get_table_names(self.db_name)
        table_names.sort()
        
        self.table_names = table_names
        
        
    def _set_table_select_widget(self, clear_value=False):
        if clear_value:
            # clears the value shown in the drop down
            self.gui.table_name.set('')
        
        self.gui.table_cbo.set_value_list(self.table_names)
        
        
    def _set_table_count_label(self):
        table_count = len(self.table_names)
        
        self.gui.table_count_lbl.config(text=f'{table_count} Tables')
        
        
    def on_backup_click(self):
        if self.db_name:
            db_path = constants.DB_PATHS[self.db_name]
              
            backup_name = time.strftime(f'{self.db_name}_%Y%m%d_%H%M%S.db')
            backup_path = constants.BACKUP_DB_FOLDER.joinpath(backup_name)
              
            progress_title = 'Backing Up Database'
              
            self.CopyDb = CopyDb(db_path, backup_path, progress_title)
             
            self.CopyDb.start()
            
        
    def on_restore_click(self):
        if self.db_name:
            restore_name = self.gui.backup_cbo.get()
            
            if restore_name:
                restore = msg.askyesno(
                    self.title, 
                    'Warning, this will replace the current database. Consider '
                    'creating a backup first. Would you like to continue?', 
                    parent=self.gui
                    )
                
                if restore:
                    restore_path = constants.BACKUP_DB_FOLDER.joinpath(
                        restore_name
                        )
                        
                    if restore_path.is_file():
                        current_path = constants.DB_PATHS[self.db_name]
                        
                        current_deleted = False
                    
                        try:
                            # remove the current database file
                            Path(current_path).unlink()
                            
                            current_deleted = True
                                
                        except PermissionError:
                            msg.showerror(
                                f'{constants.APP_NAME} - Restore Backup', 
                                f'Cannot restore ({restore_name}) at this '
                                'time because the current file is being '
                                'used.', 
                                parent=self.gui
                                )
                            
                        if current_deleted:
                            restore_path = str(restore_path)
                            
                            progress_title = 'Restoring Database'
                                   
                            self.CopyDb = CopyDb(
                                restore_path, current_path, progress_title)
                               
                            self.CopyDb.start()
            else:
                msg.showinfo(
                    self.title, 'Select a backup file to restore.', 
                    parent=self.gui
                    )
                
                
    def table_postcommand(self):
        self._set_table_names()
        
        self._set_table_select_widget()
                
        
    def on_table_change(self, *args):
        table_name = self.gui.table_name.get()
        
        if table_name != self.table_name:
            if table_name in self.table_names:
                self.table_name = table_name
            
                self._set_table_data()
                
                self._set_table_size_label(
                    f'{self.row_count:,} Rows x {self.column_count:,} Columns'
                    )
               
                if not self.column_widgets:
                    self.gui.make_column_widgets()
                    
                    self.column_widgets = True
                    
                    self._config_ref_table_widget()
                    
                    if self.is_insert_mode():
                        self.gui.show_insert_column_buttons()
                        
                    else:
                        self.gui.show_alter_column_buttons()
                        
                if not self.alter_table_enabled:
                    self.gui.enable_alter_table_buttons()
                    self.alter_table_enabled = True
                    
                if not self.value_widgets and self.is_insert_mode():
                    self.gui.make_value_widgets()
                    self.value_widgets = True
                    
                    self.gui.show_insert_record_buttons()
                    
                if self.value_widgets:
                    self.gui.make_row_value_widgets()
                    
                    self._set_record_label('')
                    
                    if not self.insert_record_enabled:
                        self.gui.enable_insert_record_button()
                        self.insert_record_enabled = True
                    
            else:
                if self.alter_table_enabled:
                    self.gui.disable_alter_table_buttons()
                    self.alter_table_enabled = False
                    
                if self.value_widgets:
                    if self.insert_record_enabled:
                        self.gui.disable_insert_record_botton()
                        self.insert_record_enabled = False
                
                # resets the attributes of the table
                self.table_info = ''
                self.table_name = ''
                self.table_sql = ''
                self.columns = {}
                self.column_names = []
                self.foreign_keys = {}
                
                self.primary_key_index = None
               
                self._set_table_size_label()
                
        self._set_table_name_widget(table_name)
          
        if self.column_widgets:     
            # indicates whether or not to clear the selected column 
            # based on whether it is already empty and if the table 
            # is being renamed
            clear_value = bool(self.column_name) and not self.renaming_table
            
            self._set_column_select_widget(clear_value=clear_value)
            

    def _set_table_data(self):
        self._set_table_sql()
        self._set_foreign_keys()
        self._set_table_info()
        self._set_columns()
        self._set_column_names()
        self._set_value_label_len()
        
        self.column_count = len(self.columns)
        
        self._set_row_count()
        
        
    def _set_table_sql(self):
        '''
            Stores the SQL code used to create the table.
        '''
        query = '''
            SELECT sql 
            FROM sqlite_master 
            WHERE type='table' AND name=?
            '''
        
        results = utilities.execute_sql(
            sql_code=query, args=(self.table_name,), db_name=self.db_name
            )
        
        if results:
            self.table_sql = results[0]
        
            
    def _set_foreign_keys(self):
        '''
            Extracts any references to other tables from the SQL code used 
            to create the table. Stores them in a dictionary with the column
            as the key and the reference table and column as the value in 
            a namedtuple.
        '''
        foreign_keys = [
            match for match in 
            re.findall(self.foreign_key_pattern, self.table_sql)
            ]
        
        self.foreign_keys = {
            self._get_foreign_key_column_name(foreign_key) :
            self._get_foreign_key_reference_names(foreign_key)
            for foreign_key in foreign_keys
            }
        
        
    def _get_foreign_key_column_name(self, foreign_key):
        '''
            Returns the name of the foreign key column which is extracted 
            from the foreign_key SQL code that defined the FOREIGN KEY.
        '''
        return re.search(
            self.between_parenthesis_pattern, foreign_key.split('REFERENCES')[0]
            ).group(1)
        
        
    def _get_foreign_key_reference_names(self, foreign_key):
        '''
            Returns a namedtuple with the names of the reference table
            and the reference column which are extracted from the 
            foreign_key SQL code that defined the FOREIGN KEY.
        '''
        names = foreign_key.split('REFERENCES')[1].strip().split('(')
        
        table_name = names[0]
        column_name = names[1].replace(')', '')
        
        return Reference(ref_table=table_name, ref_column=column_name)
        
        
    def _set_table_info(self):
        '''
            Stores the schema of the selected table. Table info returns
            a tuple for each column with the following information
            for each column: index, name, data type, whether or not 
            it can be not null, the default value of the column and 
            whether or not it is part of the primary key for the table.
        '''
        '''
            TODO can maybe make this into a function in the utilities module
            just to get the column names if the table info is not used in any 
            other places
        '''
        query = f'PRAGMA table_info({self.table_name})'
        
        self.table_info = utilities.execute_sql(
            sql_code=query, db_name=self.db_name, fetchall=True
            )
        
        
    def _set_columns(self):
        self.columns = {}
        self.primary_key_index = None
        
        for i, info in enumerate(self.table_info):
            name = info[1]
            data_type = info[2]
            primary_key = info[5]
            
            constraint = ''
            ref_table = ''
            ref_column = ''
                
            constraint = self._get_column_constraint(name, data_type)
            
            is_foreing_key = self._is_foreign_key(name)
            
            if is_foreing_key:
                foreign_key = self.foreign_keys[name]
                
                ref_table = foreign_key.ref_table
                ref_column = foreign_key.ref_column
                
            if primary_key:
                self.primary_key_index = i
                
            self.columns[name] = Column(
                index=info[0], name=name, data_type=data_type,
                not_null=info[3], default=info[4], primary_key=primary_key,
                constraint=constraint, ref_table=ref_table, 
                ref_column=ref_column, 
                is_foreign_key=is_foreing_key
                )
            
            
    def _get_column_constraint(self, column_name, data_type):
        '''
            Returns the constraint for the given column from the table
            schema if any exist and an empty string if none exist.
        '''
        # pattern to match strings in between the column name followed
        # by the data type and either a comma or closing parenthesis
        constraint_pattern = re.compile(
            f'{column_name} {data_type} (.+?)[,\)]'
            )
        
        constraint = ''
        
        match = re.search(constraint_pattern, self.table_sql)
        
        # if a match is found
        if match:
            # remove "NOT NULL", that will be included in the table info
            constraint = match.group(1).replace('NOT NULL', '').strip()
        
        return constraint
    
    
    def _is_foreign_key(self, column_name):
        '''
            Returns TRUE if column is in the dictionary of foreign keys.  
        '''
        return column_name in self.foreign_keys
    
    
    def _set_row_count(self):
        sql_function = (
            'count(*)' if self._primary_key_is_integer() else 'max(rowid)'
            )
        
        # gets the number of rows in the table, this query will work 
        # unless the table is explicitly created without a row id.
        query = f'''
            SELECT {sql_function} 
            FROM {self.table_name}
            '''
        
        results = utilities.execute_sql(sql_code=query, db_name=self.db_name)
        
        if results:
            row_count = results[0]
        
        # if there are no rows in the table then None will be returned
        self.row_count = row_count if row_count else 0
    
    
    def _primary_key_is_integer(self):
        return any(
            column.primary_key and column.data_type.lower() == 'integer'
            for column in self.columns.values()
            )
    
    
    def _set_table_size_label(self, text=''):
        self.gui.table_size_lbl.config(text=text)
        
        
    def _set_table_name_widget(self, value=''):
        self.gui.new_table_name.set(value)
        
        
    def _config_ref_table_widget(self):
        # all the table names of the selected database minus the name of 
        # the selected table
        values = [name for name in self.table_names if name != self.table_name]
        
        self.gui.ref_table_cbo.config(values=values)
        
        
    def _config_ref_column_widget(self, values):
        self.gui.ref_column_cbo.config(values=values)
    
    
    def _set_column_names(self):
        self.column_names = list(self.columns.keys())
       
        
    def _set_value_label_len(self):
        max_len = 0
        
        for column in self.columns.values():
            col_len = len(column.name) + len(column.data_type)
            
            if col_len > max_len:
                max_len = col_len
                
        self.value_label_len = int(max_len * .9)
        
        
    def _set_column_select_widget(self, clear_value=False):
        if clear_value:
            self.gui.column_name.set('')
        
        self.gui.column_cbo.set_value_list(sorted(self.column_names))
        
        
    def on_copy_click(self):
        new_table = self.gui.new_table_name.get()
    
        if new_table:
            # copies the table in another thread
            thread = threading.Thread(target=self._copy_table, args=(new_table, ))
            thread.deamon = True
            thread.start()  
                
                
    def _copy_table(self, new_table):
        loading_circle = progress.LoadingCircle(self.gui, 'Copying')
        loading_circle.start()
        
        columns_string = ','.join(self.column_names)
        
        script = f'''
            {self.table_sql.replace(self.table_name, new_table)};
            
            INSERT INTO {new_table} ({columns_string})
                SELECT {columns_string}
                
                FROM {self.table_name};
            '''
             
        copied = utilities.execute_sql(
            sql_code=script, db_name=self.db_name, dml=True, script=True,
            gui=self.gui
            )
            
        if copied:
            self._set_table_names()
              
            self._set_table_select_widget()
              
            # resets the table name entry to the name of table selected
            self._set_table_name_widget(self.table_name)
              
            msg.showinfo(
                self.title, 
                f'Copy of ({self.table_name}) created as ({new_table}).',
                parent=self.gui
                )
             
        loading_circle.end()
                
                
    def on_export_click(self):
        export_type = self.gui.export_type.get()
        
        extension = self.export_types[export_type]
        
        if (
            export_type == 2 and 
            self.row_count > constants.MAX_EXPORT_RECORDS_EXCEL
            ):
            msg.showinfo(
                self.title, 
                'Table ({}) exceeds the max of ({:,}) records allowed '
                'for exporting to ({}) with ({:,}).'.format(
                    self.table_name, constants.MAX_EXPORT_RECORDS_EXCEL, 
                    extension, self.row_count
                    ),
                parent=self.gui
                )
            
        else:
            # exports the table in another thread
            thread = threading.Thread(
                target=self._export_table, args=(export_type, extension)
                )
            
            thread.daemon = True                           
            thread.start()
            

    def _export_table(self, export_type, extension): 
        loading_circle = progress.LoadingCircle(
            parent=self.gui, text='Exporting'
            )
        
        loading_circle.start()
                  
        df = self._get_table_dataframe()
        
        header = list(df)
        
        path = self._get_export_path(extension)
        
        # if the export type is 0 for csv
        if not export_type:
            df.to_csv(
                path, header=header, index=None, sep=',', mode='a'
            )
              
        else:
            data = df.values.tolist()
            
            data.insert(0, header)
            
            # 1 for txt or 2 for xlsx
            if export_type == 1:
                np.savetxt(path, data, fmt='%s')
                  
            else:
                wb = Workbook()
                wb.new_sheet('Data', data=data)
                    
                wb.save(path)
                
        loading_circle.end()
                
        utilities.open_file(path)
        

    def _get_export_path(self, extension):
        name = f'{self.table_name}.{extension.lower()}'
        path = constants.TEMP_FILE_PATH.joinpath(name)
        
        while path.is_file():
            name = str(path).rsplit('.', 1)[0]
            
            version = self._get_version(name)
            
            if version:
                name = name.replace(version, '').strip()
                
                version = int(re.sub(r'\(|\)', '', version)) + 1
                
            else:
                version = 1
                
            path = Path(f'{name} ({version}).{extension}')
               
        return path
    
    
    def _get_version(self, file_name):
        '''
            Returns the version of the file path if one is found. The 
            version is represented as an integer surrounded by parenthesis.
        '''
        match = self.version_pattern.search(file_name)
        
        if match:
            return match.group()
                    
                    
    def _get_table_dataframe(self):
        query = f'SELECT * FROM {self.table_name}'
        
        # connect to the database for the table in read only mode
        con = sql.connect(
            constants.DB_PATHS[self.db_name], timeout=constants.DB_TIMEOUT,
            uri=True
            )
         
        with con:
            df = pd.read_sql(query, con)
             
        con.close()
        
        return df
    

    def on_delete_table_click(self):
        '''
            Deletes a table from the database if the table is not in the
            dictionary of protected tables.
        '''
        if self._is_protected_table():
            msg.showinfo(
                self.title, 
                f'Table ({self.table_name}) is protected and cannot '
                'be deleted.', 
                parent=self.gui)
        else:
            delete = msg.askyesno(
                self.title, 
                'Are you sure?\n\nThis will permanently delete table '
                f'({self.table_name}) from database ({self.db_name}). '
                f'Consider backing up ({self.db_name}) first.',
                parent=self.gui
                )
            
            if delete:
                # deletes the table in another thread
                thread = threading.Thread(target=self._delete_table)
                thread.deamon = True
                thread.start()
                
                    
                    
    def _delete_table(self):
        loading_circle = progress.LoadingCircle(self.gui, 'Deleting')
        loading_circle.start()
        
        sql_code = f'DROP TABLE IF EXISTS {self.table_name};'
                 
        executed = utilities.execute_sql(
            sql_code=sql_code, db_name=self.db_name, dml=True, 
            gui=self.gui
            )
             
        if executed:
            deleted_name = self.table_name
            
            self._set_table_names()
            
            # clears the value in the table select which will 
            # trigger the table change that will reset the column 
            # widgets
            self._set_table_select_widget(clear_value=True)
            
            self._set_table_count_label()
        
            msg.showinfo(
                self.title, f'Table ({deleted_name}) was deleted.',
                parent=self.gui
                )
            
        loading_circle.end()
                
                
    def _is_protected_table(self):
        return self.table_name in constants.PROTECTED_TABLES[self.db_name]
    
    
    def on_external_table_click(self):
        path = filedialog.askopenfilename(parent=self.gui)
        
        if path:
            extension = path.rsplit('.', 1)[1]
            
            if extension in self.import_table_types:
                # tries to load the file in another thread
                thread = threading.Thread(
                    target=self._load_new_table_df, args=(path, extension)
                    )
                
                thread.daemon = True                           
                thread.start()
                       
            else:
                msg.showinfo(
                    self.title, 
                    'File type not supported. Supported file types are: '
                    f'{self.import_table_types}.'
                    , parent=self.gui
                    )
                
                
    def _load_new_table_df(self, path, extension):
        try:
            if extension == 'csv':
                self.new_table_df = pd.read_csv(
                    path, encoding='utf-8', dtype=str
                    )
            
            else:
                self.new_table_df = pd.read_excel(path, dtype=str)
                
        except (ParserError, UnicodeDecodeError) as e:
            msg.showerror(
                self.title, f'{e} occurred when trying to load {path}.'
                )
            
        if not self.new_table_df is None:
            file_name = ntpath.basename(path).rsplit('.', 1)[0]
            self.gui.new_table_name.set(file_name)
            
            column_names = list(self.new_table_df)
            column_count = len(column_names)
            
            self.gui.column_count_cbo.set(column_count)
            
            # shows the column names in each of the entry widgets that 
            # were created when the was column count was set
            for i, name in enumerate(column_names):
                self.gui.new_table_column_vars[i].set(name)
                
            row_count = len(self.new_table_df)
            
            self.gui.row_count_lbl.config(text='{:,}'.format(row_count))
    
    
    def on_insert_table_click(self):
        table_name = self.gui.new_table_name.get()
        
        if table_name:
            table_name = table_name.replace(' ', '_')
            
            column_names = [var.get() for var in self.gui.new_table_column_vars]
            
            # if any of the column names are blank or numbers
            if any(not name or name.isdigit() for name in column_names):
                msg.showinfo(
                    self.title, 
                    'Please enter a valid name for each column of table '
                    f'({table_name}). Column names cannot begin with a number.',
                    parent=self.gui
                    )
            else:
                created = False
                
                if not self.new_table_df is None:
                    con = sql.connect(
                        constants.DB_PATHS[self.db_name], timeout=constants.DB_TIMEOUT
                        )
                    
                    try:
                        with con:
                            self.new_table_df.to_sql(
                                name=table_name, con=con, index=False
                                )
                        
                        created = True
                        
                    except ValueError:
                        msg.showerror(
                            self.title, 
                            f'Table ({table_name}) already exists in '
                            f'({self.db_name}).', 
                            parent=self.gui
                            )
                        
                    con.close()
                    
                else:
                    column_string = ' text, '.join(column_names) + ' text'
                    
                    sql_code = f'CREATE TABLE {table_name} ({column_string})'
                    
                    created = utilities.execute_sql(
                        sql_code=sql_code, db_name=self.db_name, dml=True, 
                        gui=self.gui
                        )
                    
                if created:
                    self.new_table_df = None
                    
                    self._set_table_names()
                    
                    self._set_table_select_widget()
                    
                    self.gui.table_name.set(table_name)
                    
                    self._set_table_count_label()
                    
                    msg.showinfo(
                        self.title, 
                        f'Table ({table_name}) was created in ({self.db_name}).',
                        parent=self.gui
                        )
                
        else:
            msg.showinfo(
                self.title, 'Enter a name for the new table.', parent=self.gui
                )
        

    def on_rename_click(self):
        '''
            Renames a table if a new non conflicting name is provided and 
            the table is not in the dictionary of protected tables.
        '''
        new_name = self.gui.new_table_name.get()
        
        if new_name and new_name != self.table_name:
            new_name = new_name.replace(' ', '_')
            
            if self._is_protected_table():
                msg.showinfo(
                    self.title, 
                    f'Table ({self.table_name}) is protected '
                    'and cannot be renamed.',
                    parent=self.gui
                    )
            else:
                sql_code = f'''
                    ALTER TABLE {self.table_name} 
                    RENAME TO {new_name}
                    '''
                 
                renamed = utilities.execute_sql(
                    sql_code=sql_code, db_name=self.db_name, dml=True, 
                    gui=self.gui
                    )
         
                if renamed:
                    old_name = self.table_name
                    
                    self._set_table_names()
                
                    self._set_table_select_widget()
                    
                    # temporarily sets the renaming flag to true so
                    # that the column widgets don't get reset when the 
                    # table widgets change
                    self.renaming_table = True
                    
                    self.gui.table_name.set(new_name)
                    
                    self.renaming_table = False
                
                    msg.showinfo(
                        self.title, 
                        f'Table ({old_name}) renamed to ({new_name}).',
                        parent=self.gui
                        )
        else:
            msg.showerror(
                self.title, 
                f'Enter a new name for table ({self.table_name}).', 
                parent=self.gui
                )

                
    def on_column_change(self, *args):
        column_name = self.gui.column_name.get()
        
        data_type = ''
        constraint = ''
        not_null = 0
        ref_table = ''
        ref_column = ''
        
        if column_name != self.column_name:
            if column_name in self.column_names:
                self.column_name = column_name
                
                Column = self.columns[self.column_name]
                
                data_type = Column.data_type
                constraint = Column.constraint
                not_null = Column.not_null
                ref_table = Column.ref_table
                ref_column = Column.ref_column
                
                self.gui.ref_table_cbo.set('')
                self.gui.ref_column_cbo.set('')
                
                if not self.alter_column_enabled:
                    self.gui.enable_alter_column_buttons()
                    self.alter_column_enabled = True
                    
                if not self.value_widgets:
                    self.gui.make_value_widgets()
                    
                    self.value_widgets = True
                    
                    if self.is_insert_mode():
                        self.gui.show_insert_record_buttons()
                        
                    else:
                        self.gui.show_search_widgets()
                        self.gui.show_alter_record_buttons()
                        
                    self.gui.make_row_value_widgets()
                
                if not self.alter_record_enabled:
                    self.gui.enable_alter_record_buttons()
                    self.alter_record_enabled = True
                    
                if not self.search_enabled:
                    self.gui.enable_search_button()
                    self.search_enabled = True
                
            else:
                if self.alter_column_enabled:
                    self.gui.disable_alter_column_buttons()
                    self.alter_column_enabled = False
                    
                if self.alter_record_enabled:
                    self.gui.disable_alter_record_buttons()
                    self.alter_record_enabled = False
                    
                if self.search_enabled:
                    self.gui.disable_search_button()
                    self.search_enabled = False
                
                # resets the attributes of the column
                self.column_name = ''
                
        self._set_column_name_widget(column_name)
        
        self.gui.type_cbo.set(data_type)
        self.gui.constraint_cbo.set(constraint)
        self.gui.not_null_state.set(not_null)
        self.gui.ref_table_cbo.set(ref_table)
        self.gui.ref_column_cbo.set(ref_column)
        
        if self.value_widgets:
            # destroys the pop up list if one is showing
            self.gui.search_ent.hide_value_list()
            
            self._set_record_label('')
            self.gui.match_count_label.config(text='')
        

    def _set_column_name_widget(self, value=''):
        self.gui.new_column_name.set(value)
        
        
    def on_ref_table_select(self, event):
        ref_table = self.gui.ref_table_cbo.get()
        
        ref_columns = utilities.get_column_names(self.db_name, ref_table)
        
        self._config_ref_column_widget(ref_columns)
        
        
    def on_delete_column_click(self):
        print('delete the column if not protected')
        
        
    def on_insert_column_click(self):
        print('in on insert column')
        
        
    def on_update_column_click(self):
        print('rename, change type or constraint will be done here')
            
            
    def on_search_click(self, event=None):
        if self.column_name:
            # hides the value list if it was already showing from previous search
            self.gui.search_ent.hide_value_list()
            
            value = self.gui.search_ent.get().strip()
             
            if value:
                # searches for the value in another thread
                thread = threading.Thread(
                    target=self._search, args=(value, )
                    )
                 
                thread.daemon = True                           
                thread.start()
                
        else:
            msg.showinfo(
                self.title, 'Please select a column first.', parent=self.gui
                )
            
            self.gui.column_cbo.focus()
                
                
    def _search(self, value):
        loading_circle = progress.LoadingCircle(
            parent=self.gui, text='Searching'
            )
        
        loading_circle.start()
        
        matches = []
        
        query = f'''
            SELECT rowid, {self.column_name} 
            FROM {self.table_name} 
            WHERE {self.column_name} LIKE "{value}%"
            '''
       
        results = utilities.execute_sql(
            sql_code=query, db_name=self.db_name, fetchall=True
            )
        
        loading_circle.end()
        
        if results:
            matches = [f'{value} [r{rowid}]' for rowid, value in results]
            
        match_count = len(matches)
        self._set_match_count_label(match_count)
        
        if match_count == 1:
            self.on_search_match(matches[0])
            
        else:
            self.gui.search_ent.set_value_list(matches)
    
    
    def _set_match_count_label(self, match_count):
        text = '{:,} Match'.format(match_count)
        
        if match_count != 1:
            text += 'es'
      
        self.gui.match_count_label.config(text=text)
        
        
    def on_search_match(self, value=''):
        if not value:
            # gets the value form the entry which has the rowid in square 
            # brackets to the right of the value
            value = self.gui.search_ent.get()
        
        parts = value.split('[')
        value = parts[0].strip()
        
        # removes the "r" that indicates its a row number and the closing 
        # square bracket
        row_id = int(parts[1].replace('r', '').replace(']', ''))
        
        self.gui.search_ent.set(value)
        
        values = self._fetch_row_values_by_row_id(row_id)
        
        if values:
            self._set_value_widgets(values)
        
        
    def _fetch_row_values_by_row_id(self, row_id):
        '''
            Returns a tuple with all the values from the selected table
            where the row id is equal to the row id of the value that 
            was selected when searching.
        '''
        query = f'''
            SELECT * 
            FROM {self.table_name}
            WHERE rowid=?
            '''
        
        values = utilities.execute_sql(
            sql_code=query, args=(row_id, ), db_name=self.db_name
            )
           
        return values
    
    
    def _fetch_row_values_by_column(self, value):
        query = f'''
            SELECT *
            FROM {self.table_name}
            WHERE {self.column_name}=?
            '''
        
        values = utilities.execute_sql(
            sql_code=query, args=(value, ), db_name=self.db_name
            )
        
        return values
        
        
    def _set_value_widgets(self, values):
        for i, column in enumerate(self.columns.values()):
            value = values[i]
            
            if value and column.is_foreign_key:
                foreign_value = self._fetch_foreign_value(column.name, value)
                
                if foreign_value:
                    value = f'{value} : {foreign_value}'
          
            self.gui.value_vars[i].set(value)
                
                
    def _fetch_foreign_value(self, column_name, value):
        reference = self.foreign_keys[column_name]
        
        query = f'''
            SELECT name
            FROM {reference.ref_table}
            WHERE {reference.ref_column}=?
            '''
        
        foreign_value = ''
        
        # does not show the error if the reference table does not have 
        # a column named "name"
        results = utilities.execute_sql(
            sql_code=query, args=(value,), db_name=self.db_name, 
            show_error=False
            )
        
        if results:
            foreign_value = results[0]
        
        return foreign_value
                  

    def get_foreign_values(self, column_name):
        '''
            Returns a list of strings for each foreign key consisting 
            of the reference column value and the value of column 
            name in the reference table if one exists separated by a colon.
        '''
        foreign_key = self.foreign_keys[column_name]
        ref_table = foreign_key.ref_table
    
        query = f'SELECT id, name FROM {ref_table}'
        
        results = utilities.execute_sql(
            sql_code=query, db_name=self.db_name, fetchall=True
            )
        
        values = []
        
        if results:
            values = [f'{i[0]} {constants.FOREIGN_KEY_SEPARATOR} {i[1]}' for i in results]
                
        return values
        
        
    def get_value_options(self, column_name):
        '''
            Returns a list of strings for each foreign key id consisting 
            of the id and the name of that record separated by a colon.
        '''
        foreign_key = self.foreign_keys[column_name]
        ref_table = foreign_key.ref_table
    
        query = f'SELECT id, name FROM {ref_table}'
        
        value_options = []
        
        results = utilities.execute_sql(
            sql_code=query, db_name=self.db_name, fetchall=True
            )
        
        if results:
            value_options = [f'{i[0]} : {i[1]}' for i in results]
                
        return value_options
    
    
    def on_update_record_click(self):
        if not self.primary_key_index is None:
            key_value = self.gui.value_vars[self.primary_key_index].get()
            
            if key_value:
                key_column = self.column_names[self.primary_key_index]
                
                values = self._get_values()
                
                self._remove_foreign_key_values(values)
                
                # adds the primary key value to the list of arguments
                values.append(key_value)
                
                sql_code = f'''
                    UPDATE {self.table_name}
                    SET {",".join(f"{i}=?" for i in self.column_names)}
                    WHERE {key_column}=?
                    '''
                
                updated = utilities.execute_sql(
                    sql_code=sql_code, args=values, db_name=self.db_name, 
                    dml=True, gui=self.gui
                    )
                     
                if updated:
                    self._set_record_label(f'{key_value} updated.')
                    
        else:
            self._show_primary_key_message()
        
        
    def on_delete_record_click(self):
        if not self.primary_key_index is None:
            key_value = self.gui.value_vars[self.primary_key_index].get()
            
            if key_value:
                # removes the foreign key value if it has one
                key_value = key_value.split(
                    constants.FOREIGN_KEY_SEPARATOR
                    )[0].strip()
                
                key_column = self.column_names[self.primary_key_index]
                
                sql_code = f'''
                    DELETE FROM {self.table_name} 
                    WHERE {key_column}=?
                    '''
                  
                deleted = utilities.execute_sql(
                    sql_code=sql_code, args=(key_value, ),
                    db_name=self.db_name, dml=True, gui=self.gui
                    )
                   
                if deleted:
                    self._set_record_label(f'{key_value} deleted.')
                    
        else:
            self._show_primary_key_message()
        
        
    def on_insert_record_click(self):
        values = self._get_values()
        self._remove_foreign_key_values(values)
      
        sql_code = '''
            INSERT INTO {} ({})
            VALUES ({})
            '''.format(
                self.table_name, ','.join(self.column_names),
                ','.join('?' for _ in range(len(self.column_names)))
                )
        
        inserted = utilities.execute_sql(
            sql_code=sql_code, args=values, db_name=self.db_name, 
            dml=True, gui=self.gui
            )

        if inserted:
            value = (
                values[0] if self.primary_key_index is None
                else values[self.primary_key_index]
                )
            
            self._set_record_label(f'{value} inserted.')
            
            
    def on_column_count_change(self, *args):
        new_table_column_count = self.gui.new_table_column_count.get()
        
        if new_table_column_count != self.new_table_column_count:
            self.new_table_column_count = new_table_column_count
            self.gui.make_new_table_column_widgets()
            

    def _get_values(self):
        values = []
        
        for var in self.gui.value_vars:
            value = str(var.get()).replace('\n', '').strip()
            
            #values.append(value if value else None)
            values.append(value)
            
        return values
        
        
    def _remove_foreign_key_values(self, values):
        '''
            Removes any foreign key values that were displayed to the user 
            and only leaves the id foreign key.
        '''
        for i, value in enumerate(values):
            column_name = self.column_names[i]
            column = self.columns[column_name]
            
            if column.is_foreign_key:
                if value and constants.FOREIGN_KEY_SEPARATOR in value:
                    values[i] = value.split(
                        constants.FOREIGN_KEY_SEPARATOR
                        )[0].strip()
                    
                    
    def _show_primary_key_message(self):
        msg.showinfo(
            self.title, 
            f'Please create a primary key for table ({self.table_name}) '
            'in order to uniquely identify the record you are attempting '
            'to alter.',
            parent=self.gui
            )
        
        
    def _set_record_label(self, text):
        self.gui.record_label.config(text=text)
        
          
    def _clear_value_widgets(self):
        for var in self.gui.value_vars:
            var.set('')
            
            
    def check_id_column_tooltip(self, parent):
        # if a tooltip already exists
        if self.id_column_tooltip:
            self.gui.id_column_tooltip.delete()
            
        if self.db_name in constants.ID_COLUMN_TOOLTIPS:
            if self.table_name in constants.ID_COLUMN_TOOLTIPS[self.db_name]:
                message = constants.ID_COLUMN_TOOLTIPS[self.db_name][self.table_name]
                
                self.gui.id_column_tooltip = self.gui.create_tooltip(
                    parent, message
                    )
                
                
    def on_db_separator_drag(self, event, section):
        increment = 1
        
        if self._drag_started(event.x) and not self.dragging:
            self.dragging = True
            
        else:
            if event.x > self.mouse_x:
                if section == 'database':
                    if self.db_cbo_width + increment <= self.MAX_CBO_WIDTH:
                        self.db_cbo_width += increment
                        
                elif section == 'table':
                    if self.table_cbo_width + increment <= self.MAX_CBO_WIDTH:
                        self.table_cbo_width += increment
                        self.table_ent_width += increment
                
                elif section == 'column':
                    self.column_cbo_width += increment
                    self.column_ent_width += increment
        
            else:
                if section == 'database':
                    if self.db_cbo_width - increment >= self.MIN_CBO_WIDTH:
                        self.db_cbo_width -= increment
                        
                elif section == 'table':
                    if self.table_cbo_width - increment >= self.MIN_CBO_WIDTH:
                        self.table_cbo_width -= increment
                        self.table_ent_width -= increment
                
                elif section == 'column':
                    self.column_cbo_width -= increment
                    self.column_ent_width -= increment
                
            self.mouse_x = event.x
            
            if section == 'database':
                self.gui.db_cbo.config(width=self.db_cbo_width)
                self.gui.backup_cbo.config(width=self.db_cbo_width)
                
            elif section == 'table':
                self.gui.table_cbo.config(width=self.table_cbo_width)
                self.gui.new_table_name_ent.config(width=self.table_ent_width)
                   
            elif section == 'column':
                self.gui.column_cbo.config(width=self.column_cbo_width)
                self.gui.new_column_name_ent.config(width=self.column_ent_width)
                self.gui.type_cbo.config(width=self.column_cbo_width)
                self.gui.constraint_cbo.config(width=self.column_cbo_width)
                self.gui.ref_table_cbo.config(width=self.column_cbo_width)
                self.gui.ref_column_cbo.config(width=self.column_cbo_width)
                

    def _drag_started(self, x):
        return -3 < x < 3
            
            
    def on_db_separator_release(self, event):
        self.mouse_x = 0
        self.dragging = False
        
        utilities.set_default(
            'db_cbo_width', self.user_id, self.db_cbo_width
            )
        
        utilities.set_default(
            'table_cbo_width', self.user_id, self.table_cbo_width
            )
        
        utilities.set_default(
            'column_cbo_width', self.user_id, self.column_cbo_width
            )
        

class View(tk.Toplevel):
    '''
    '''
    
    
    CBO_WIDTH = 40
    ENT_WIDTH = CBO_WIDTH + 10
    HEIGHT = 460
    WIDTH = 1640
    
    
    def __init__(self, controller):
        super().__init__()
        
        self.controller = controller
        
        self.alter_column_buttons = []
        self.alter_record_buttons = []
        self.alter_table_buttons = []
        
        self.new_table_column_vars = []
        self.value_vars = []
        
        self.new_table_columns_frm = None
        self.value_frm = None
        
        self.column_tooltip = None
        self.db_tooltip = None
        self.id_column_tooltip = None
        self.table_tooltip = None
        
        self.column_name = tk.StringVar()
        self.column_name.trace('w', self.controller.on_column_change)
        
        self.new_column_name = tk.StringVar()
        self.new_table_name = tk.StringVar()
        
        self.search_value = tk.StringVar()
        
        self.table_name = tk.StringVar()
        self.table_name.trace('w', self.controller.on_table_change)
        
        # 0 for csv, 1 for txt, 2 for xlsx
        self.export_type = tk.IntVar(value=self.controller.DEFAULT_EXPORT_TYPE)
        self.mode = tk.IntVar(value=self.controller.mode)
        self.not_null_state = tk.IntVar()
        
        self.new_table_column_count = tk.IntVar()
        
        self.new_table_column_count.trace(
            'w', self.controller.on_column_count_change
            )
        
        bold_style = ttk.Style()
        bold_style.configure('bold.TLabel', font=('Arial', '8', 'bold'))
        
        self.config(menu=Menu(self))
        
        self._set_main_frames()
        
        self._make_frame_tooltips()
        
        self._make_db_widgets()
        
        self.db_cbo.focus()
        
        
    def _set_main_frames(self):
        main_frm = ttk.Frame(self)
        
        left_frm = ttk.Frame(main_frm)
        right_frm = ttk.Frame(main_frm)
        
        self.frm_one = ttk.Frame(left_frm)
        self.frm_two = ttk.Frame(left_frm)
        self.frm_three = ttk.Frame(right_frm)
        self.frm_four = ttk.Frame(right_frm)
        
        main_frm.pack(
            fill='both', expand=1, padx=constants.OUT_PAD, 
            pady=constants.OUT_PAD
            )
        
        left_frm.pack(fill='both', expand=1, side='left')
        right_frm.pack(fill='both', expand=1, side='right')
        
        self.frm_one.pack(fill='both', expand=1, side='left')
        self.frm_two.pack(fill='both', expand=1, side='right')
        
        self.frm_three.pack(fill='both', expand=1, side='left')
        self.frm_four.pack(fill='both', expand=1, side='right')
        
        
    def _make_frame_tooltips(self):
        self.db_tooltip = self.create_tooltip(
            self.frm_one, 'Select a database to view its tables.'
            )
        
        self.table_tooltip = self.create_tooltip(
            self.frm_two, 'Select a table to view its columns.'
            )
        
        self.column_tooltip = self.create_tooltip(
            self.frm_three, 'Select a column to view its values.'
            )
        self.db_tooltip = ToolTip(
            self.frm_one, 'Select a database to view its tables.'
            )
        
        
    def create_tooltip(self, parent, message):
        tooltip = ToolTip(parent, message)
        
        return tooltip
        
        
    def _window_setup(self, width_scale):
        x_offset = (
            self.winfo_screenwidth() - int(self.WIDTH * width_scale)
            ) // 2
        
        y_offset = (self.winfo_screenheight() - int(self.HEIGHT)) // 2
        
        self.geometry(f'+{x_offset}+{y_offset}')
        
        
    def _make_db_widgets(self):
        lbl_width = 9
        
        main_frm = ttk.Frame(self.frm_one)
        
        db_frm = ttk.Frame(main_frm)
        db_lbl = ttk.Label(db_frm, text='Database:', width=lbl_width)
        
        self.db_cbo = ttk.Combobox(
            db_frm, values=[name for name in constants.DB_NAMES], 
            state='readonly', width=self.controller.db_cbo_width
            )
        
        self.db_cbo.bind('<<ComboboxSelected>>', self.controller.on_db_select)
        
        backups_frm = ttk.Frame(main_frm)
        
        backups_lbl = ttk.Label(
            backups_frm, text='Backups:', width=lbl_width
            )
        
        self.backup_cbo = ttk.Combobox(
            backups_frm, takefocus=False, state='readonly', 
            width=self.controller.db_cbo_width
            )
        
        self.table_count_lbl = ttk.Label(main_frm)
        
        self.db_btn_frm = ttk.Frame(main_frm)
        
        backup_btn = ttk.Button(
            self.db_btn_frm, text='Backup', takefocus=False,
            command=self.controller.on_backup_click
            )
        
        restore_btn = ttk.Button(
            self.db_btn_frm, text='Restore', takefocus=False,
            command=self.controller.on_restore_click
            )
        
        main_frm.pack(anchor='n', expand=1, fill='both', side='left')
        
        db_frm.pack(fill='x')
        db_lbl.pack(side='left')
        self.db_cbo.pack()
        #self.db_cbo.pack(fill='x')
        
        backups_frm.pack(fill='x', pady=constants.OUT_PAD)
        backups_lbl.pack(side='left')
        self.backup_cbo.pack()
        #self.backup_cbo.pack(fill='x')
        
        self.table_count_lbl.pack(anchor='w')
        
        backup_btn.pack(side='left', padx=constants.OUT_PAD)
        restore_btn.pack()
        
        self._window_setup(.25)
        
        
    def show_alter_db_buttons(self):
        self.db_btn_frm.pack(anchor='e', side='bottom')
    
    
    def hide_alter_db_buttons(self):
        self.db_btn_frm.pack_forget()
        
        
    def _insert_vertical_separator(self, parent, section):
        separator = ttk.Separator(
            parent, cursor='sb_h_double_arrow', orient='vertical'
            )
        
        separator.pack(
            fill='y', padx=constants.OUT_PAD, side='left'
            )
        
        separator.bind(
            '<B1-Motion>', 
            lambda event:self.controller.on_db_separator_drag(event, section)
            )
        
        separator.bind(
            '<ButtonRelease>', self.controller.on_db_separator_release
            )
        
        self.create_tooltip(
            separator, f'Drag left or right to adjust width of {section} section.'
            )
        
        
    def make_table_widgets(self):
        lbl_width = 11
        
        self.db_tooltip.delete()
        
        self._insert_vertical_separator(self.frm_two, 'database')
        
        main_frm = ttk.Frame(self.frm_two)
         
        table_frm = ttk.Frame(main_frm)
        table_lbl = ttk.Label(table_frm, text='Table:', width=lbl_width)
        
        self.table_cbo = ComboboxAutoComplete(
            table_frm, postcommand=self.controller.table_postcommand,
            textvariable=self.table_name, height=25,
            width=self.controller.table_cbo_width
            )
        
        name_frm = ttk.Frame(main_frm)
        name_lbl = ttk.Label(name_frm, text='New Name:', width=lbl_width)
        
        self.new_table_name_ent = ttk.Entry(
            name_frm, takefocus=False, textvariable=self.new_table_name, 
            width=self.controller.table_ent_width
            )
        
        ToolTip(self.new_table_name_ent, 'Name for copying/renaming or new table.')
         
        self.table_size_lbl = ttk.Label(main_frm)
        
        self.new_table_frm = ttk.Frame(main_frm)
        
        separator = ttk.Separator(self.new_table_frm, orient='horizontal')
        
        column_count_frm = ttk.Frame(self.new_table_frm)
        
        column_count_lbl = ttk.Label(
            column_count_frm, text='Column Count:', width=14
            )
        
        self.column_count_cbo = ttk.Combobox(
            column_count_frm, justify='right', state='readonly', width=4,
            takefocus=False, textvariable=self.new_table_column_count,
            values=[i for i in range(1, self.controller.new_table_column_limit)]
            )
        
        row_count_frm = ttk.Frame(self.new_table_frm)
        row_count_lbl = ttk.Label(row_count_frm, text='Row Count:')
        self.row_count_lbl = ttk.Label(row_count_frm)
        
        table_button_frm = ttk.Frame(main_frm)
        
        left_table_button_frm = ttk.Frame(table_button_frm)
        right_table_button_frm = ttk.Frame(table_button_frm)
        
        self.copy_table_btn = ttk.Button(
            left_table_button_frm, text='Copy', takefocus=False,
            command=self.controller.on_copy_click
            )
        
        self.export_table_btn = ttk.Button(
            left_table_button_frm, text='Export', takefocus=False,
            command=self.controller.on_export_click
            )
        
        self.external_table_btn = ttk.Button(
            right_table_button_frm, text='External', takefocus=False,
            command=self.controller.on_external_table_click
            )
        
        self.delete_table_btn = ttk.Button(
            right_table_button_frm, text='Delete', takefocus=False,
            command=self.controller.on_delete_table_click
            )
        
        self.insert_table_btn = ttk.Button(
            right_table_button_frm, text='Insert', takefocus=False,
            command=self.controller.on_insert_table_click
            )
        
        self.rename_table_btn = ttk.Button(
            right_table_button_frm, text='Rename', takefocus=False,
            command=self.controller.on_rename_click
            )
        
        self.alter_table_buttons.append(self.copy_table_btn)
        self.alter_table_buttons.append(self.export_table_btn)
        self.alter_table_buttons.append(self.delete_table_btn)
        self.alter_table_buttons.append(self.rename_table_btn)
        
        self.disable_alter_table_buttons()
         
        main_frm.pack(anchor='n', expand=1, fill='both', side='right')
        
        table_frm.pack(fill='x')
        table_lbl.pack(side='left')
        self.table_cbo.pack()
        
        name_frm.pack(fill='x', pady=constants.OUT_PAD)
        name_lbl.pack(side='left')
        self.new_table_name_ent.pack()
        
        self.table_size_lbl.pack(anchor='w')
        
        table_button_frm.pack(anchor='e', side='bottom')
        left_table_button_frm.pack(side='left', padx=constants.OUT_PAD)
        right_table_button_frm.pack()
        
        separator.pack(fill='x', pady=constants.OUT_PAD)
        
        column_count_frm.pack(fill='x')
        column_count_lbl.pack(side='left')
        self.column_count_cbo.pack(anchor='e')
        
        row_count_frm.pack(fill='x')
        row_count_lbl.pack(side='left')
        self.row_count_lbl.pack(anchor='e')
        
        self._window_setup(.5)
        
        
    def make_new_table_column_widgets(self):
        if not self.new_table_columns_frm is None:
            self.new_table_columns_frm.destroy()
            
            self.new_table_column_vars = []
        
        self.new_table_columns_frm = ttk.Labelframe(
            self.new_table_frm, text='Column Names'
            )
        
        self.new_table_columns_frm.pack(fill='x', pady=constants.OUT_PAD)
        
        # inner frame for scroll region otherwise the label of the 
        # label frame moves with the scroll bar
        inner_frm = ttk.Frame(self.new_table_columns_frm)
        inner_frm.pack(fill='x')
        
        count = self.new_table_column_count.get()
        
        scroll = count >= constants.COUNT_FOR_SCROLLBAR
        
        label_frm = (
            FrameScroll(inner_frm) if scroll 
            else self.new_table_columns_frm
            )
        
        pad = False
        
        for i in range(1, count + 1):
            var = tk.StringVar()
            self.new_table_column_vars.append(var)
            
            frm = ttk.Frame(label_frm)
            lbl = ttk.Label(frm, text=f'Column_{i}:', width=11)
            
            ent = ttk.Entry(
                frm, textvariable=var, takefocus=False,
                width=self.controller.table_ent_width
                )
            
            pady = constants.IN_PAD if pad else 0
            pad = not pad
            
            frm.pack(fill='x', pady=pady)
            lbl.pack(side='left')
            ent.pack()
            
        if scroll:
            label_frm.update()
        
        
    def show_alter_table_buttons(self):
        self.copy_table_btn.pack(pady=constants.OUT_PAD)
        self.export_table_btn.pack()
        
        self.delete_table_btn.pack(pady=constants.OUT_PAD)
        self.rename_table_btn.pack()
    
    
    def hide_alter_table_buttons(self):
        self.copy_table_btn.pack_forget()
        self.export_table_btn.pack_forget()
        
        self.delete_table_btn.pack_forget()
        self.rename_table_btn.pack_forget()
    
    
    def show_insert_table_buttons(self):
        self.external_table_btn.pack(side='left', padx=constants.OUT_PAD)
        self.insert_table_btn.pack()
    
    
    def hide_insert_table_buttons(self):
        self.external_table_btn.pack_forget()
        self.insert_table_btn.pack_forget()
        
        
    def enable_alter_table_buttons(self):
        for button in self.alter_table_buttons:
            button.config(state='enabled')
            
            
    def disable_alter_table_buttons(self):
        for button in self.alter_table_buttons:
            button.config(state='disabled')
    
    
    def show_insert_table_widgets(self):
        self.new_table_frm.pack(fill='x')
        
        self.row_count_lbl.config(text=0)
        
        # sets the column count to the first item or 1 which will trigger
        # the callback that then creates the column widgets
        self.column_count_cbo.current(0)
    
    
    def hide_insert_table_widgets(self):
        self.new_table_frm.pack_forget()
        
        
    def make_column_widgets(self):
        lbl_width = 11
        
        self.table_tooltip.delete()
        
        self._insert_vertical_separator(self.frm_three, 'table')
        
        main_frm = ttk.Frame(self.frm_three)
        
        column_frm = ttk.Frame(main_frm)
        
        column_lbl = ttk.Label(
            column_frm, text='Column:', width=lbl_width
            )
        
        self.column_cbo = ComboboxAutoComplete(
            column_frm, textvariable=self.column_name, width=self.controller.column_cbo_width
            )
        
        name_frm = ttk.Frame(main_frm)
        name_lbl = ttk.Label(name_frm, text='New Name:', width=lbl_width)
        
        self.new_column_name_ent = ttk.Entry(
            name_frm, takefocus=False, textvariable=self.new_column_name, 
            width=self.controller.column_cbo_width
            )
        
        type_frm = ttk.Frame(main_frm)
        type_lbl = ttk.Label(type_frm, text='Type:', width=lbl_width)
        
        self.type_cbo = ttk.Combobox(
            type_frm, takefocus=False, state='readonly', 
            values=constants.DATA_TYPES, width=self.controller.column_cbo_width
            )
        
        constraint_frm = ttk.Frame(main_frm)
        
        constraint_lbl = ttk.Label(
            constraint_frm, text='Constraint:', width=lbl_width
            )
        
        self.constraint_cbo = ttk.Combobox(
            constraint_frm, state='readonly', values=constants.CONSTRAINTS,  
            takefocus=False, width=self.controller.column_cbo_width
            )
        
        ref_table_frm = ttk.Frame(main_frm)
        
        ref_table_lbl = ttk.Label(
            ref_table_frm, text='Ref Table:', width=lbl_width
            )
        
        self.ref_table_cbo = ttk.Combobox(
            ref_table_frm, state='readonly', takefocus=False,  
            width=self.controller.column_cbo_width
            )
        
        self.ref_table_cbo.bind(
            '<<ComboboxSelected>>', self.controller.on_ref_table_select
            )
        
        ref_column_frm = ttk.Frame(main_frm)
        
        ref_column_lbl = ttk.Label(
            ref_column_frm, text='Ref Column:', width=lbl_width
            )
        
        self.ref_column_cbo = ttk.Combobox(
            ref_column_frm, state='readonly', takefocus=False,
            width=self.controller.column_cbo_width
            )
        
        not_null_chk = ttk.Checkbutton(
            main_frm, takefocus=False, text='Not Null', 
            var=self.not_null_state
            )
        
        self.column_button_frm = ttk.Frame(main_frm)
        
        self.delete_column_btn = ttk.Button(
            self.column_button_frm, text='Delete', takefocus=False,
            command=self.controller.on_delete_column_click
            )
        
        self.insert_column_btn = ttk.Button(
            self.column_button_frm, text='Insert', takefocus=False,
            command=self.controller.on_insert_column_click
            )
        
        self.update_column_btn = ttk.Button(
            self.column_button_frm, text='Update', takefocus=False,
            command=self.controller.on_update_column_click
            )
        
        self.alter_column_buttons.append(self.delete_column_btn)
        self.alter_column_buttons.append(self.update_column_btn)
        
        self.disable_alter_column_buttons()
        
        main_frm.pack(anchor='n', expand=1, fill='both', side='right')
        
        column_frm.pack(fill='x')
        column_lbl.pack(side='left')
        self.column_cbo.pack(fill='x')
        
        name_frm.pack(fill='x', pady=constants.OUT_PAD)
        name_lbl.pack(side='left')
        self.new_column_name_ent.pack(fill='x')
        
        type_frm.pack(fill='x')
        type_lbl.pack(side='left')
        self.type_cbo.pack(fill='x')
        
        constraint_frm.pack(fill='x', pady=constants.OUT_PAD)
        constraint_lbl.pack(side='left')
        self.constraint_cbo.pack(fill='x')
        
        ref_table_frm.pack(fill='x')
        ref_table_lbl.pack(side='left')
        self.ref_table_cbo.pack(fill='x')
        
        ref_column_frm.pack(fill='x', pady=constants.OUT_PAD)
        ref_column_lbl.pack(side='left')
        self.ref_column_cbo.pack(fill='x')
        
        not_null_chk.pack(anchor='w')
        
        self.column_button_frm.pack(anchor='e', side='bottom')
        
        self._window_setup(.75)
        
        
    def show_alter_column_buttons(self):
        self.update_column_btn.pack(side='left', padx=constants.OUT_PAD)
        self.delete_column_btn.pack()
        
        
    def hide_alter_column_buttons(self):
        self.update_column_btn.pack_forget()
        self.delete_column_btn.pack_forget()
        
        
    def show_insert_column_buttons(self):
        self.insert_column_btn.pack()
        
        
    def hide_insert_coulmn_buttons(self):
        self.insert_column_btn.pack_forget()
        
        
    def enable_alter_column_buttons(self):
        for button in self.alter_column_buttons:
            button.config(state='enabled')
            
            
    def disable_alter_column_buttons(self):
        for button in self.alter_column_buttons:
            button.config(state='disabled')
        
        
    def make_value_widgets(self):
        lbl_width = 7
        
        self.column_tooltip.delete()
        
        self._insert_vertical_separator(self.frm_four, 'column')
        
        main_frm = ttk.Frame(self.frm_four)
        
        self.search_frm = ttk.Frame(main_frm)
        self.bottom_value_frm = ttk.Frame(main_frm)
        
        self.search_ent_frm = ttk.Frame(self.search_frm)
        
        self.search_lbl = ttk.Label(
            self.search_ent_frm, text='Value:', width=lbl_width
            )
        self.search_ent = EntrySearch(
            self.search_ent_frm, search_function=self.controller.on_search_click, 
            select_function=self.controller.on_search_match, 
            width=self.ENT_WIDTH
            )
        
        self.disable_search_button()
        
        self.match_count_label = ttk.Label(
            self.search_frm, style='bold.TLabel'
            )
        
        self.outer_value_frame = ttk.Labelframe(
            self.bottom_value_frm, text='Values'
            )
        
        record_footer_frm = ttk.Frame(self.bottom_value_frm)
        
        self.record_label = ttk.Label(record_footer_frm, style='bold.TLabel')
        
        record_button_frm = ttk.Frame(record_footer_frm)
        
        self.update_record_btn = ttk.Button(
            record_button_frm, text='Update', takefocus=False,
            command=self.controller.on_update_record_click
            )
        
        self.delete_record_btn = ttk.Button(
            record_button_frm, text='Delete', takefocus=False,
            command=self.controller.on_delete_record_click
            )
        
        self.alter_record_buttons.append(self.delete_record_btn)
        self.alter_record_buttons.append(self.update_record_btn)
        
        self.disable_alter_record_buttons()
        
        self.insert_record_btn = ttk.Button(
            record_button_frm, text='Insert', takefocus=False,
            command=self.controller.on_insert_record_click
            )
        
        self.disable_insert_record_botton()
        
        main_frm.pack(anchor='n', expand=1, fill='both', side='right')
        
        self.bottom_value_frm.pack(expand=1, fill='both', side='bottom')
        
        self.search_ent_frm.pack(expand=1, fill='x')
        
        self.search_lbl.pack(side='left')
        self.search_ent.pack(fill='x')
         
        self.match_count_label.pack(anchor='e', pady=constants.OUT_PAD)
        
        self.outer_value_frame.pack(anchor='n', fill='x', pady=constants.OUT_PAD)
        
        record_footer_frm.pack(anchor='e', fill='x', side='bottom')
        self.record_label.pack(side='left')
        record_button_frm.pack(anchor='e')
        
        self._window_setup(1)
        
        
    def show_search_widgets(self):
        self.search_frm.pack(fill='x')
        
        
    def hide_search_widgets(self):
        self.search_frm.pack_forget()
        
        
    def show_alter_record_buttons(self):
        self.update_record_btn.pack(side='left', padx=constants.OUT_PAD)
        self.delete_record_btn.pack()
    
    
    def hide_alter_record_buttons(self):
        self.update_record_btn.pack_forget()
        self.delete_record_btn.pack_forget()
        
        
    def enable_alter_record_buttons(self):
        for button in self.alter_record_buttons:
            button.config(state='enabled')
            
            
    def disable_alter_record_buttons(self):
        for button in self.alter_record_buttons:
            button.config(state='disabled')
            
            
    def enable_search_button(self):
        self.search_ent.search_btn.config(state='enabled')
        
        
    def disable_search_button(self):
        self.search_ent.search_btn.config(state='disabled')
    
    
    def show_insert_record_buttons(self):
        self.insert_record_btn.pack()
    
    
    def hide_insert_record_buttons(self):
        self.insert_record_btn.pack_forget()
        
        
    def enable_insert_record_button(self):
        self.insert_record_btn.config(state='enabled')
        
        
    def disable_insert_record_botton(self):
        self.insert_record_btn.config(state='disabled')
        
        
    def make_row_value_widgets(self):
        if self.value_frm:
            self.value_frm.destroy()
            
            self.value_vars = []
            
        self.value_frm = ttk.Frame(self.outer_value_frame)
        
        scroll = self.controller.column_count >= constants.COUNT_FOR_SCROLLBAR
        
        value_frm = FrameScroll(self.value_frm) if scroll else self.value_frm
        
        pad = True
        
        for i, column in enumerate(self.controller.columns.values()):
            var = tk.StringVar()
            self.value_vars.append(var)
            
            text = f'{i}. {column.name} ({column.data_type.lower()}):'
            
            frm = ttk.Frame(value_frm)
            lbl = ttk.Label(
                frm, text=text, 
                width=self.controller.value_label_len + 5
                )
            
            if column.name.lower() == constants.ID_COLUMN_NAME:
                self.controller.check_id_column_tooltip(frm)
            
            if column.is_foreign_key:
                values = self.controller.get_foreign_values(column.name)
                
                widget = ComboboxAutoComplete(
                    frm, textvariable=var, value_list=values
                    )
            
            else:
                widget = ttk.Entry(frm, textvariable=var)
                
            widget.config(width=self.CBO_WIDTH)
            
            #pady = constants.IN_PAD if pad else 0
            pad = not pad
                
            frm.pack(fill='x', padx=constants.IN_PAD)#, pady=pady)
            lbl.pack(side='left')
            widget.pack(fill='x')
            
        if scroll:
            value_frm.update()
            
        self.value_frm.pack(fill='x')
        

class Menu(tk.Menu):
    def __init__(self, parent):
        super().__init__()
        
        self.parent = parent
        
        self._make_mode_menu()
        
        self._make_settings_directory()
        
        
    def _make_mode_menu(self):
        mode_menu = tk.Menu(self, tearoff=False)
        
        for mode, name in constants.DB_MODES.items():
            mode_menu.add_radiobutton(
                label=name, value=mode, variable=self.parent.mode, 
                command=self.parent.controller.on_mode_change
                )
        
        self.add_cascade(label='Mode', menu=mode_menu)
        
        
    def _make_settings_directory(self):
        settings_menu = tk.Menu(self, tearoff=False)
        export_menu = tk.Menu(self, tearoff=False)
        
        settings_menu.add_command(
            label='Directory', command=''
            )
        
        value = 0
        export_menu.add_radiobutton(
            label=self.parent.controller.export_types[value],
            value=value, variable=self.parent.export_type
            )
        
        value = 1
        export_menu.add_radiobutton(
            label=self.parent.controller.export_types[value],
            value=value, variable=self.parent.export_type
            )
        
        value = 2
        export_menu.add_radiobutton(
            label=self.parent.controller.export_types[value],
            value=value, variable=self.parent.export_type
            )
        
        self.add_cascade(label='Settings', menu=settings_menu)
        
        settings_menu.add_cascade(label='Export', menu=export_menu)
        
