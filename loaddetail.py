'''
Created on Oct 24, 2018

@author: vahidrogo
'''

from contextlib import suppress
import pandas as pd
from tkinter import messagebox as msg

from addressparser import AddressParser
import constants
from rundictionary import RunDictionary
from sqlquery import SqlQuery
import utilities


ADDRESS_COLUMN_NAME = 'Address'
PERMIT_COLUMN_NAME = 'AccountNumber'
SUB_COLUMN_NAME = 'AccountSubNumber'

SCHEMA = 'stars'

MAX_PERIOD_COUNT = 40
from progress import LoadingCircle
from timeit import default_timer as timer
class FetchDetail:
    '''
    '''
    
    
    fetch_columns = [
        'BusinessName', PERMIT_COLUMN_NAME, SUB_COLUMN_NAME, 
        ADDRESS_COLUMN_NAME, 'ZIP', 'NAICSCode', 'LP_DateIssued', 
        'LP_DateInactive', 'EconQtr_PeriodDescription', 'Amount'
        ]
    
    
    def __init__(self, controller, selections):
        self.controller = controller
        self.selections = selections
        
        self.query = ''
        self.table_name = ''
        
        self.df = None
        self.jurisdiction = None
        
        self._set_period_count()
        self._set_period_headers()
        
        self.newest_period = int(f'{self.selections.year}0{self.selections.quarter}')
        self.last_period = int(f'{self.period_headers[-1][-4:]}0{self.period_headers[-1][0]}')
     
        
    def _set_period_count(self):
        self.period_count = (
            MAX_PERIOD_COUNT if self.selections.period_count == 'All'
            else int(self.selections.period_count)
            )
        
        
    def _set_period_headers(self):
        self.period_headers = []
        
        quarter, year = self.selections.quarter, self.selections.year
        
        quarter_suffixes = {
            1: 'st',
            2: 'nd',
            3: 'rd',
            4: 'th'
            }
        
        for _ in range(self.period_count):
            self.period_headers.append(
                f'{quarter}{quarter_suffixes[quarter]} Quarter {year}'
                )
            
            if quarter == 1:
                quarter = 4
                year -= 1
            
            else:
                quarter -= 1
            

    def main(self, jurisdiction):
        self.jurisdiction = jurisdiction
        
        self.controller.update_progress(
            0, f'{self.jurisdiction.id}: Fetching data.'
            )
        
        self._set_table_name()
        self._set_query()
        self._set_df()
        
        # formats the permit numbers
        self.df[PERMIT_COLUMN_NAME] = self.df[
            PERMIT_COLUMN_NAME].apply(
                lambda x: utilities.format_permit_number(x)
                )
                
        load_detail = LoadDetail(self, self.df, 'QE')
        load_detail.load(jurisdiction)

        
    def _set_table_name(self):
        if utilities.is_addon(self.jurisdiction):
            self.table_name = (
                'SalesTaxPaymentWithSpreadCA_QC_AO_Stage' 
                if self.selections.basis == 'Cash'
                else 'SalesTaxPaymentWithSpreadCA_QE_AO_Stage'
                )
        else:
            self.table_name = (
                'SalesTaxPaymentWithSpread_QC_Stage' 
                if self.selections.basis == 'Cash'
                else 'SalesTaxPaymentWithSpread_QE_Stage'
                )
        
        
    def _set_query(self):
        self.query = f'''
            SELECT {", ".join(self.fetch_columns)}
            
            FROM {SCHEMA}.{self.table_name}
            
            WHERE TaxAreaCode = {self.jurisdiction.tac}
                AND ABS(Amount) >= 1
                AND Quarter_Key >= {self.last_period}
                AND Quarter_Key <= {self.newest_period}
            '''
                
                
    def _set_df(self):
        address_index = self.fetch_columns.index(ADDRESS_COLUMN_NAME)
        permit_index = self.fetch_columns.index(PERMIT_COLUMN_NAME)
        sub_index = self.fetch_columns.index(SUB_COLUMN_NAME)
        
        horizontal = {}
        initial_amounts = {period : 0 for period in self.period_headers}
        
        sql_query = SqlQuery()
        
        loading_circle = LoadingCircle(self.controller.progress, 'Fetching')
        loading_circle.start()
        
        for i, row in enumerate(sql_query.execute_query(self.query, cursor=True)):
            loading_circle.update_text(f'Fetching\n{i:,}')
            
            sub = row[sub_index]
            key = f'{row[address_index]}{row[permit_index]}{sub}'
          
            if key not in horizontal:
                # last two columns are the quarter and the amount
                permit_data = list(row[:-2])
                  
                if sub is None:
                    # assigns the default sub
                    permit_data[2] = constants.MISSING_SUB_PLACE_HOLDER
                   
                amounts = initial_amounts.copy()
                   
                horizontal[key] = {
                    'permit_data' : permit_data, 'amounts' : amounts
                    }
                   
            period = row[-2]
            amount = float(row[-1])
              
            horizontal[key]['amounts'][period] += amount
         
        row_count = len(horizontal)
 
        tac_column = [self.jurisdiction.tac for _ in range(row_count)]
        jurisdiction_column = [self.jurisdiction.name for _ in range(row_count)]
        est_column = ['' for _ in range(row_count)]
 
        self.df = [
            row['permit_data'] + list(row['amounts'].values())
            for row in horizontal.values()
            ]
         
        self.df = pd.DataFrame(self.df)
 
        self.df.insert(0, constants.TAC_COLUMN_NAME, tac_column)
        self.df.insert(0, 'jurisdiction', jurisdiction_column)
        self.df.insert(constants.ESTIMATE_COLUMN, constants.ESTIMATE_COLUMN_NAME, est_column)
 
        columns = ['jurisdiction', constants.TAC_COLUMN_NAME] + self.fetch_columns[:-2] + ['est']
        columns.extend(self.period_headers)
 
        self.df.columns = columns
        
        sql_query.close()
        loading_circle.end()
        

