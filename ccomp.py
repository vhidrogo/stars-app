'''
Created on Dec 19, 2018

@author: vahidrogo
'''

import sqlite3 as sql
from tkinter import messagebox as msg
import xlsxwriter

import constants
import utilities


class Ccomp:
    '''
    '''
    
    
    gray_color = '#dbdbdb'
    highlight_color = '#D7E4BC'

    format_properties = {
        'amount_header' : {'align' : 'center', 'bottom' : 2},
        
        'business_to_business_change' : {
            'left' : 2, 'left_color' : constants.B2B_COLOR,
            'num_format' : '0.0%'
            },
        
        'business_to_business_change_jurisdiction' : {
            'left' : 2, 'left_color' : constants.B2B_COLOR,
            'num_format' : '0.0%', 'bg_color' : highlight_color
            },
        
        'business_to_business_header' : {
            'bold' : True, 'bottom' : 2, 'font_color' : constants.B2B_COLOR, 
            'rotation' : 90
            },
        
        'construction_change' : {
            'left' : 2, 'left_color' : constants.CONSTRUCTION_COLOR,
            'num_format' : '0.0%'
            },
        
        'construction_change_jurisdiction' : {
            'left' : 2, 'left_color' : constants.CONSTRUCTION_COLOR,
            'num_format' : '0.0%', 'bg_color' : highlight_color
            },
        
        'construction_header' : {
            'bold' : True, 'font_color' : constants.CONSTRUCTION_COLOR, 
            'rotation' : 90, 'bottom' : 2, 
            },
        
        'county' : {
            'bg_color' : gray_color, 'bold' : True, 'italic' : True, 'top' : 2
            },
        
        'current_amount' : {'bold' : True, 'left' : 2, 'num_format' : '#,##0'},
        
        'current_amount_jurisdiction' : {
            'bg_color' : highlight_color, 'bold' : True, 'left' : 2, 
            'num_format' : '#,##0'  
            },
        
        'food_products_change' : {
            'left' : 2, 'left_color' : constants.FOOD_PRODUCTS_COLOR,
            'num_format' : '0.0%'
            },
        
        'food_products_change_jurisdiction' : {
            'left' : 2, 'left_color' : constants.FOOD_PRODUCTS_COLOR,
            'num_format' : '0.0%', 'bg_color' : highlight_color
            },
        
        'food_products_header' : {
            'bold' : True, 'font_color' : constants.FOOD_PRODUCTS_COLOR, 
            'rotation' : 90, 'bottom' : 2
            },
        
        'general_retail_change' : {
            'left' : 2, 'left_color' : constants.GENERAL_RETAIL_COLOR,
            'num_format' : '0.0%'
            },
        
        'general_retail_change_jurisdiction' : {
            'left' : 2, 'left_color' : constants.GENERAL_RETAIL_COLOR,
            'num_format' : '0.0%', 'bg_color' : highlight_color
            },
        
        'general_retail_header' : {
            'bold' : True, 'font_color' : constants.GENERAL_RETAIL_COLOR, 
            'rotation' : 90, 'bottom' : 2
            },
        
        'jurisdiction_highlight' : {'bg_color' : highlight_color},
        
        'jurisdiction_header' : {'bottom' : 2},
        
        'jurisdiction_name' : {'bg_color' : highlight_color, 'bold' : True},
        
        'last_row' : {'top' : 2},
        
        'miscellaneous_change' : {
            'left' : 2, 'left_color' : constants.MISC_COLOR, 
            'num_format' : '0.0%'
            },
        
        'miscellaneous_change_jurisdiction' : {
            'left' : 2, 'left_color' : constants.MISC_COLOR, 
            'num_format' : '0.0%', 'bg_color' : highlight_color
            },
        
        'miscellaneous_header' : {
            'bold' : True, 'bottom' : 2, 'font_color' : constants.MISC_COLOR, 
            'rotation' : 90
            },
        
        'prior_amount' : {'num_format' : '#,##0'},
        
        'prior_amount_jurisdiction' : {
            'num_format' : '#,##0', 'bg_color' : highlight_color
            },
        
        'segment_header' : {'align' : 'center', 'bottom' : 2},
        
        'title' : {'bold' : True, 'font_size' : 12},
        
        'total_change' : {'bold' : True, 'num_format' : '0.0%', 'right' : 2},
        
        'total_change_jurisdiction' : {
            'bg_color' : highlight_color, 'bold' : True, 
            'num_format' : '0.0%', 'right' : 2
            },
        
        'transportation_change' : {
            'left' : 2, 'left_color' : constants.TRANSPORTATION_COLOR,
            'num_format' : '0.0%'
            },
        
        'transportation_change_jurisdiction' : {
            'left' : 2, 'left_color' : constants.TRANSPORTATION_COLOR,
            'num_format' : '0.0%', 'bg_color' : highlight_color
            },
        
        'transportation_header' : {
            'bold' : True, 'font_color' : constants.TRANSPORTATION_COLOR, 
            'rotation' : 90, 'bottom' : 2
            }
        }
    
    sheet_properties = {
        'columns' : {
            'current_amount' : 7, 'prior_amount' : 8, 
            'first_category_change' : 1, 'first_segment' : 10, 
            'jurisdictions' : 0, 'last_category_change' : 6, 'last' : 13, 
            'total_change' : 9
            },
        
        'column_widths' : {
            'amount' : 12, 'change' : 7,  'name' : 27, 'segment' : 20
            },
        
        'rows' : {'title' : 0, 'headers' : 1, 'city_data' : 2}
        }
    
    output_name = 'CCOMP'
    
    output_type = 'xlsx'
    
    periods = ['current', 'prior']
    
    TOP_SEGMENT_CHANGE_COUNT = 2
    

    def __init__(self, controller):
        self.controller = controller
        self.selections = self.controller.selections
        
        self.output_saved = False
        
        self._set_prior_period()
        self._set_months()
        self._set_category_column_names()
        self._set_categories()
        
        # query to select the name, current amount and the prior year 
        # amount for each category in the city
        self.category_data_query = f'''
            SELECT name, {self.period_columns[self.periods[0]]}, 
                {self.period_columns[self.periods[1]]}
                
            FROM {constants.CATEGORY_TOTALS_TABLE}, 
                {constants.STARS_DB}.{constants.CATEGORIES_TABLE}
             
            WHERE {constants.TAC_COLUMN_NAME}=?
                AND {constants.CATEGORY_ID_COLUMN_NAME}
                    ={constants.STARS_DB}.{constants.CATEGORIES_TABLE}.
                        {constants.ID_COLUMN_NAME}
            '''
        
        # query to select the name, current amount and the prior year
        # amount for each segment in the city
        self.segment_data_query = f'''
            SELECT name, {self.period_columns[self.periods[0]]}, 
                {self.period_columns[self.periods[1]]}
                
            FROM {constants.SEGMENT_TOTALS_TABLE}, 
                {constants.STARS_DB}.{constants.SEGMENTS_TABLE}
             
            WHERE {constants.TAC_COLUMN_NAME}=?
                AND {constants.SEGMENT_ID_COLUMN_NAME}
                    ={constants.STARS_DB}.{constants.SEGMENTS_TABLE}.
                        {constants.ID_COLUMN_NAME}
            '''
        
        self.output_path = ''
        self.title = ''
        
        self.last_row = 0
        
        self.counties = []
        
        self.cities = {}
        
        self.city_data = {}
        
        self.formats = {}
        
        
    def _set_prior_period(self):
        self.prior_period = f'{self.selections.year-1}Q{self.selections.quarter}'
        
        
    def _set_months(self):
        quarter = self.selections.quarter
        
        if quarter == 1:
            month_one = 'January'
            month_two = 'March'
            
        elif quarter == 2:
            month_one = 'April'
            month_two = 'June'
            
        elif quarter == 3:
            month_one = 'July'
            month_two = 'September'
            
        else:
            month_one = 'October'
            month_two = 'December'
        
        self.month_one = month_one
        self.month_two = month_two
        
        
    def _set_category_column_names(self):
        self.period_columns = {}
        
        year = self.selections.year
        quarter = self.selections.quarter
        
        for column in self.periods:
            name = f'{constants.QUARTER_COLUMN_PREFIX}{year}q{quarter}'
            
            self.period_columns[column] = name
        
            year -= 1
            
            
    def _set_categories(self):
        self.categories = []
        
        query = f'''
            SELECT name
            FROM {constants.CATEGORIES_TABLE}
            '''
        
        results = utilities.execute_sql(
            sql_code=query, db_name=constants.STARS_DB, fetchall=True
            )
        
        if results:
            for i in results:
                self.categories.append(i[0])
        
    
    def main(self, jurisdiction):
        self.jurisdiction = jurisdiction
        
        self.controller.update_progress(
            0, f'{self.jurisdiction.id}: Preparing data.'
            )
        
        self._set_output_path()
        
        self._set_title()
        
        self._set_counties()
        
        self._set_cities()
        
        self._set_city_data()
        
        self.controller.update_progress(
            80, f'{self.jurisdiction.id}: Writing output.'
            )
        
        self._write_output()
        
        self.controller.update_progress(
            100, f'{self.jurisdiction.id}: Finished.'
            )
        
        if self.output_saved and self.selections.open_output:
            utilities.open_file(self.output_path)
        
        
    def _set_output_path(self):
        name = (
            f'{self.jurisdiction.id} {self.selections.period} {self.output_name}'
            )
        self.output_path = f'{self.jurisdiction.folder}{name}.{self.output_type}'
        
            
    def _set_title(self):
        self.title = (
            f'{self.jurisdiction.region_name.upper()}: Quarterly Comparison of '
            f'{self.prior_period} and {self.selections.period} ('
            f'{self.month_one} through {self.month_two} Sales)'
            )
            
            
    def _set_counties(self):
        query = f'''
            SELECT {constants.ID_COLUMN_NAME}, name
            FROM {constants.COUNTIES_TABLE}
            WHERE {constants.REGION_ID_COLUMN_NAME}=?
            '''
        
        args = (self.jurisdiction.region_id, )
        
        results = utilities.execute_sql(
            sql_code=query, args=args, db_name=constants.STARS_DB, fetchall=True
            )
        
        if results:
            for county_id, name in results:
                self.counties.append((county_id, name))
                
                
    def _set_cities(self):
        # query to select all cities in the county excluding the county pool
        query = f'''
            SELECT name, {constants.TAC_COLUMN_NAME} 
            FROM {constants.JURISDICTIONS_TABLE}
            WHERE {constants.COUNTY_ID_COLUMN_NAME}=? 
                AND {constants.TAC_COLUMN_NAME} NOT LIKE '%99'
            '''
        
        for county_id, county_name in self.counties:
            args = (county_id, )
            
            results = utilities.execute_sql(
                sql_code=query, args=args, db_name=constants.STARS_DB, fetchall=True
                )
            
            if results:
                # sorts by city name
                results.sort()
                
                self.cities[county_name] = results
                
                
    def _set_city_data(self):
        sql_code = 'ATTACH DATABASE ? AS ?'
        
        args = (
            str(constants.DB_PATHS[constants.STARS_DB]), 
            constants.STARS_DB
            )
        
        con = sql.connect(
            constants.DB_PATHS[constants.STATEWIDE_DATASETS_DB], uri=True,
            timeout=constants.DB_TIMEOUT
            )
           
        db_attached = utilities.execute_sql(
            sql_code=sql_code, args=args, open_con=con, dontfetch=True
            )
        
        if db_attached:
            for county_name, cities in self.cities.items():
                cities_data = {}
                
                for city_name, tac in cities:
                    include = True
                    
                    city_data = {}
                    
                    category_changes = {}
                    
                    args = (tac, )
                    
                    category_results = utilities.execute_sql(
                        sql_code=self.category_data_query, args=args, 
                        open_con=con, fetchall=True
                        )
                    
                    if category_results:
                        total_current = 0
                        total_prior = 0
                        
                        for category_name, current, prior in category_results:
                            # percent change for the category
                            change = utilities.percent_change(current, prior)
                            
                            category_changes[category_name] = change
                            
                            city_data['category_changes'] = category_changes
                            
                            total_current += current
                            total_prior += prior
                        
                        if total_current:
                            # percent change for the city 
                            total_change = utilities.percent_change(
                                total_current, total_prior
                                )   
                            
                            city_data['total_current'] = total_current
                            city_data['total_prior'] = total_prior
                            city_data['total_change'] = total_change
                            
                        else:
                            include = False
                        
                    else:
                        include = False
                        
                    if include:
                        segment_results = utilities.execute_sql(
                            sql_code=self.segment_data_query, args=args, 
                            open_con=con, fetchall=True
                            )
                        
                        amount_changes = []
                        
                        if segment_results:
                            for segment_name, current, prior in segment_results:
                                amount_change = current - prior
                                
                                amount_changes.append(
                                    (amount_change, segment_name)
                                    )
                            
                            # sorts by change lowest to highest   
                            amount_changes.sort()
                            
                            # stores the names of the top two largest segment 
                            # gains and declines
                            city_data['decline_one'] = amount_changes[0][1]  
                            city_data['decline_two'] = amount_changes[1][1]
                            city_data['gain_one'] = amount_changes[-1][1]
                            city_data['gain_two'] = amount_changes[-2][1]
                            
                    if include:
                        cities_data[city_name] = city_data
                    
                self.city_data[county_name] = cities_data
                
        con.close()
    

    def _write_output(self):
        self.wb = xlsxwriter.Workbook(self.output_path)
        self.ws = self.wb.add_worksheet(self.output_name)
        
        self.ws.set_row(1, 75)
        
        self._set_formats()
        
        self._write_title()
        
        self._write_jurisdiction_header()
        
        self._write_category_headers()
        
        self._write_current_amount_header()
        
        self._write_prior_amount_header()
        
        self._write_total_change_header()
        
        self._write_gain_headers()
        
        self._write_decline_headers()
        
        self._write_city_data()
        
        self._set_category_change_columns()
        
        self._set_amount_columns()
        
        self._set_segment_columns()
        
        self._set_name_column()
        
        self._write_footer()
        
        self._set_page()
        
        try:
            self.wb.close()
            
            self.output_saved = True
            
        except PermissionError:
            msg.showerror(
                self.selections.title, 
                f'Could not save to:\n\n{self.output_path}\n\nThere is '
                'a file with that name currently open.'
                )
        
        
    def _set_formats(self):
        self.formats = {
            name : self.wb.add_format(properties) 
            for name, properties in self.format_properties.items()
            }
        
        self.formats['amount_header'].set_text_wrap()
    
    
    def _write_title(self):
        row = self.sheet_properties['rows']['title']
        
        cell_format = self.formats['title']
        
        self.ws.write(row, row, self.title, cell_format)
        
        
    def _write_jurisdiction_header(self):
        row = self.sheet_properties['rows']['headers']
        column = self.sheet_properties['columns']['jurisdictions']
        
        cell_format = self.formats['jurisdiction_header']
        
        self.ws.write(row, column, '', cell_format)
        
        
    def _write_category_headers(self):
        row = self.sheet_properties['rows']['headers']
        column = self.sheet_properties['columns']['first_category_change']
        
        for category_name in self.categories:
            format_name = f'{category_name.lower().replace(" ", "_")}_header'
            
            cell_format = self.formats[format_name]
            
            self.ws.write(row, column, category_name.title(), cell_format)
            
            column += 1
            
            
    def _write_current_amount_header(self):
        row = self.sheet_properties['rows']['headers']
        column = self.sheet_properties['columns']['current_amount']
        
        value = (
            f'{self.month_one[:3]} - {self.month_two[:3]} '
            f'{self.selections.year} ({self.selections.period})'
            )
        
        self.ws.write(row, column, value, self.formats['amount_header'])
        
        
    def _write_prior_amount_header(self):
        row = self.sheet_properties['rows']['headers']
        column = self.sheet_properties['columns']['prior_amount']
        
        value = (
            f'{self.month_one[:3]} - {self.month_two[:3]} '
            f'{self.selections.year - 1} ({self.prior_period})'
            )
        
        self.ws.write(row, column, value, self.formats['amount_header'])
        
        
    def _write_total_change_header(self):
        row = self.sheet_properties['rows']['headers']
        column = self.sheet_properties['columns']['total_change']
        
        self.ws.write(row, column, '% Chg', self.formats['segment_header'])
        
        
    def _write_gain_headers(self):
        row = self.sheet_properties['rows']['headers']
        column = self.sheet_properties['columns']['first_segment']
        
        for _ in range(self.TOP_SEGMENT_CHANGE_COUNT):
            self.ws.write(row, column, 'Gain', self.formats['segment_header'])
            
            column += 1
        
        
    def _write_decline_headers(self):
        row = self.sheet_properties['rows']['headers']
        column = self.sheet_properties['columns']['first_segment'] + self.TOP_SEGMENT_CHANGE_COUNT
        
        for _ in range(self.TOP_SEGMENT_CHANGE_COUNT):
            self.ws.write(row, column, 'Decline', self.formats['segment_header'])
            
            column += 1
        
        
    def _write_city_data(self):
        row = self.sheet_properties['rows']['city_data']
        
        for county_name, cities_data in self.city_data.items():
            if cities_data:
                column = 0
                
                cell_format = self.formats['county']
                
                self.ws.merge_range(
                    row, column, row, self.sheet_properties['columns']['last'],
                    f'{county_name} county'.upper(), cell_format
                    )
                
                row += 1
                
                for city_name, city_data in cities_data.items():
                    column = 0
                    
                    is_main_jurisdiction = city_name == self.jurisdiction.name
                    
                    if is_main_jurisdiction:
                        cell_format = self.formats['jurisdiction_name']
                        
                        self.ws.write(row, column, city_name.upper(), cell_format)
                        
                    else:
                        self.ws.write(row, column, city_name.upper())
                        
                    column += 1
                    
                    category_changes = city_data['category_changes']
                    
                    for category in self.categories:
                        change = 0
                        
                        format_name = f'{category.lower().replace(" ", "_")}_change'
                        
                        if city_name == self.jurisdiction.name:
                            format_name += '_jurisdiction'
                        
                        cell_format = self.formats[format_name]
                        
                        if category in category_changes:
                            change = category_changes[category]
                        
                        self.ws.write(row, column, change, cell_format)
                        column += 1 
                        
                    for period in self.periods:
                        amount = city_data[f'total_{period}']
                        
                        format_name = f'{period}_amount'
                        
                        if is_main_jurisdiction:
                            format_name += '_jurisdiction'
                            
                        cell_format = self.formats[format_name]
                        
                        self.ws.write(row, column, amount, cell_format)
                        
                        column += 1
                    
                    format_name = 'total_change'
                    
                    if is_main_jurisdiction:
                        format_name += '_jurisdiction'
                        
                    self.ws.write(
                        row, column, city_data['total_change'], 
                        self.formats[format_name]
                        )
                    column += 1
                    
                    for i in ['gain_one', 'gain_two', 'decline_one', 'decline_two']:
                        if is_main_jurisdiction:
                            self.ws.write(
                                row, column, city_data[i].title(), 
                                self.formats['jurisdiction_highlight']
                                )
                            
                        else:
                            self.ws.write(row, column, city_data[i].title())
                    
                        column += 1
                    
                    row += 1
                
        self.last_row = row
                
        self._write_bottom_border(row)
        
        
    def _write_bottom_border(self, row):
        blank_row = [''] * (self.sheet_properties['columns']['last'] + 1)
        
        self.ws.write_row(row, 0, blank_row, self.formats['last_row'])
                
              
    def _set_category_change_columns(self):
        width = self.sheet_properties['column_widths']['change']
         
        start = self.sheet_properties['columns']['first_category_change']
        end = self.sheet_properties['columns']['last_category_change'] + 1
         
        for i in range(start, end):
            self.ws.set_column(i, i, width)
            
            
    def _set_name_column(self):
        width = self.sheet_properties['column_widths']['name']
        
        self.ws.set_column(0, 0, width)
            
            
    def _set_amount_columns(self):
        width = self.sheet_properties['column_widths']['amount']
        
        for period in self.periods:
            index = self.sheet_properties['columns'][f'{period}_amount']
            
            self.ws.set_column(index, index, width)
            
            
    def _set_segment_columns(self):
        width = self.sheet_properties['column_widths']['segment']
        
        start = self.sheet_properties['columns']['first_segment']
        end = self.sheet_properties['columns']['last'] + 1
        
        for i in range(start, end):
            self.ws.set_column(i, i, width)
            
            
    def _write_footer(self):
        footer = f'&L{constants.LEFT_NON_CONFIDENTIAL_FOOTER}&R{constants.RIGHT_FOOTER}'
        
        self.ws.set_footer(footer)
        
        
    def _set_page(self):
        self.ws.repeat_rows(0, 1)
        
        self.ws.set_landscape()
        
        self.ws.set_margins(left=0.25, right=0.15, top=0.5, bottom=0.5)
        
        column = self.sheet_properties['columns']['last']
        
        self.ws.print_area(0, 0, self.last_row, column)
        
        # 1 page wide and as long as necessary
        self.ws.fit_to_pages(width=1, height=0)
            
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
