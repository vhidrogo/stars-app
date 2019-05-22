'''
Created on Nov 5, 2018

@author: vahidrogo

This module is for frequently used functions and classes throughout 
the application.
'''

import getpass
import os
import re
import sqlite3 as sql
import subprocess
import time
from tkinter import messagebox as msg
import traceback

import constants
from fillna import FillNa
from output import Output


FillNa = FillNa()
Output = Output()


def user_exists(user_name):
    exists = False
    
    query = f'''
        SELECT COUNT(*)
        FROM users
        WHERE user_name=?
        '''
    
    db_path = str(constants.INTERNAL_DB_FOLDER.joinpath(constants.CONFIGURATION_DB))
    
    con = sql.connect(db_path, uri=True)
    
    results = con.execute(query, (user_name, )).fetchone()
    
    if results:
        count = results[0]

        if count:
            exists = True
         
    con.close()
     
    return exists


def add_new_user(user_name):
    query = f'''
        SELECT MAX(rowid)
        FROM users
        '''
    
    db_path = str(constants.INTERNAL_DB_FOLDER.joinpath(constants.CONFIGURATION_DB))
    
    con = sql.connect(db_path, uri=True)
    
    results = con.execute(query).fetchone()
    
    max_id = 0
    
    if results:
        max_id = results[0]
        
    new_id = max_id + 1
     
    insert_query = f'''
        INSERT INTO users(id, user_name)
        VALUES (?, ?)
        '''
     
    with con:
        con.execute(insert_query, (new_id, user_name))
         
    con.close()
    
    
def fetch_user_id(user_name):
    query = f'''
            SELECT {constants.ID_COLUMN_NAME}
            FROM users
            WHERE user_name=?
            '''
        
    db_path = str(
        constants.INTERNAL_DB_FOLDER.joinpath(constants.CONFIGURATION_DB)
        )

    con = sql.connect(db_path, uri=True)
    
    results = con.execute(query, (user_name, )).fetchone()
    
    if results:
        return results[0]
    
    
def fetch_default_id(default_name):
    default_id = 0
    
    table_name = 'DefaultNames'
    
    query = f'''
        SELECT {constants.ID_COLUMN_NAME}
        FROM {table_name}
        WHERE name = ?
        '''
    
    args = (default_name, )
    
    con = sql.connect(
        constants.INTERNAL_DB_FOLDER.joinpath(constants.CONFIGURATION_DB),
        uri=True
        )
    
    results = con.execute(query, args).fetchone()
    
    con.close()
    
    if results:
        default_id = results[0]
        
    return default_id
    
    
def set_default(default_name, user_id, default):
    table_name = 'defaults'
    
    default_id = fetch_default_id(default_name)
    
    key = f'{user_id}-{default_id}'
    
    # query to check if the default for the user is already in the 
    #defaults table
    exists_query = f'''
        SELECT COUNT(*)
        FROM {table_name}
        WHERE {constants.ID_COLUMN_NAME}=?
        '''
     
    con = sql.connect(
        str(constants.INTERNAL_DB_FOLDER.joinpath(constants.CONFIGURATION_DB)), 
        uri=True
        )
     
    exists = False
     
    results = con.execute(exists_query, (key, )).fetchone()
     
    if results:
        exists = results[0]
         
    if exists:
        # query to update the default for existing user 
        query = f'''
            UPDATE {table_name}
            SET value=?
            WHERE {constants.ID_COLUMN_NAME}=?
            '''
         
        args = (default, key)
     
    else:
        # query to insert a new user into the defaults table 
        query = f'''
            INSERT INTO {table_name}({constants.ID_COLUMN_NAME}, user_id, 
                default_id, value)
            VALUES (?, ?, ?, ?)
            '''
         
        args = (key, user_id, default_id, default)
         
    with con:
        con.execute(query, args)
         
    con.close()
    
    