class LoadDetail:
    '''
    '''
    
    
    AddressParser = AddressParser(constants.ADDRESS_COLUMN)

    default_column_names = [
        constants.ID_COLUMN_NAME, 'JURISDICTION', 'TAC', 'BUSINESS', 
        'PERMIT', 'SUB', 'BUSINESS_CODE_ID'
        ]
        
    default_column_names.extend(constants.ADDRESS_COLUMNS)
        
    default_column_names.extend(
        ['ZIP_CODE', 'OPEN_DATE', 'CLOSED_DATE', 'EST']
        )
    
    NAICS_DIGITS = 6
    
    
    def __init__(self, controller, df, name='', is_cash=False):
        self.controller = controller
        
        self.df = df
        self.name = name
        
        self.selections = self.controller.selections
        
        self.row_count = len(self.df)
        
        self.column_names = []
        self.table_name = ''
        self.business_columns = []
        self.quarterly_columns = []
        
        self.table_permits = {}
        
        self.new_businesses = []
        
        self.quarterly_amounts = []
        
        self.is_cash = (is_cash or 'qc' in self.name.lower())
        
        self.values_db = (
            constants.QUARTERLY_CASH_DB if self.is_cash 
            else constants.QUARTERLY_ECONOMIC_DB
            )
        
        self.business_table_keys = set()
        
        self.new_business_table_keys = set()
        
        self._set_naics_codes_dictionary()
        
        
    def _set_naics_codes_dictionary(self):
        self.naics_codes = {}
        
        query = f'''
            SELECT naics, {constants.BUSINESS_CODE_ID_COLUMN_NAME}
            FROM {constants.NAICS_TO_BUSINESS_CODE_TABLE}
            '''
        
        results = utilities.execute_sql(
            sql_code=query, db_name=constants.STARS_DB, fetchall=True
            )
        
        if results:
            for i in range(self.NAICS_DIGITS, 1, -1):
                naics_codes = self._get_naics_codes_dictionary(results, i)
                
                self.naics_codes[i] = naics_codes


    def _get_naics_codes_dictionary(self, codes, digits):
        naics_codes = {}
        
        for naics_code, business_code_id in codes:
            naics_code = self._get_six_digit_naics_code(naics_code, digits)
                
            if naics_code not in naics_codes:
                naics_codes[naics_code] = business_code_id
            
        return naics_codes
    
    
    def _get_six_digit_naics_code(self, naics_code, digits=None):
        code = str(naics_code)
        
        if not digits:
            digits = len(code)
            
        code = code[:digits]
        
        for _ in range(self.NAICS_DIGITS - digits):
            code += '0'
            
        return code
      
      
    def load(self, jurisdiction):
        self.jurisdiction = jurisdiction
        
        self.controller.update_progress(
            0, f'{self.jurisdiction.id}: Preparing data.')
        
        if self._valid_first_period():
            # fills empty fields in the quarterly columns with zeroes and 
            # empty string in the other columns
            utilities.FillNa.fill_na(self.df)
            
            self.controller.update_progress(
                5, f'{self.jurisdiction.id}: Verifying SQL tables.')
                 
            self._set_column_names()
            
            self._set_table_name()
            
            self._set_table_columns()
            
            self._set_tables()
            
            self._set_business_table_keys()
             
            # start and end of the progress for processing the businesses
            start_progress = 5
            end_progress = 30
                        
            self.controller.update_progress(
                start_progress, 
                f'{self.jurisdiction.id}: Processing businesses.'
                )
                        
            progress_increment = self._get_progress_increment(
                start_progress, end_progress
                )
                        
            self._process_businesses(start_progress, progress_increment)
             
            self.controller.update_progress(
                end_progress, 
                f'{self.jurisdiction.id}: Inserting values.'
                )
                     
            self._insert_values(
                constants.BUSINESSES_DB, self.business_columns, 
                self.new_businesses
                )
            
            self._insert_values(
                self.values_db, self.quarterly_columns, 
                self.quarterly_amounts
                )
             
            progress = 35
                  
            self.controller.update_progress(
                progress, f'{self.jurisdiction.id}: Load completed.'
                )
               
            name_end_progress = 65
            
            run_dictionary = RunDictionary(self.controller)
             
            run_dictionary.main(
                self.jurisdiction, 'Name', start_progress=progress, 
                end_progress=name_end_progress
                )
              
            run_dictionary.main(
                self.jurisdiction, 'Permit', start_progress=name_end_progress
                )
            
            
    def _valid_first_period(self):
        column_names = list(self.df)
        
        first_header = column_names[constants.FIRST_QUARTER_COLUMN]
        
        first_period = self._get_period(first_header)
       
        selected_period = self.selections.period
        
        # if the most recent quarter on the file is not the same as the 
        # quarter selected on the main gui
        if first_period == selected_period:
            valid_first_period = True
            
        else:
            if self._period_is_newer(first_period):
                # drops all the quarters between the most recent quarter on the
                # file and the quarter selected
                self._drop_extra_periods(column_names)
                 
                valid_first_period = True
                 
            else:
                msg.showerror(
                    self.selections.title,
                    'Quarters are missing in file. The most recent period '
                    f'on the file ({first_period}) is older than the '
                    f'selected period ({selected_period}).'
                    )
                 
                valid_first_period = False
         
        return valid_first_period
    
    
    def _get_period(self, raw_header):
        '''
            Reduces the first quarter on the file by one.
        '''
        year = int(raw_header[-4:])
        quarter = int(raw_header[0])
        
        if self.is_cash:
            if quarter == 1:
                quarter = 4
                year -= 1
                
            else: 
                quarter -= 1
                
        first_quarter = f'{year}Q{quarter}'
        
        return first_quarter
            
            
    def _period_is_newer(self, period):
        year = int(period[:4])
        quarter = int(period[-1])
        
        selected = int(f'{self.selections.year}{self.selections.quarter}')
        
        file = int(f'{year}{quarter}')
        
        return file > selected
    
    
    def _drop_extra_periods(self, column_names):
        period_headers = column_names[constants.FIRST_QUARTER_COLUMN :]
        
        for i in period_headers:
            period = self._get_period(i)
            
            if self._period_is_newer(period):
                self.df.drop(i, axis=1, inplace=True)
        
        
    def _set_column_names(self):
        period_count = len(list(self.df)) - constants.FIRST_QUARTER_COLUMN
        
        period_names = utilities.get_period_headers(
            period_count, self.selections, descending=True
            )
       
        self.column_names = self.default_column_names + period_names
        
        
    def _set_table_name(self):
        self.table_name = (
            f'{constants.NUMBER_TABLE_PREFIX}{self.jurisdiction.id}'
            if self.jurisdiction.id.isdigit() else self.jurisdiction.id
            )
        
        
    def _set_table_columns(self):
        self.business_columns = self.column_names[
            :constants.DB_FIRST_QUARTER_COLUMN
            ]
        
        quarterly_columns = [
            f'{constants.QUARTER_COLUMN_PREFIX}{name}' for name in 
            self.column_names[constants.DB_FIRST_QUARTER_COLUMN:]
            ]
        
        quarterly_columns.insert(0, constants.ID_COLUMN_NAME)
        
        self.quarterly_columns = quarterly_columns
        
        
    def _set_tables(self):
        if not self._business_table_exists():
            self._create_table(constants.BUSINESSES_DB, self.business_columns)
        
        # drops the values table if it exists
        sql_code = f'DROP TABLE IF EXISTS {self.table_name}'
         
        utilities.execute_sql(
            sql_code=sql_code, db_name=self.values_db, dml=True
            )
         
        self._create_table(
            self.values_db, self.quarterly_columns, quarterly=True)
        
        
    def _business_table_exists(self):
        '''
            Returns:
                A boolean representing whether or not the table exists in 
                the database.
        '''
        table_names = utilities.get_table_names(constants.BUSINESSES_DB)
        
        return self.table_name in table_names
    
    
    def _create_table(
            self, db_name, column_names, quarterly=False):
        '''
            Creates a table in the given database with the column names in 
            the list provided and if the data is quarterly then the column 
            names will have different types. If it is quarterly then the id 
            column will be of the text type, but the rest of the columns will
            be integers. If the data is not quarterly then the columns will all
            be of the text type. The table will be created in the database of 
            the name that is provided and with the names the list of column 
            names. The only thing that will change in the definition of the table
            if the data is quarterly is the data type of the id column in the 
            definition of the table when it is created and the other parts of the 
            table will be the same.
        
            Args:
                db_name: A string representing the name of the 
                    database where the new table will be created in.
                
                column_names: A list of strings which are the column names
                    that will be used for the new table.
                
                quarterly: A boolean that flags whether or not the data will 
                    go into one of the quarterly databases or not.
        '''
        data_type = 'INTEGER' if quarterly else 'TEXT'
        
        column_string = self._get_column_string(column_names, data_type)
        
        if not quarterly:
            # sets data type for business code id column
            column = constants.BUSINESS_CODE_ID_COLUMN_NAME.upper()
            column_string = column_string.replace(
                f'{column} TEXT', f'{column} INTEGER'
                )
        
        # sets id as primary key
        column_string = column_string.replace(
                f'{constants.ID_COLUMN_NAME} {data_type}', 
                f'{constants.ID_COLUMN_NAME} TEXT PRIMARY KEY'
                )
        
        schema = f'CREATE TABLE {self.table_name} ({column_string})'
         
        if not quarterly:
            schema = self._insert_business_code_foreign_key(schema)
        
        utilities.execute_sql(
            sql_code=schema, db_name=db_name, dml=True
            )
        
        
    def _get_column_string(self, column_names, data_type=None):
        '''
            Returns a strings of the column names and their types formatted 
            so that it can be used as part of the dml when creating the sql 
            table.
        
            Args:
                column_names: A list of strings that contains the names of the 
                columns that will be used for the names of the table when it 
                is created in the database.
                
                data_type: A string representing the data type that will be 
                    assigned to the columns of the table when it is creates.
            
            Returns:
                A formatted string containing all of the column names and their
                    types. The string is formatted to match the syntax used by 
                    the sql dml.
        '''
        return ''.join(
            f'{name} {data_type}, ' if data_type else f'{name}, ' 
            for name in column_names 
            )[:-2].strip()
            
            
    def _insert_business_code_foreign_key(self, schema):
        key = (
            f'FOREIGN KEY({constants.BUSINESS_CODE_ID_COLUMN_NAME.upper()}) '
            f'REFERENCES {constants.BUSINESS_CODES_TABLE}'
                f'({constants.ID_COLUMN_NAME})'
            )
       
        new_schema = f'{schema[:-1]}, {key})'
        
        return new_schema
    
        
    def _set_business_table_keys(self):
        '''
            Returns the values of the id column from the table in the 
            given database.
        
            Args: 
                database_name: A string representing the name of the 
                    database where the table with the keys is located.
        '''
        if self._business_table_exists():
            sql_code = (
                f'SELECT {constants.ID_COLUMN_NAME} '
                f'FROM {self.table_name}'
                )
            
            results = utilities.execute_sql(
                sql_code=sql_code, db_name=constants.BUSINESSES_DB, fetchall=True
                )
            
            if results:
                self.business_table_keys = {i[0] for i in results}
        
        
    def _get_progress_increment(self, start_progress, end_progress):
        return (end_progress - start_progress) / self.row_count
        
        
    def _process_businesses(self, progress, progress_increment):
        for i, row_values in enumerate(self.df.itertuples(index=False)):
            self.controller.update_progress(
                progress,
                f'{self.jurisdiction.id}: Processing business {i+1:,} /{self.row_count:,}'
                )
            
            if i == 0:
                # these fields are the same for every row so they 
                # only need to be bound once
                city_name = row_values[constants.CITY_COLUMN]
                tac = row_values[constants.TAC_COLUMN]
                
            permit = row_values[constants.PERMIT_COLUMN]
            sub = row_values[constants.SUB_COLUMN]
            
            # don't need this since all empty subs get assigned the 9999
            #===================================================================
            # # gets a unique sub
            # sub = self._get_unique_sub(permit, sub)
            #===================================================================
            
            table_key = self._get_table_key(permit, sub)
            
            self.new_business_table_keys.add(table_key)
             
            amounts = list(row_values[constants.FIRST_QUARTER_COLUMN:])
             
            # inserts the key for the amounts table
            amounts.insert(0, table_key)
             
            self.quarterly_amounts.append(amounts)
            
            if table_key not in self.business_table_keys:
                business = row_values[constants.BUSINESS_COLUMN]
                
                if business:
                    # removes thing like "inc" and "corp" and "store #56"
                    business = utilities.clean_business_name(business)
                
                naics_code = row_values[constants.NAICS_COLUMN]
                
                business_code_id = self._get_business_code_id(naics_code)
                
                business_row = [
                        table_key, city_name, tac, business, permit, sub, 
                        business_code_id
                        ]
                    
                address = row_values[constants.ADDRESS_COLUMN]
                         
                # gets a list of the individual fields of the address 
                parsed_address = self.AddressParser.parse_address(address)
                         
                business_row.extend(parsed_address)
                         
                zip_code = row_values[constants.ZIP_COLUMN]
                open_date = row_values[constants.OPEN_COLUMN]
                close_date = row_values[constants.CLOSE_COLUMN]
                    
                estimate = ''
                            
                business_row.extend(
                    [zip_code, open_date, close_date, estimate])
                 
                self.new_businesses.append(business_row)
                
            progress += progress_increment
            

    #===========================================================================
    # def _get_unique_sub(self, permit, sub):
    #     if sub:
    #         if permit in self.table_permits:
    #             # adds the sub to the list of subs for the permit
    #             self.table_permits[permit].append(sub)
    #         else:
    #             self.table_permits[permit] = [sub]
    #                
    #     else:
    #         if permit in self.table_permits:
    #             # creates a new sub number by adding one to the largest
    #             # sub number for the permit
    #             sub = max(self.table_permits[permit]) + 1
    #             self.table_permits[permit].append(sub)
    #         else:
    #             sub = 0
    #             self.table_permits[permit] = [sub]
    #             
    #     return sub
    #===========================================================================
    
    
    def _get_table_key(self, permit, sub):
        # the key is made up of the permit number, sub number and a third 
        # integer separated by "-"
        key = f'{permit}-{sub}-0'
        
        # if the key is already in the list of keys, which will
        # occur when there exists duplicate subs for a permit
        # the last part of the key will be incremented until it is
        # no longer in the list of keys
        if key in self.new_business_table_keys:
            while key in self.new_business_table_keys:
                permit_id = int(key[-1]) + 1
                key = f'{key[:-1]}{permit_id}'
                
        return key
    
    
    def _get_business_code_id(self, naics_code):
        business_code_id = constants.BLANK_BUSINESS_CODE
        
        if naics_code:
            naics_code = self._get_six_digit_naics_code(naics_code)
      
            for i in self.naics_codes.values():
                with suppress(KeyError):
                    business_code_id = i[naics_code]
                    
                    return business_code_id  
        
        return business_code_id
        
        
    def _insert_values(
            self, db_name, column_names, values):
        '''
            Args:
                db_name: A string that represents the name of the 
                    database that contains the table where the values 
                    will be inserted.
                
                column_names: A list of strings with each of the column
                    names for the table where the values will be inserted.
                
                values: A list with the values that will be inserted into
                    the table.
        '''
        column_string = self._get_column_string(column_names)
        
        place_holders = self._get_value_place_holders(len(column_names))
        
        sql_code = (
            f'INSERT INTO {self.table_name}({column_string}) '
            f'VALUES({place_holders})')
        
        utilities.execute_sql(
            sql_code=sql_code, args=values, db_name=db_name, dml=True, 
            many=True
            )
        
        
    def _get_value_place_holders(self, count):
        '''
            Returns a formatted string that matches the syntax of the sql dml
            that will be used as part of the statement when inserting the 
            values. There is a "?" place holder for each of the columns in the
            table that will serve as place holders for the values that will
            be inserted into the table.
    
            Args:
                count: An integer representing the number of columns
                in the table that will need a place holder.
        '''
        return ''.join('?, ' for _ in range(count))[:-2]
    
    
    
       
