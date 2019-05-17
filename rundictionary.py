'''
Created on Oct 22, 2018

@author: vahidrogo
'''

import sqlite3 as sql

import constants
import utilities


class RunDictionary:
    '''
    '''
    
    
    name_dictionary_query = f'''
        SELECT good_name, {constants.BUSINESS_CODE_ID_COLUMN_NAME} 
        
        FROM {constants.NAME_DICTIONARY_TABLE} 
            
        WHERE bad_name=?
        
        COLLATE NOCASE
        '''
    
    permit_dictionary_query = f'''
        SELECT {constants.BUSINESS_COLUMN_NAME}, {constants.BUSINESS_CODE_ID_COLUMN_NAME} 
        
        FROM {constants.PERMITS_TABLE} 
            
        WHERE {constants.ID_COLUMN_NAME}=?
        '''
    
    
    def __init__(self, controller):
        self.controller = controller
        
        self.businesses_query = ''
        
        self.update_query = ''
        
        self.jurisdiction = None
        
        self.is_name_dictionary = True
        
        self.businesses = []
        
        
    def main(
            self, jurisdiction, dictionary_type, start_progress=0, end_progress=100):
        
        progress = start_progress
        
        self.jurisdiction = jurisdiction
        
        self.controller.update_progress(
            progress, f'{self.jurisdiction.id}: Fetching Data.'
            )
        
        self.is_name_dictionary = dictionary_type == 'Name'
        
        self._set_table_name()
        
        self._set_businesses_query()
        
        self._set_businesses()
       
        if self.businesses:
            self._set_update_query()
            
            row_count = len(self.businesses)
             
            query = (
                self.name_dictionary_query if self.is_name_dictionary
                else self.permit_dictionary_query
                )
             
            step = f'Running {dictionary_type} Dictionary'
             
            self.controller.update_progress(
                progress, f'{self.jurisdiction.id}: {step}'
                )
            
            sql_code = (
                'ATTACH DATABASE '
                f'"{constants.DB_PATHS[constants.BUSINESSES_DB]}" '
                f'AS {constants.BUSINESSES_DB}'
                )
             
            con = sql.connect(
                constants.DB_PATHS[constants.STARS_DB], 
                timeout=constants.DB_TIMEOUT
                )
            
            with con:
                business_db_attached = utilities.execute_sql(
                    sql_code=sql_code, open_con=con, dontfetch=True
                    )
                 
                if business_db_attached:
                    for i, row in enumerate(self.businesses, start=1):
                        run_query = False
                          
                        if self.is_name_dictionary:
                            business = row[-1]
                              
                            args = (business, )
                              
                            run_query = True
                             
                        else:
                            business = row[-2]
                            business_code = row[-1]
                              
                            if (
                                business.lower() in ['', 'unknown'] or 
                                not business_code):
                                permit = row[1]
                                  
                                args = (permit, )
                                  
                                run_query = True
                          
                        if run_query:
                            results = ()
                              
                            results = utilities.execute_sql(
                                sql_code=query, args=args, open_con=con
                                )
                              
                            if results:
                                row_id = row[0]
                                
                                args = results + (row_id, )
                                
                                utilities.execute_sql(
                                    sql_code=self.update_query, args=args, 
                                    open_con=con, dml=True
                                    )
                                 
                        progress += (end_progress - start_progress) / row_count
                        
                        self.controller.update_progress(
                            progress, 
                            f'{self.jurisdiction.id}: {step} {i:,} /{row_count:,}'
                            )
                        
                    self.controller.update_progress(
                        100, f'{self.jurisdiction.id}: Finished.'
                        )
            
            
    def _set_table_name(self):
        self.table_name = (
            f'{constants.NUMBER_TABLE_PREFIX}{self.jurisdiction.id}' 
            if self.jurisdiction.id.isdigit() else self.jurisdiction.id
            )
        
        
    def _set_businesses_query(self):
        if self.is_name_dictionary:
            self.businesses_query = f'''
                SELECT rowid, {constants.BUSINESS_COLUMN_NAME} 
                FROM {self.table_name}
                '''
        
        else:
            self.businesses_query = f'''
                SELECT rowid, {constants.PERMIT_COLUMN_NAME}, 
                    {constants.BUSINESS_COLUMN_NAME}, 
                    {constants.BUSINESS_CODE_ID_COLUMN_NAME} 
                FROM {self.table_name}
                '''    
    
    
    def _set_update_query(self):
        self.update_query = f'''
            UPDATE {constants.BUSINESSES_DB}.{self.table_name}
            
            SET {constants.BUSINESS_COLUMN_NAME}=?, 
                {constants.BUSINESS_CODE_ID_COLUMN_NAME}=?

            WHERE rowid=?
            '''
                    
                    
    def _set_businesses(self):
        self.businesses = []
        
        results = utilities.execute_sql(
            sql_code=self.businesses_query, db_name=constants.BUSINESSES_DB, 
            fetchall=True
            )
        
        if results:
            self.businesses = results
        