'''
Created on Jul 20, 2018

@author: vahidrogo
'''

from copy import deepcopy
from operator import itemgetter
import pandas as pd
import sqlite3 as sql
import threading
from tkinter import messagebox as msg
import traceback

import constants
from loaddetail import LoadDetail
from progress import Progress
import utilities


class BusinessDetailJoin(threading.Thread):
    '''
    '''
    
    
    title = f'{constants.APP_NAME} - Business Detail (Join)'
    
    
    def __init__(self, jurisdiction, files, selections):
        super().__init__()
        
        self.jurisdiction = jurisdiction
        self.files = files
        self.selections = selections
        
        self.file_count = len(self.files)
        
        self.name = ''
        
        self.abort = False
        self.con = None
        
        self.df = None
        
        self.other_columns = []
        self.table_names = []
        
        self.period_columns = {}
        
        
    def run(self):
        self.progress = Progress(self, self.title)

        self.con = sql.connect(':memory:')
        
        try:
            progress = 0
        
            for i, item in enumerate(self.files.items()):
                name, data = item
                df = data[1]
                
                if not self.name:
                    self.name = name
                    
                self.update_progress(
                    progress, f'Creating SQL table for {name}.'
                    )
                
                self._process_file(df, i)
                
                progress += 45 / self.file_count
                
            self.update_progress(45, 'Joining SQL tables.')
            
            self._join_tables()
            
            # drops the id column
            self.df.drop(constants.ID_COLUMN_NAME, axis=1, inplace=True)
            
            self._revert_column_names()
            
            self._sort_quarters()
            
            self.update_progress(55, 'Filling in NULLS.')
            
            utilities.FillNa.fill_na(self.df)
            self.df.to_csv('test.csv')
            if self.df is not None:
                load_detail = LoadDetail(self, self.df, self.name)
                
                load_detail.load(self.jurisdiction)
                
        except Exception:
            msg.showerror(
                self.title, 
                'Unhandled exception occurred attempting to join '
                f'{self.file_count} for {self.jurisdiction.id}:\n\n{traceback.format_exc()}'
                )
        
        finally:
            self.progress.destroy()
            self.con.close()
    
        return self.df
       
        
    def _process_file(self, df, count):
        table_name = f't{count}'
        self.table_names.append(table_name)
         
        self._prepare_column_names(df)
        
        column_names = list(df)
        
        if not self.other_columns:
            self.other_columns = column_names[:constants.FIRST_QUARTER_COLUMN]
            
            self.other_columns.insert(0, constants.ID_COLUMN_NAME)
        
        self.period_columns[table_name] = column_names[constants.FIRST_QUARTER_COLUMN:]
        
        self._insert_id_column(df)
        
        # creates the table in the in memory database
        df.to_sql(table_name, self.con, index=False)
        
        
    def _prepare_column_names(self, df):
        '''
            Prepares the column names so that they will be accepted by sql.
        '''
        names = list(df)
        
        fixed_names = []
        
        for name in names:
            name = name.replace(':', '').replace(' ', '_')
            
            if name[0].isdigit():
                name = 'c_' + name
                
            fixed_names.append(name)
                
        df.columns = fixed_names
        
        
    def _insert_id_column(self, df):
        '''
            Gets a unique sub number for each location to use as part of the 
            key for that location.
        '''
        # inserts an empty column into the dataframe for the row ids
        df.insert(0, constants.ID_COLUMN_NAME, '')
        
        row_ids = set()
        
        for i, row in enumerate(df.itertuples(index=False)):
            permit = str(row[constants.PERMIT_COLUMN + 1])
            
            # the currently assigned value to the permit for this location
            # which may be a blank
            sub = row[constants.SUB_COLUMN + 1]
     
            # unique id to use as the join
            row_id = self._row_id(row_ids, permit, sub)
            
            # sets the row id in the dataframe
            df.at[i, constants.ID_COLUMN_NAME] = row_id
            
            # adds the row id to the set of already created row ids
            row_ids.add(row_id)
    
    
    def _row_id(self, keys, permit, sub):
        # the key is made up of the permit number, sub number and a third 
        # integer separated by "-"
        key = f'{permit}-{sub}-0'
        
        # if the key is already in the list of keys, which will
        # occur when there exists duplicate subs for a permit
        # the last part of the key will be incremented until it is
        # no longer in the list of keys
        while key in keys:
            sub_id = int(key[-1]) + 1
            key = f'{key[:-1]}{sub_id}'
                
        return key
         

    def _join_tables(self,):
        table_one = self.table_names[0]
        joined_table = 'joined'
        
        create_columns = deepcopy(self.other_columns)
        left_select_columns = [
            f'{table_one}.{column}' for column in self.other_columns
            ]
        
        create_columns += self.period_columns[table_one]
        left_select_columns += self.period_columns[table_one]
        
        right_period_columns = self.period_columns[table_one]
        
        for name in self.table_names[1:]:
            right_period_columns += self.period_columns[name]
            
            right_select_columns = [
                f'{name}.{column}' for column in self.other_columns
                ] + right_period_columns
            
            create_columns += self.period_columns[name]
            left_select_columns += self.period_columns[name]
            
            create_columns_string = ','.join(create_columns)
            left_select_columns_string = ','.join(left_select_columns)
            right_select_columns_string = ','.join(right_select_columns)
            
            # creates a new table "joined" to insert the results of the 
            # emulated full outer join into it
            # then drops table one and the table that was joined and renames
            # the joined results to the name of table one to join with the 
            # next table
            sql_script = f'''
                CREATE TABLE {joined_table} ({create_columns_string});
                
                INSERT INTO {joined_table} ({create_columns_string})
                    SELECT {left_select_columns_string}
                    FROM {table_one} 
                    LEFT JOIN {name} USING({constants.ID_COLUMN_NAME})
                    
                    UNION ALL
                    
                    SELECT {right_select_columns_string}
                    FROM {name} 
                    LEFT JOIN {table_one} USING({constants.ID_COLUMN_NAME})
                    WHERE {table_one}.{constants.ID_COLUMN_NAME} IS NULL;
                    
                DROP TABLE {table_one};
                
                DROP TABLE {name};
                
                ALTER TABLE {joined_table} RENAME TO {table_one}; 
                '''

            self.con.executescript(sql_script)
            
        query = f'''
            SELECT *
            FROM {table_one}
            '''
             
        self.df = pd.read_sql(query, self.con)
        
            
    def _revert_column_names(self):
        '''
            Reverts the column names so that they are accepted by the load
            process.
        '''
        revert_names = []
        
        column_names = list(self.df)
        
        for name in column_names:
            name = name.replace('c_', '').replace('_', ' ')
            
            revert_names.append(name)
            
        self.df.columns = revert_names


    def _sort_quarters(self):
        column_names = list(self.df)
        
        quarter_columns = column_names[constants.FIRST_QUARTER_COLUMN:]
            
        sort_keys = [(q, q[-4:] + q[0]) for q in quarter_columns]
        
        quarter_columns = [
            q[0] for q in sorted(sort_keys, key=itemgetter(1), reverse=True)
            ]
        
        column_names[constants.FIRST_QUARTER_COLUMN:] = quarter_columns
            
        # replaces the dataframe with the one with the quarters sorted 
        self.df = self.df[column_names]
        
    
    def update_progress(self, progress, message):
        self.progress.update_progress(
            progress, message, 0, self.selections.jurisdiction_count
            )