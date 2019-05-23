'''
Created on May 23, 2019

@author: vahidrogo
'''

from tkinter import messagebox as msg
import xlsxwriter

import constants
import utilities


OUTPUT_NAME = 'Annualized Per Capita by Economic Category Chart'
OUTPUT_TYPE = 'xlsx'

SHEET_NAME = 'Per Capita Chart'

TITLE_FONT_SIZE = 14

AXIS_FONT_SIZE = 12

DATA_LABEL_FONT_SIZE = 12
LEGEND_FONT_SIZE = 13

X_AXIS_ROTATION = 45


class AnnualizedPerCapitaChart:
    '''
        Creates the "Annualized Per Capita by Economic Category" Excel chart.
    '''
    
    
    sheet_properties = {
        'cols': {
            'chart': 0,
            'data': 0,
            'print': 15,
            },
        
        'rows': {
            'chart': 0,
            'data': 34,
            'print': 30,
            }
        }
    
    chart_properties = {
        'height': 620,
        'width': 1020
        }
    
    
    def __init__(self, controller, selections):
        self.controller = controller
        self.selections = selections
        
        self.output_path = ''
        self.sales_tax_query = ''
        
        self.category_count = 0
        
        self.output_saved = False
        
        self.jurisdiction = None
        
        self.wb = None
        self.ws = None
        
        self.category_totals = ()
        
        self.category_per_capita = []
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
        
        if self.category_totals:
            self.category_count = len(self.category_totals)
            
            self._set_population()
            
            if self.population:
                self._set_totals()
                self._set_category_per_capita()
               
                self._set_output_path()
                self._create_output()
                
                if self.output_saved and self.selections.open_output:
                    utilities.open_file(self.output_path)

        
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
        
        
    def _set_category_per_capita(self):
        for x in self.category_totals:
            category_data = [x[0]]
            totals = x[1:]
            
            for total, population in zip(totals, self.population.values()):
                category_data.append(int(total // population))
                
            self.category_per_capita.append(category_data)
        
        
    def _set_output_path(self):
        name = (
            f'{self.selections.period} {self.jurisdiction.id} {OUTPUT_NAME}'
            )
        
        self.output_path = f'{self.jurisdiction.folder}{name}.{OUTPUT_TYPE}'
        
        
    def _create_output(self):
        self.wb = xlsxwriter.Workbook(self.output_path)
        self.ws = self.wb.add_worksheet(SHEET_NAME)
        
        self._write_per_capita_data()
        self._write_x_labels()
        self._create_chart()
        self._set_footer()
        self._set_page()
        self._output()
        
        
    def _write_per_capita_data(self):
        row = self.sheet_properties['rows']['data']
        col = self.sheet_properties['cols']['data']
        
        header_format = self.wb.add_format({'bold': True, 'bottom': True})
        amount_format = self.wb.add_format({'num_format': '$#,##0'})
        
        # writes the category name header
        self.ws.write(row, col, 'Category', header_format)
        row += 1
        
        # writes the per capita data
        for x in self.category_per_capita:
            self.ws.write_row(row, col, x, amount_format)
            row += 1
            
            
    def _write_x_labels(self):
        row = self.sheet_properties['rows']['data']
        col = self.sheet_properties['cols']['data'] + 1
        
        labels = [
            f'{period}: ${int(total // self.population[period]):,}' 
            for period, total in zip(self.interval_periods, self.totals)
            ]
        
        self.ws.write_row(row, col, labels)
        
        
    def _create_chart(self):
        x_label_row = self.sheet_properties['rows']['data']
        data_row = x_label_row + 1
        
        first_data_col = self.sheet_properties['cols']['data']
        last_data_col = first_data_col + self.selections.years
        
        chart = self.wb.add_chart({'type': 'column', 'subtype': 'stacked'})
        
        for x in self.category_per_capita:
            category = x[0]
            
            color = constants.THEME_COLORS[
                category.lower().replace(' ', '_')
                ]
            
            chart.add_series({
                'values': [
                        SHEET_NAME, 
                        data_row, first_data_col + 1, data_row, last_data_col
                        ],
                
                'categories': [
                    SHEET_NAME, 
                    x_label_row, first_data_col + 1, x_label_row, last_data_col
                    ],
                
                'name': [SHEET_NAME, data_row, first_data_col], 
                
                'data_labels': {
                    'value': True,
                    'font': {
                        'color': 'white', 
                        'size': DATA_LABEL_FONT_SIZE
                        }
                    },
                
                'fill': {'color': color}
                })
            
            data_row += 1
        
        chart.set_size({
            'width': self.chart_properties['width'],
            'height': self.chart_properties['height']
            })
        
        chart.set_title({
            'name': self._get_chart_title(),
            'name_font': {
                'name': 'Calibri',
                'color': constants.BLUE_THEME_COLOR,
                'size': TITLE_FONT_SIZE
                }
            })
        
        chart.set_y_axis({
            'num_font': {
                'color': constants.BLUE_THEME_COLOR,
                'size': AXIS_FONT_SIZE
                }
            })
        
        chart.set_x_axis({
            'num_font': {
                'color': constants.BLUE_THEME_COLOR,
                'rotation': X_AXIS_ROTATION,
                'size': AXIS_FONT_SIZE
                }
            })
        
        chart.set_legend({
            'position': 'bottom',
            'font': {
                'size': LEGEND_FONT_SIZE, 'bold': True, 
                'color': constants.BLUE_THEME_COLOR
                }
        })
        
        chart.set_plotarea({
        'border' : {'none' : True},
        'fill' : {'none' : True}
        })
     
        chart.set_chartarea({
            'border' : {'none' : True},
            'fill' : {'none' : True}
            })
                
        self.ws.insert_chart(
            self.sheet_properties['rows']['chart'],
            self.sheet_properties['cols']['chart'],
            chart
            )
        
        
    def _get_chart_title(self):
        juri_header = utilities.fetch_jurisdiction_header(self.jurisdiction.name)
        return f'{juri_header.title()}\nAnnualized Sales Tax Per Capita'
        
        
    def _set_footer(self):
        '''
            Sets the left and right footers.
        '''
        footer = (
            f'&L{constants.LEFT_NON_CONFIDENTIAL_FOOTER}'
            f'&R{constants.RIGHT_FOOTER}'
            )
        
        self.ws.set_footer(footer)
            
            
    def _set_page(self):
        self.ws.set_landscape()
        
        self.ws.set_margins(left=0.5, right=0.5, top=0.5, bottom=0.5)
        
        last_row = self.sheet_properties['rows']['print']
        last_col = self.sheet_properties['cols']['print']
        
        self.ws.print_area(0, 0, last_row, last_col)
        
        self.ws.fit_to_pages(width=1, height=1)
        
        
    def _output(self):
        try:
            self.wb.close()
            self.output_saved = True
            
        except PermissionError:
            msg.showerror(
                self.selections.title,
                f'Failed to save to:\n\n{self.output_path}\n\n'
                'A file at that path is currently open.'
                )
        
         
    