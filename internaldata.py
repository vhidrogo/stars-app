'''
Created on Oct 9, 2018

@author: vahidrogo
'''

import sqlite3 as sql

import constants
import utilities


class InternalData:
    '''
    '''
    

    def __init__(
            self, is_cash, juri_abbrev, columns='*', group_by='', 
            order_by='', descending=False, limit=None):
        
        self.is_cash = is_cash
        self.juri_abbrev = juri_abbrev
        self.columns = columns
        self.group_by = group_by
        self.order_by = order_by
        self.descending = descending
        self.limit = limit
        
        self.values_db = (
            constants.QUARTERLY_CASH_DB if self.is_cash 
            else constants.QUARTERLY_ECONOMIC_DB
            )
        
        self._set_table_names()
        
        self._set_query()
        
        
    def _set_table_names(self):
        business_table = values_table = self.juri_abbrev
        
        if self.juri_abbrev.isdigit():
            business_table = constants.NUMBER_TABLE_PREFIX + business_table
            values_table = constants.NUMBER_TABLE_PREFIX + values_table
            
        self.business_table = business_table
        self.values_table = f'{self.values_db}.{values_table}'
        
        
    def _set_query(self):
        query = f'''
            SELECT {self.columns} 
            FROM {self.business_table} 
            NATURAL JOIN {self.values_table}
            '''
        
        if self.group_by:
            query = f'{query} GROUP BY {self.group_by}'
            
        if self.order_by:
            direction = 'DESC' if self.descending else 'ASC'
            
            query = f'{query} ORDER BY {self.order_by} {direction}'
            
        if self.limit:
            query = f'{query} LIMIT {self.limit}'
            
        self.query = query
       

    def get_data(self):
        sql_code = f'ATTACH DATABASE ? AS ?'
        
        args = (
            str(constants.DB_PATHS[self.values_db]), 
            self.values_db
            )
        
        con = sql.connect(
            constants.DB_PATHS[constants.BUSINESSES_DB], uri=True,
            timeout=constants.DB_TIMEOUT
            )
        
        business_db_attached = utilities.execute_sql(
            sql_code=sql_code, args=args, open_con=con, dontfetch=True
            )
         
        results = []
        
        if business_db_attached:
            results = utilities.execute_sql(
                sql_code=self.query, open_con=con, getcursor=True
                )
            
        data = None
            
        if results:
            column_names = [i[0] for i in results.description]
            
            data = results.fetchall()
            
            data = {'column_names' : column_names, 'data' : data}
            
        con.close()
            
        return data
        
        