'''
Created on Feb 10, 2019

@author: vahidrogo
'''

import pandas as pd

import constants
from internaldata import InternalData
import utilities


class BusinessDetailTotals:
    '''
    '''
    
    
    def __init__(self, controller, selections):
        self.controller = controller
        self.selections = selections
        
        self.output_name = f'{self.selections.type_option} Totals by'
        
        self.current_period = ''
        self.prior_period = ''
        
        self.output_path = ''
        
        self.is_cash = self.selections.basis == 'Cash'
        self.is_category = self.selections.type_option == 'Category'
        
        self.df = None
        self.jurisdiction = None
        self.output_saved = False
        
        self.period_headers = []
        
        self._set_total_names()
        
        
    def _set_total_names(self):
        '''
            Populates a dictionary with the business code id as the key 
            and it's associated value is either a segment name or a 
            category name.
        '''
        self.total_names = {}
        
        if self.is_category:
            query = f'''
                SELECT b.Id, c.name
                
                FROM {constants.BUSINESS_CODES_TABLE} b, 
                    {constants.SEGMENTS_TABLE} s,
                    {constants.CATEGORIES_TABLE} c
                
                WHERE b.{constants.SEGMENT_ID_COLUMN_NAME}=s.Id
                    AND s.{constants.CATEGORY_ID_COLUMN_NAME}=c.Id
                '''
        
        else:
            query = f'''
                SELECT b.Id, s.name
                
                FROM {constants.BUSINESS_CODES_TABLE} b, 
                    {constants.SEGMENTS_TABLE} s
                    
                WHERE b.{constants.SEGMENT_ID_COLUMN_NAME}=s.Id
                '''
        
        results = utilities.execute_sql(
            sql_code=query, db_name=constants.STARS_DB, fetchall=True
            )
        
        for business_code_id, total_name in results:
            self.total_names[business_code_id] = total_name
            

    def main(self, jurisdiction):
        self.jurisdiction = jurisdiction
        
        self.controller.update_progress(
            0, f'{self.jurisdiction.id}: Fetching Data.'
            )
        
        if not self.is_cash:
            self._set_econ_table_name()
         
        self._set_period_headers()
        
        self.current_period = self.period_headers[-1]
        self.prior_period = self.period_headers[-5]
          
        self._set_column_string()
          
        self._set_df()
        
        if self.df is not None:
            self._insert_total_names()
            
            self.df.drop(
                constants.BUSINESS_CODE_ID_COLUMN_NAME.upper(), axis=1, 
                inplace=True
                )
             
            self._group_by_total_name()
            
            if self.selections.interval == 'Year':
                self._convert_to_year_amounts()
                
                # removes the oldest three period headers that were used
                # to pull the quarterly amounts
                del self.period_headers[:3]
            
            # only takes the number of period columns left in case some with
            # None values were dropped off in the group function
            header = [self.selections.type_option] 
            header.extend(self.period_headers[-(len(list(self.df)) - 1):])

            self.df.columns = header
               
            self._order()
                
            self._set_output_path()
                
            self.output_saved = utilities.Output.output(
                self.df, self.output_path, header, 
                )
                
            if self.output_saved:
                self.controller.update_progress(
                    100, f'{self.jurisdiction.id}: Finished.'
                    )
                    
                if self.selections.open_output:
                    utilities.open_file(self.output_path)
                    
                    
    def _set_econ_table_name(self):
        self.econ_table_name = constants.BUSINESS_CODE_TOTALS_TABLE
                
        if utilities.is_addon(self.jurisdiction):
            self.econ_table_name += constants.ADDON_SUFFIX
        
        
    def _set_period_headers(self):
        '''
            Populates a list of string period headers for each of the 
            periods that will be fetched.
        '''
        if self.selections.period_count == 'All':
            if self.is_cash:
                table_name = utilities.get_jurisdiction_table_name(
                    self.jurisdiction.id
                    )
                
                db_name = constants.QUARTERLY_CASH_DB
                
                # number of other columns in the table other than the 
                # period columns
                other_column_count = 1
                
            else: 
                table_name = self.econ_table_name
                db_name = constants.STATEWIDE_DATASETS_DB
                other_column_count = 3
            
            column_names = utilities.get_column_names(db_name, table_name)
            
            # the table has an id column and the available periods
            count = len(column_names) - other_column_count
            
        else:
            count = int(self.selections.period_count)
            
            if (
                self.selections.interval == 'Year' 
                and count + 3 <= constants.MAX_PERIOD_COUNT
                ):
                
                count += 3
            
        self.period_headers = utilities.get_period_headers(
            count, self.selections
            )
            
            
    def _set_column_string(self):
        '''
            Builds the string that will be part of the SQL query to pull 
            the sum of each period and the business code id.
        '''
        self.column_string = f'{constants.BUSINESS_CODE_ID_COLUMN_NAME},'
        
        period_columns = [
            constants.QUARTER_COLUMN_PREFIX + i for i in self.period_headers
            ]
        
        if self.is_cash:
            # surrounds the period columns with the syntax for 
            # SQL sum function
            period_columns = [f'SUM({i})' for i in period_columns]
        
        self.column_string += ','.join(period_columns)
        
        
    def _set_df(self):
        if self.is_cash:
            internal_data = InternalData(
                True, self.jurisdiction.id, self.column_string,
                group_by=constants.BUSINESS_CODE_ID_COLUMN_NAME
                )
                  
            results = internal_data.get_data()
                
            if results:
                columns = results['column_names']
                business_code_totals = results['data']
                    
                self.df = pd.DataFrame(business_code_totals, columns=columns)
                
        else:
            query = f'''
                SELECT {self.column_string}
                FROM {self.econ_table_name}
                WHERE {constants.TAC_COLUMN_NAME}=?
                '''
            
            args = (self.jurisdiction.tac, )
            
            results = utilities.execute_sql(
                sql_code=query, args=args, fetchall=True,
                db_name=constants.STATEWIDE_DATASETS_DB, 
                )
            
            if results:
                columns = [constants.BUSINESS_CODE_ID_COLUMN_NAME.upper()]
                columns.extend(self.period_headers)
                
                self.df = pd.DataFrame(results, columns=columns)
                

    def _insert_total_names(self):
        total_names = []
        
        for row in self.df.itertuples(index=False):
            # if the business code id is blank (assigned a 0) then the 
            # default business code is used instead
            business_code_id = (
                row[0] if row[0] else constants.DEFAULT_BUSINESS_CODE
                )
            
            total_name = self.total_names[business_code_id]
            total_names.append(total_name)
            
        self.df.insert(0, self.selections.type_option, total_names)
        
        
    def _group_by_total_name(self):
        column_names = list(self.df)
    
        group_columns = [self.selections.type_option]
        
        sum_columns = column_names[1:]
        
        self.df = self.df.groupby(
            group_columns, as_index=False, sort=False
            )[sum_columns].sum()
            
            
    def _convert_to_year_amounts(self):
        year_data = []
        
        for row in self.df.itertuples(index=False):
            segment = row[0]
            quarter_amounts = row[1:]
            
            year_amounts = [
                sum(quarter_amounts[i : i + constants.BMY_PERIOD_COUNT])
                for i in range(
                    len(quarter_amounts) - constants.BMY_PERIOD_COUNT + 1
                    )
                ]
            
            year_data.append([segment] + year_amounts)
         
        self.df = pd.DataFrame(year_data)
        
        
    def _order(self):
        if self.selections.order != 'None':
            if self.selections.order == 'Name':
                # sorts by the segment name
                self.df.sort_values(by=self.selections.type_option, inplace=True)
                
            elif self.selections.order == 'Quarter':
                # sorts by the most recent period
                self.df.sort_values(
                    by=self.current_period, ascending=self.selections.ascending,
                    inplace=True
                    )
                
            else:
                if self.selections.order == '$ Change':
                    # inserts column with most recent quarter over quarter 
                    # amount change
                    self.df[self.selections.order] = (
                        self.df[self.current_period] - self.df[self.prior_period]
                        )
                    
                elif self.selections.order == '% Change':
                    # inserts a column with most recent quarter over quarter
                    # percent change
                    self.df[self.selections.order] = self.df.apply(
                        lambda row: self._percent_change(row), axis=1
                        )
                    
                else:
                    columns = list(self.df)
                    
                    # inserts a column with the sum of the most recent four 
                    # columns which are to the left of the data
                    self.df[self.selections.order] = (
                        self.df[columns[-1]] + self.df[columns[-2]] 
                        + self.df[columns[-2]] + self.df[columns[-4]]
                        )
                    
                # sorts by the change column
                self.df.sort_values(
                    by=self.selections.order, ascending=self.selections.ascending, 
                    inplace=True
                    )
                
                # drops the amount change column
                self.df.drop(self.selections.order, axis=1, inplace=True)
        
                
    def _percent_change(self, row):
        '''
            Args: 
                Pandas Series.
            
            Returns:
                Float. The calculated percent change for the row if the 
                prior period amount is non zero, otherwise returns 0.
        '''
        return (
            (row[self.current_period] - row[self.prior_period]) 
            / 
            row[self.prior_period]
            if row[self.prior_period] else 0
            )
            
            
    def _set_output_path(self):
        name = (
            f'{self.jurisdiction.id} {self.selections.period} '
            f'{self.selections.basis} {self.output_name} {self.selections.interval}'
            )
        
        self.output_path = (
            f'{self.jurisdiction.folder}{name}.{self.selections.output_type}'
            )
                    
