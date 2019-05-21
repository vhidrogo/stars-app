'''
Created on May 21, 2019

@author: vahidrogo
'''

import pandas as pd
from tkinter import messagebox as msg
import xlsxwriter

import constants
import utilities

OUTPUT_NAME = 'Annualized Growth by Economic Category'
OUTPUT_TYPE = 'xlsx'

CATEGORY_CHANGE_COLUMN = 'cat_change'

SHEET_NAME = 'Jurisdiction & Region Charts'

MIN_YEARS = 2

DATA_NAMES = ['jurisdiction', 'region']

TITLE_FONT_SIZE = 14
LEGEND_FONT_SIZE = 13
DATA_LABEL_FONT_SIZE = 12


class AnnualizedGrowthChart:
    '''
        Outputs the "Annualized Growth by Economic Category" Excel chart.
    '''
    
    
    sheet_properties = {
        'cols': {
            'jurisdiction_chart': 0,
            'jurisdiction_data': 0,
            'print': 15,
            'region_chart': 8,
            'region_data': 3,
            },
        
        'rows': {
            'charts': 0,
            'data': 34,
            'print': 30,
            }
        }
    
    chart_properties = {
        'height': 620,
        'width': 510
        }
  

    def __init__(self, controller, selections):
        self.controller = controller
        self.selections = selections
        
        self.output_path = ''
        
        self.output_saved = False
        
        self.wb = None
        self.ws = None
        
        self.period_headers = []
        
        self.year_periods = []
        self.year_strings = []
        
        self.queries = {name: '' for name in DATA_NAMES}
        self.args = {name: () for name in DATA_NAMES}
        self.dfs = {name: None for name in DATA_NAMES}
        self.total_changes = {name: 0 for name in DATA_NAMES}
        
        
    def main(self, jurisdiction):
        if self.selections.years >= MIN_YEARS:
            self.jurisdiction = jurisdiction
            
            self.controller.update_progress(
                0, f'{self.jurisdiction.id}: Creating chart.'
                )
            
            self._set_year_periods()
            self._set_period_headers()
            self._set_year_strings()
            
            self._set_queries()
            self._set_args()
            self._set_dataframes()
            self._set_total_changes()
            self._set_category_changes()
           
            self._set_output_path()
            self._create_output()
            
            self.controller.update_progress(
                100, f'{self.jurisdiction.id}: Finished.'
                )
            
            if self.output_saved and self.selections.open_output:
                utilities.open_file(self.output_path)
                
        else:
            msg.showinfo(
                self.selections.title, 
                f'A minimum of ({MIN_YEARS}) are required to calculate growth.'
                )
            
            
    def _set_year_periods(self):
        period_count = (self.selections.years * 4)
        
        period_headers = utilities.get_period_headers(
            count=period_count,
            selections=self.selections,
            prefix=constants.QUARTER_COLUMN_PREFIX
            )
        
        # tuple with list of periods making up oldest and newest years
        self.year_periods = (period_headers[:4], period_headers[-4:])
            
            
    def _set_year_strings(self):
        self.year_strings = [
            '+'.join(periods) for periods in self.year_periods
            ]
        
        
    def _set_period_headers(self):
        period_headers = [x[-1] for x in self.year_periods]
        
        self.period_headers = [
            x.replace(
                constants.QUARTER_COLUMN_PREFIX, 
                constants.YEAR_COLUMN_PREFIX.upper()
                )
            for x in period_headers
            ]
        
        
    def _set_queries(self):
        self.queries['jurisdiction'] = f'''
            SELECT c.Name,{self.year_strings[0]},{self.year_strings[-1]}
            
            FROM {constants.CATEGORY_TOTALS_TABLE} t,
                {constants.CATEGORIES_TABLE} c
             
            WHERE {constants.TAC_COLUMN_NAME}=?
                AND {constants.CATEGORY_ID_COLUMN_NAME}=c.Id
            
            ORDER BY {constants.CATEGORY_ID_COLUMN_NAME}
            '''
        
        self.queries['region'] = f'''
            SELECT c.Name,{self.year_strings[0]},{self.year_strings[-1]}
            
            FROM {constants.CATEGORY_TOTALS_TABLE}{constants.REGION_SUFFIX} t,
                {constants.CATEGORIES_TABLE} c
             
            WHERE {constants.REGION_ID_COLUMN_NAME}=?
                AND {constants.CATEGORY_ID_COLUMN_NAME}=c.Id
            
            ORDER BY {constants.CATEGORY_ID_COLUMN_NAME}
            '''
        
    def _set_args(self):
        self.args['jurisdiction'] = (self.jurisdiction.tac, )
        self.args['region'] = (self.jurisdiction.region_id, )
        
        
    def _set_dataframes(self):
        for name in DATA_NAMES:
            data = utilities.execute_sql(
                sql_code=self.queries[name],
                args=self.args[name],
                db_name=constants.STATEWIDE_DATASETS_DB,
                fetchall=True,
                attach_db=constants.STARS_DB
                )
            
            self.dfs[name] = pd.DataFrame(
                data, columns=[constants.CATEGORY_COLUMN_NAME] + self.period_headers
                )
            
            
    def _set_category_changes(self):
        for name in DATA_NAMES:
            self.dfs[name][CATEGORY_CHANGE_COLUMN] = self.dfs[name].apply(
                lambda row: self._percent_change(row, name), axis=1
                )
            
            
    def _set_total_changes(self):
        for name in DATA_NAMES:
            old_total = sum(self.dfs[name][self.period_headers[0]])
            new_total = sum(self.dfs[name][self.period_headers[-1]])
            
            total_change = new_total - old_total
            
            self.total_changes[name] = total_change
            

    def _percent_change(self, row, name):
        return (
            (row[self.period_headers[1]] - row[self.period_headers[0]])
            /
            self.total_changes[name]
            )
        
        
    def _create_output(self):
        self.wb = xlsxwriter.Workbook(self.output_path)
        self.ws = self.wb.add_worksheet(SHEET_NAME)
        
        # hides the printed grid lines
        self.ws.hide_gridlines()
        
        self._create_charts()
        self._set_footer()
        self._set_page()
        self._output()
        
        
    def _create_charts(self):
        chart_row = self.sheet_properties['rows']['charts']
        data_row = self.sheet_properties['rows']['data']
        
        cell_bold_format = self.wb.add_format({
            'bold': True, 'bottom': True
            })
        
        cell_percent_format = self.wb.add_format({'num_format': '0.0%'})
        
        for name in DATA_NAMES:
            chart_col = self.sheet_properties['cols'][name + '_chart']
            data_col = self.sheet_properties['cols'][name + '_data']
            
            category_names = [
                x.title() 
                for x in self.dfs[name][constants.CATEGORY_COLUMN_NAME]
                ]
            
            category_count = len(category_names)
            
            # writes the data name
            self.ws.write(data_row, data_col, name + ' data', cell_bold_format)
            
            # writes the category names
            self.ws.write_column(data_row + 1, data_col, category_names)
            
            # writes the category changes
            self.ws.write_column(
                data_row + 1, data_col + 1, 
                self.dfs[name][CATEGORY_CHANGE_COLUMN], cell_percent_format
                )
            
            chart = self.wb.add_chart({
                'type': self.selections.type_option.lower()
                })
            
            chart.add_series({
                'values': [
                    SHEET_NAME, data_row + 1, data_col + 1, 
                    data_row + len(category_names), data_col + 1
                    ],
                
                'categories': [
                    SHEET_NAME, data_row + 1, data_col, 
                    data_row + category_count, data_col
                    ],
                
                'data_labels': {
                    'font': {
                        'bold': True, 'color': 'white', 
                        'size': DATA_LABEL_FONT_SIZE
                        }, 
                    'num_format': '0%', 'value': True
                    },
                
                'points': self._get_point_colors()
                })
            
            chart.set_title({
                'name': self._get_chart_title(name),
                'name_font': {
                    'name': 'Calibri',
                    'color': constants.BLUE_THEME_COLOR,
                    'size': TITLE_FONT_SIZE
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
            
            chart.set_size({
                'width': self.chart_properties['width'], 
                'height': self.chart_properties['height']
                })
            
            self._set_chart_legend(name, chart, category_count)
            
            self.ws.insert_chart(chart_row, chart_col, chart)
        
            data_col += 3
            
            
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
            
            
    def _set_chart_legend(self, data_name, chart, series_count):
        mid_series = series_count // 2
        
        # deletes the last three categories from the jurisdiction chart
        # legend and the first three from the region chart legend
        delete_series = (
            [i for i in range(mid_series, series_count)] if data_name == 'jurisdiction'
            else [i for i in range(mid_series)]
            )
        
        chart.set_legend({
            'position': 'bottom',
            'font': {
                'size': LEGEND_FONT_SIZE, 'bold': True, 
                'color': constants.BLUE_THEME_COLOR
                },
            'delete_series': delete_series
            })
        
        
    def _get_point_colors(self):
        return [
            {'fill': {'color': color}} for color in constants.THEME_COLORS.values()
            ]
            
            
    def _get_chart_title(self, data_name):
        area_name = (
            self.jurisdiction.name if data_name == 'jurisdiction'
            else f'{self.jurisdiction.region_name} Region'
            )
        
        if self.total_changes[data_name] < 0:
            direction = 'Decrease'
            change = 'Decline'
        else:
            direction = 'Increase'
            change = 'Growth' 
        
        return (
            f'{area_name.title()} - Total Sales Tax {direction} '
            f'${int(self.total_changes[data_name]):,} '
            f'{self.period_headers[0].replace("_", " ")} to '
            f'{self.period_headers[1].replace("_", " ")} {change} Sources:'
            )
        
        
    def _set_output_path(self):
        name = (
            f'{self.jurisdiction.id} {self.selections.period} {OUTPUT_NAME} '
            f'{self.selections.type_option} Chart'
            )
        
        self.output_path = f'{self.jurisdiction.folder}{name}.{OUTPUT_TYPE}'
        
        
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