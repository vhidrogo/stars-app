'''
Created on May 13, 2019

@author: vahidrogo
'''

from sqlquery import SqlQuery
import utilities


PERIOD_COUNT = 12

AMOUNT_COL = 'Amount'
PERIOD_COL = 'CQuarterName'
TRANSACTION_TYPE_COL = 'TransactionType'
FETCH_COLUMNS = ['TransactionType', 'CQuarterName', 'Amount']

OUTPUT_NAME = 'Summarized Cash Anomalies'


class CashAnomalies:
    '''
    '''
    def __init__(self, controller, selections):
        self.controller = controller
        self.selections = selections
        
        self.df = None
        self.jurisdiction = None
        self.output_saved = False
        
        self.query = ''
        self.output_path = ''
        
        self.period_headers = utilities.get_period_headers(
            count=PERIOD_COUNT,
            selections=self.selections,
            descending=True,
            sep=' '
            )
        

    def main(self, jurisdiction):
        self.jurisdiction = jurisdiction
        
        self.controller.update_progress(
            0, f'{self.jurisdiction.id}: Fetching data.'
            )
        
        self._set_query()
        self._set_df()
        
        if self.df is not None:
            self._transpose_periods()
            self._set_output_path()
            self._output()
            
        self.controller.update_progress(
            100, f'{self.jurisdiction.id}: Finished.'
            )
            
        if self.output_saved and self.selections.open_output:
            utilities.open_file(self.output_path)
        
        
    def _set_query(self):
        self.query = f'''
            SELECT {TRANSACTION_TYPE_COL}, {PERIOD_COL}, SUM({AMOUNT_COL})
            
            FROM stars.CR_CashAnomoly_CA
            
            WHERE TaxArea = {self.jurisdiction.tac}
                AND {PERIOD_COL} IN {tuple(self.period_headers)} 
                
            GROUP BY {TRANSACTION_TYPE_COL}, {PERIOD_COL}
            '''
        
        
    def _set_df(self):
        sql_query = SqlQuery()
        
        self.df = sql_query.query_to_pandas_df(self.query)
        
        sql_query.close()
        
    
    def _transpose_periods(self):
        transposed = {}
        
        for row in self.df.itertuples(index=False):
            transaction_type = row[0]
            
            if transaction_type not in transposed:
                amounts = {period: 0 for period in self.period_headers}
                
                transposed[transaction_type] = amounts
                
            period = row[1]
            amount = row[-1]
            
            transposed[transaction_type][period] += amount
        
        self.df = [
            (transaction_type, ) + tuple(amounts.values())
            for transaction_type, amounts in transposed.items() 
            ]    
    
    def _set_output_path(self):
        name = f'{self.jurisdiction.id} {self.selections.period} {OUTPUT_NAME}'
        
        self.output_path = (
            f'{self.jurisdiction.folder}{name}.{self.selections.output_type}'
            )
    
    
    def _output(self):
        header = ['TransactionType'] + self.period_headers
        
        self.output_saved = utilities.Output.output(
            self.df, self.output_path, header
            )