def fetch_default(default_name, user_id):
    default_id = fetch_default_id(default_name)
    
    if default_id:
        key = f'{user_id}-{default_id}'
        
        query = f'''
            SELECT value
            FROM defaults
            WHERE {constants.ID_COLUMN_NAME}=?
        '''
    
        con = sql.connect(
            str(constants.INTERNAL_DB_FOLDER.joinpath(constants.CONFIGURATION_DB)), 
            uri=True
            )
        
        results = con.execute(query, (key, )).fetchone()
        
        con.close()
        
        if results:
            return results[0]
    

def open_file(path):
    try:
        os.startfile(path)
        
    except Exception:
        msg.showerror(constants.APP_NAME, traceback.format_exc())


def get_current_path(path, selections=None, quarter=None, year=None):
    if selections is not None:
        quarter = selections.quarter
        year = selections.year
         
    path = path.replace('{quarter}', str(quarter))
    path = path.replace('{year}', str(year))
     
    return path


def is_addon(jurisdiction):
    '''
        Returns whether or not the jurisdiction is an addon.
           
        Args:
            jurisdiction: An instance jurisdiction().
           
        Returns:
            Bool: True if the jurisdiction type is the type for addons, or
            transits which are also addons.
    '''
    return jurisdiction.type in ['addon', 'transit']

  
def execute_sql(
        sql_code, args=(), open_con=None, db_name=None, dml=False, 
        many=False, script=False, fetchall=False, dontfetch=False, 
        getcursor=False, gui=None, show_error=True, attach_db=''):
        
        result = ''
        
        if open_con:
            con = open_con
        
        else:
            db_path = constants.DB_PATHS[db_name]
        
            is_read_only = not dml
            
            con = sql.connect(
                db_path, timeout=constants.DB_TIMEOUT, uri=is_read_only
                )
            
        if attach_db:
            attach_sql = 'ATTACH DATABASE ? AS ?'
            attach_args = (str(constants.DB_PATHS[attach_db]), attach_db)
            con.execute(attach_sql, attach_args)
            
        # con.rollback() is called after the with block finishes with 
        # an exception, the exception is still raised and must be caught
        try:
            # Successful, con.commit() is called automatically afterwards
            with con:
                # if the statement is a data modification statement like
                # UPDATE/SET/DELETE
                if dml:
                    con.execute('PRAGMA foreign_keys=ON;')
                
                if many:
                    result = con.executemany(sql_code, args)
                elif script:
                    result = con.executescript(sql_code)
                else:
                    result = con.execute(sql_code, args)
                    
                if not getcursor:
                    if dml or dontfetch:
                        # set result to true to signal that the dml statement
                        # was successfully executed
                        result = True
                    else:
                        # gets the results from the cursor
                        result = (
                            result.fetchall() if fetchall else result.fetchone()
                            )
                
        except (sql.IntegrityError, sql.OperationalError) as error:
            if show_error:
                msg.showerror(
                    f'{constants.APP_NAME} - Database Error', error, parent=gui
                    )
            
        finally:
            if not open_con:
                con.close()
            
        return result
    
    
def get_table_names(db_name):
    names = []
    
    query = '''
        SELECT name 
        FROM sqlite_master 
        WHERE type='table'
        '''
        
    results = execute_sql(
        sql_code=query, db_name=db_name, fetchall=True
        )
    
    if results:
        names = [i[0] for i in results]
    
    return names


def get_column_names(db_name, table_name):
    names = []
     
    query = f'PRAGMA table_info({table_name})'
         
    table_info = execute_sql(
        sql_code=query, db_name=db_name, fetchall=True
        )
     
    if table_info:
        names = [i[1] for i in table_info]
     
    return names
    
    
def get_period_headers(
        count, selections=None, period=None, year=None, quarter=None, 
        descending=False, prefix='', sep=''
        ):
    
    if selections or period:
        if selections:
            quarter, year = selections.quarter, selections.year
        else:
            year, quarter = [int(i) for i in period.lower().split('q')]
        
    headers = []
    
    for _ in range(count):
        period = f'{year}{sep}Q{quarter}'
        
        if prefix:
            period = prefix + period
        
        headers.append(period)
        
        if quarter == 1:
            quarter = 4
            year -= 1
        
        else:
            quarter -= 1
                
    return headers if descending else list(reversed(headers))


