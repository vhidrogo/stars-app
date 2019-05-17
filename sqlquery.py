'''
Created on Feb 26, 2019

@author: vahidrogo
'''

import pandas as pd
import pyodbc


DRIVER = '{SQL Server}'
SERVER_NAME = 'FROVSQLCS301'
DB_NAME = 'PROD_DW'


class SqlQuery:
    '''
    '''
    

    def __init__(self):
        self.connection_string = f'''
            DRIVER={DRIVER};
            SERVER={SERVER_NAME};
            DATABASE={DB_NAME};
            TRUSTED_CONNECTION=yes;
            '''
        
        self.con = pyodbc.connect(self.connection_string)
        
        
    def query_to_pandas_df(self, query, args=()):
        return pd.read_sql_query(query, self.con, params=args)
        
        
    def fetch_column_names(self, schema_name, table_name):
        names = []
        
        query = f'''
            SELECT COLUMN_NAME
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_NAME = ? AND TABLE_SCHEMA = ?
            '''
        
        args = (table_name, schema_name)
        
        results = self.execute_query(query, args)
        
        if results:
            names = [i[0] for i in results]
            
        return names
    
    
    def fetch_count(self, schema_name, table_name):
        count = 0
        
        query = f'''
            SELECT COUNT(*)
            FROM {schema_name}.{table_name}
            '''
        
        results = self.execute_query(query, fetchall=False)
        
        if results:
            count = results[0]
            
        return count
        
        
    def fetch_version(self):
        query = 'SELECT @@version'
        
        return self.execute_query(query)
    
    
    def execute_query(self, query, args=(), fetchall=True, cursor=False):
        if cursor:
            return self.con.execute(query)
        
        else:
            if fetchall:
                return self.con.execute(query, args).fetchall()
            
            else:
                return self.con.execute(query, args).fetchone()
        
        
    def close(self):
        self.con.close()
 