'''
Created on May 23, 2019

@author: vahidrogo
'''

import xlsxwriter

import constants
import utilities


class AnnualizedPerCapitaChart:
    '''
        Creates the "Annualized Per Capita by Economic Category" Excel chart.
    '''
    
    
    def __init__(self, controller, selections):
        self.controller = controller
        self.selections = selections
        
        self.output_path = ''
        self.sales_tax_query = ''
        
        self.jurisdiction = None
        
        self.category_totals = ()
        
        self.totals = []
        
        self.population = {}
        
        self.period_count = (self.selections.years * 4)
        
        self._set_periods()
        self._set_interval_periods()
        
        self._set_sales_tax_query()
        self._set_population_query()
        
        
    def main(self, jurisdiction):
        self.jurisdiction = jurisdiction
        
        self._set_category_totals()
        print(self.category_totals)
        if self.category_totals:
            self._set_population()
            
            if self.population:
                self._set_totals()
                print(self.population)
                print()
                
                print(self.totals)
        
    def _set_periods(self):
        self.periods = utilities.get_period_headers(
            count=self.period_count,
            selections=self.selections,
            prefix=constants.QUARTER_COLUMN_PREFIX
            )
        
        
    def _set_interval_periods(self):
        self.interval_periods = utilities.get_period_headers(
            count=self.period_count,
            selections=self.selections,
            step=4
            )
        
        
    def _set_sales_tax_query(self):
        self.sales_tax_query = f'''
            SELECT c.Name,{",".join(self._get_sum_year_strings())}
            
            FROM {constants.CATEGORY_TOTALS_TABLE} t,
                {constants.CATEGORIES_TABLE} c
                
            WHERE t.{constants.TAC_COLUMN_NAME} = ?
                AND t.{constants.CATEGORY_ID_COLUMN_NAME} = c.Id
            
            GROUP BY {constants.CATEGORY_ID_COLUMN_NAME}
            '''
            
    def _get_sum_year_strings(self):
        '''
            Returns a list of strings separated by "+" with each 
            of the periods that make up each year.
        '''
        sum_year_strings = []
        
        for period in self.periods[:-3:4]:
            i = self.periods.index(period)
            sum_year_strings.append(
                f'{period}+{self.periods[i+1]}+{self.periods[i+2]}+{self.periods[i+3]}'
                )
            
        return sum_year_strings
        
        
    def _set_population_query(self):
        self.population_query = f'''
            SELECT Period, Population
            
            FROM Population
            
            WHERE {constants.TAC_COLUMN_NAME} = ?
                AND Period in {tuple(self.interval_periods)}
                
            ORDER BY Period
            '''
        
    def _set_category_totals(self):
        self.category_totals = utilities.execute_sql(
            sql_code=self.sales_tax_query,
            args=(self.jurisdiction.tac, ),
            db_name=constants.STATEWIDE_DATASETS_DB,
            fetchall=True,
            attach_db=constants.STARS_DB
            )
        
        
    def _set_population(self):
        query_results = utilities.execute_sql(
            sql_code=self.population_query,
            args=(self.jurisdiction.tac, ),
            db_name=constants.STATEWIDE_DATASETS_DB,
            fetchall=True
            )   
        
        if query_results:
            self.population = {
                period: population for period, population in query_results
                }
            
            
    def _set_totals(self):
        self.totals = [sum(x) for x in list(zip(*self.category_totals))[1:]]
        
         
    