def get_downloads_folder():
    user = getpass.getuser()
        
    return f'C:/Users/{user}/Downloads/'


def get_excluded_from_text_file(file_name, file_lines, jurisdiction=None):
    '''
        Writes the contents of file_lines to a text file named file_name
        that is opened and then waits for user to close. A set is returned 
        with the contents of any lines that were deleted by the user.
        
        Args:
            file_name: String, name used for the file.
            
            file_lines: List, strings that will be written to the file.
        
        Returns: Set, with the contents of any lines that were deleted 
            by the user.
    '''
    if jurisdiction:
        file_name = f'{jurisdiction.id} {file_name}'
    
    file_name += ' - Delete Line to Exclude'
    
    file_path = str(constants.TEMP_FILE_PATH.joinpath(file_name))
    
    with open(file_path, 'w+') as file:
        for name in file_lines:
            file.write(f'{name}\n\n')
       
    subprocess.call(['notepad.exe', file_path])
    
    final_file_lines = [
        line[:-1] for line in open(file_path).readlines() if line[:-1]
        ]
    
    exclude_files = set(set(file_lines) - set(final_file_lines))
    
    return exclude_files


def timestamp():
    return time.strftime('%Y%m%d_%H%M%S')


def is_unincorporated(tac):
    return tac[-3:] == constants.UNINCORPORATED_IDENTIFIER


def percent_change(current_amount, prior_amount):
    return (current_amount - prior_amount) / prior_amount if prior_amount else 0


def is_valid_permit_number(permit_number):
    return re.match(constants.PERMIT_PATTERN, permit_number)


def format_permit_number(permit_number):
    permit_number = str(permit_number)
    
    left = f'0{permit_number[:2]}' if len(permit_number) == 8 else permit_number[:3]
    right = permit_number[-6:]
    formatted_permit_number = left + '-' + right
    
    return formatted_permit_number


def format_tac(tac):
    tac = str(tac)
    return '0' + tac if len(tac) == 4 else tac

    
def clean_business_name(business_name):
    for pattern in constants.BUSINESS_NAME_REMOVE_PATTERNS:
        business_name = re.sub(pattern, '', business_name)
        
    # to remove "+", "=" and "\n"
    translate_string = str.maketrans('', '', '+=\n')
    
    business_name = business_name.translate(translate_string).strip()
        
    return business_name


def get_jurisdiction_table_name(jurisdiction_id):
    '''
        Returns the name of the table for the jurisdiction. If the 
        jurisdiction is a number then the name of the table will be
        that prefixed with "table_".
        
        Args: 
            String, three character abbreviation for the jurisdiction.
            
        Returns:
            String, the name of the table for the jurisdiction.
    '''
    return (
        constants.NUMBER_TABLE_PREFIX + jurisdiction_id 
        if jurisdiction_id.isdigit() else jurisdiction_id
        )
    
def fetch_jurisdiction_header(jurisdiction_name):
    query = f'''
        SELECT s.name
        
        FROM {constants.JURISDICTIONS_TABLE} j,
            {constants.JURISDICTIONS_SUB_TYPES_TABLE} s
            
        WHERE j.Name=?
            AND j.JurisdictionSubTypeId=s.Id
        '''
    
    results = execute_sql(
        sql_code=query, 
        args=(jurisdiction_name, ), 
        db_name=constants.STARS_DB
        )
    
    sub_type = results[0] if results else ''
    
    if sub_type == 'City' and 'City' not in jurisdiction_name:
        header = f'City of {jurisdiction_name}'
    
    elif sub_type == 'Town':
        header = f'Town of {jurisdiction_name}'
    
    else:
        header = jurisdiction_name
    
    return header