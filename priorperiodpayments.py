'''
Created on Mar 18, 2019

@author: vahidrogo
'''

from sqlquery import SqlQuery
import utilities


class PriorPeriodPayments:
    '''
    '''
    
    
    PERIOD_COUNT = 4
    
    business_column_name = 'BusinessName'
    cash_period_column_name = 'CQuarterName'
    econ_period_column_name = 'EQuarterName'
    amount_column_name = 'Amount'
    permit_column_name = 'AccountNumber'
    
    fetch_column_names = [
        permit_column_name, business_column_name, amount_column_name, 
        cash_period_column_name, econ_period_column_name
        ]
    
    exclude_types = ('MV', 'NR', 'ZR', 'Other')
    
    tac_column_name = 'TaxArea'
    type_column_name = 'TransactionType'
    
    schema_name = 'stars'
    table_name = 'CR_CashAnomoly_CA'
    
    output_name = 'Prior_Period_Payments'
    
    
    def __init__(self, controller):
        self.controller = controller
        self.selections = self.controller.selections
        
        self.df = None
        
        self.jurisdiction = None
        
        self.output_saved = False
        
        self._set_adjusted_cash_period()

        self.adjusted_cash_year = int(self.adjusted_cash_period.split()[0])
        self.adjusted_cash_quarter = int(self.adjusted_cash_period[-1])
        
        self.base_periods = utilities.get_period_headers(
            self.PERIOD_COUNT, year=self.adjusted_cash_year, 
            quarter=self.adjusted_cash_quarter
            )
        
        self.fetch_periods = tuple(
            i.replace('Q', ' Q') for i in self.base_periods
            )

        self.query = ''
        
        self.output_path = ''
        
        self.sheet_rows = []
        

    def _set_adjusted_cash_period(self):
        year = self.selections.year
        quarter = self.selections.quarter
        
        if quarter == 4:
            quarter = 1
            year += 1
            
        else:
            quarter += 1
        
        self.adjusted_cash_period = f'{year} Q{quarter}'
        
        
    def main(self, jurisdiction):
        self.jurisdiction = jurisdiction
        
        self.controller.update_progress(
            0, f'{self.jurisdiction.id}: Fetching data.'
            )
        
        self._set_query()
        
        self._set_df()
        
        if self.df is not None:
            # formats the permit column
            self.df[self.permit_column_name] = self.df[self.permit_column_name].apply(
                lambda x: utilities.format_permit_number(x)
                )
            
            self._transpose()
            
            if self.df is not None:
                self._set_output_path()
                
                self._output()
                
                if self.output_saved:
                    self.controller.update_progress(
                        100, f'{self.jurisdiction.id}: Finished.'
                        )
                    
                    if self.selections.open_output:
                        utilities.open_file(self.output_path)
            
            
    def _set_query(self):
        group_columns = [
            self.permit_column_name, self.business_column_name, 
            self.cash_period_column_name, self.econ_period_column_name
            ]
        
        query = f'''
            SELECT {', '.join(self.fetch_column_names)} 
            
            FROM {self.schema_name}.{self.table_name}
            
            WHERE {self.tac_column_name} = '{self.jurisdiction.tac}' 
                AND {self.type_column_name} NOT IN {self.exclude_types}
                AND {self.cash_period_column_name} IN {self.fetch_periods}
                
            GROUP BY {', '.join(group_columns)}
            '''
        
        # replaces the name of the amount column to surround it with the 
        # SQL SUM function
        self.query = query.replace(
            self.amount_column_name, 
            f'SUM({self.amount_column_name}) {self.amount_column_name}'
            )
        
        
    def _set_df(self):
        sql_query = SqlQuery()
        
        self.df = sql_query.query_to_pandas_df(self.query)
        
        sql_query.close()
        
        
    def _transpose(self):
        horizontal = {}
        
        for row in self.df.itertuples():
            permit = getattr(row, self.permit_column_name)
            
            if permit not in horizontal:
                business = getattr(row, self.business_column_name)
                
                amounts = {period : 0 for period in self.fetch_periods}
                
                horizontal[permit] = {
                    'business' : business, 'amounts' : amounts
                    }
                
            cash_period = getattr(row, self.cash_period_column_name)
            econ_period = getattr(row, self.econ_period_column_name)
            
            amount = int(getattr(row, self.amount_column_name))
            
            # adds the amount to the correct period
            horizontal[permit]['amounts'][cash_period] += amount
            
            # if the period that it was for is still part of the forecast base
            if econ_period in self.fetch_periods:
                # adds the inverse of the amount in the economic period
                horizontal[permit]['amounts'][econ_period] += -amount

        self.sheet_rows = [
            [permit, data['business']] + list(data['amounts'].values())
            for permit, data in horizontal.items()
            ]
        

    def _set_output_path(self):
        name = (
            f'{self.jurisdiction.id} {self.selections.period} {self.output_name}'
            )
        self.output_path = (
            f'{self.jurisdiction.folder}{name}.{self.selections.output_type}'
            )

            
    def _output(self):
        header = [self.permit_column_name, self.business_column_name] + self.base_periods
        
        utilities.Output.output(self.sheet_rows, self.output_path, header)
        
        self.output_saved = True
        
        