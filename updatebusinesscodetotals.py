'''
Created on Nov 5, 2018

@author: vahidrogo
'''

import pandas as pd
from tkinter import messagebox as msg

import constants
from estimates import Estimates
from internaldata import InternalData
import utilities


class UpdateBusinessCodeTotals:
    '''
        Updates the business_code_totals table in statewide_datasets.db
        with the information from the tale in the businesses database for
        the jurisdiction.
    '''
    
    
    table_name = constants.BUSINESS_CODE_TOTALS_TABLE
    db_name = constants.STATEWIDE_DATASETS_DB
    
    
    def __init__(self, controller):
        self.controller = controller
        
        self.selections = self.controller.selections
        
        self.df = None
        
        self.is_addon = False
        
        self.tac_column = 0
        self.business_code_column = 1
        
        self.estimates = Estimates()
        
        
    def main(self, jurisdiction):
        self.jurisdiction = jurisdiction
        
        if utilities.is_addon(self.jurisdiction):
            self.table_name += constants.ADDON_SUFFIX
        
        # if the jurisdiction is for the county pool 
        if self.jurisdiction.type == 'jurisdiction' and self.jurisdiction.tac[-2:] == '99':
            msg.showinfo(
                self.selections.title, 
                f'Jurisdiction ({self.jurisdiction.name}) does not '
                f'belong in table ({self.table_name}).'
                )
        
        else:
            self.controller.update_progress(
                0, f'{self.jurisdiction.id}: Fetching data.'
                )
            
            self._set_df()
            
            if self.df is not None:
                self.controller.update_progress(
                    10, f'{self.jurisdiction.id}: Processing data.'
                    )
                
                self._enter_estimates()
                   
                self._set_needed_columns()
                   
                self._fill_business_code_blanks()
                   
                self._group_by_business_code()
                   
                self._insert_id_column()
                   
                self.controller.update_progress(
                    20, f'{self.jurisdiction.id}: Updating {self.table_name}.'
                    )
                   
                self._update_table()
                   
                self.controller.update_progress(
                    0, f'{self.jurisdiction.id}: Update complete.'
                    )
        
        
    def _set_df(self):
        self.internal_data = InternalData(False, self.jurisdiction.id)
        
        results = self.internal_data.get_data()
        
        if results:
            column_names = results['column_names']
            data = results['data']
            
            self.df = pd.DataFrame(data, columns=column_names)
            
            
    def _enter_estimates(self):
        self.estimates.set_dictionaries(self.df.values.tolist())
        
        first_period_column = list(self.df)[constants.DB_FIRST_QUARTER_COLUMN]
        
        for i, row in enumerate(self.df.itertuples(index=False)):
            # gets the estimate amount if one is necessary, if one is 
            # not necessary then 0 will be returned
            estimate_amount = self.estimates.get_estimate(row)
              
            if estimate_amount:
                self.df.at[
                    i, constants.ESTIMATE_COLUMN_NAME
                    ] = constants.ESTIMATE_COLUMN_NAME
                    
                self.df.at[i, first_period_column] = estimate_amount
                
            
    def _set_needed_columns(self):
        column_names = list(self.df)
        period_columns = column_names[constants.DB_FIRST_QUARTER_COLUMN:]
        
        needed_columns = []
        
        needed_columns.append(column_names[constants.DB_TAC_COLUMN])
        
        needed_columns.append(
            column_names[constants.DB_BUSINESS_CODE_ID_COLUMN]
            )
        
        needed_columns.extend(period_columns)
        
        self.df = self.df[needed_columns]
        
        
    def _fill_business_code_blanks(self):
        '''
            Assigns the default business code id to businesses that have 
            a value of 0 for that column.
        '''
        column_name = list(self.df)[self.business_code_column]
        
        value = constants.DEFAULT_BUSINESS_CODE
        
        # fills all the blanks in the business code column with the default
        self.df.loc[self.df[column_name] == 0, column_name] = value
        
        
    def _group_by_business_code(self):
        column_names = list(self.df)
    
        group_columns = [
            column_names[self.tac_column], 
            column_names[self.business_code_column]
            ]
      
        sum_columns = column_names[self.business_code_column + 1:]
        
        self.df = self.df.groupby(
            group_columns, as_index=False, sort=False)[sum_columns].sum()
        
        
    def _insert_id_column(self):
        # tac and business code id columns
        key_columns = [self.tac_column, self.business_code_column]
        
        id_column = self.df.iloc[
            :, key_columns].apply(lambda x: '-'.join(x.map(str)), axis=1)
        
        self.df.insert(0, constants.ID_COLUMN_NAME, id_column)
        
        
    def _update_table(self):
        deleted = self._delete_current_rows()
        
        if deleted:
            self._insert_new_rows()
            
    
    def _delete_current_rows(self):
        query = f'''
            DELETE FROM {self.table_name}
            WHERE {constants.TAC_COLUMN_NAME}=?
            '''
        
        deleted = utilities.execute_sql(
            sql_code=query, args=(self.jurisdiction.tac, ), 
            db_name=self.db_name, dml=True
            )
        
        return deleted
    
    
    def _insert_new_rows(self):
        column_names = list(self.df)
        
        column_string = ','.join(column_names)
         
        value_place_holders = ','.join('?' for _ in range(len(column_names)))
         
        query = f'''
            INSERT INTO {self.table_name}({column_string})
            VALUES({value_place_holders})
            '''
       
        values = self.df.values.tolist()
        
        utilities.execute_sql(
            sql_code=query, args=values, db_name=self.db_name, 
            dml=True, many=True
            )
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    