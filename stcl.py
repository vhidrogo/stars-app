'''
Created on Dec 19, 2018

@author: vahidrogo
'''

from operator import itemgetter
import sqlite3 as sql
from tkinter import messagebox as msg
import xlsxwriter

import constants
import utilities


CHART_FONT_SIZE = 11
TABLE_FONT_SIZE = 10

EBI_TABLE_NAME = EBI_COLUMN_NAME = 'ebi'


class Stcl:
    '''
    '''
    
    
    # column index and value pairs for each of the column table_headers
    table_headers = {
        2: 'Actual Sales Tax', 3: 'Potential Sales Tax', 
        4: 'Capture / Gap', 5: 'Rate'
    }
    
    format_properties = {
        'business_code_amount': {
            'font_size': TABLE_FONT_SIZE, 'num_format': 0x05
            },
        
        'business_code_name': {
            'font_size': TABLE_FONT_SIZE, 'indent': 1, 'italic': True
            },
        
        'business_code_percent': {
            'font_size': TABLE_FONT_SIZE, 'num_format': '0%'
            },
        
        'business_to_business_amount': {
            'bg_color': constants.B2B_COLOR, 'bold': True, 
            'font_color': 'white' , 'font_size': TABLE_FONT_SIZE, 
            'num_format': 0x05
            },
        
        'business_to_business_percent': {
            'bg_color': constants.B2B_COLOR, 'bold': True, 
            'font_color': 'white' , 'font_size': TABLE_FONT_SIZE, 
            'num_format': '0%'
            },
        
        'chart_message': {'font_size': 11},
        
        'construction_amount': {
            'bg_color': constants.CONSTRUCTION_COLOR, 'bold': True, 
            'font_color': 'white', 'font_size': TABLE_FONT_SIZE, 
            'num_format': 0x05
            },
         
         'construction_percent': {
            'bg_color': constants.CONSTRUCTION_COLOR, 'bold': True, 
            'font_color': 'white', 'font_size': TABLE_FONT_SIZE, 
            'num_format': '0%'
            },
         
        'food_products_amount': {
            'bg_color': constants.FOOD_PRODUCTS_COLOR, 'bold': True,
            'font_size': TABLE_FONT_SIZE, 'num_format': 0x05
            },
        
        'food_products_percent': {
            'bg_color': constants.FOOD_PRODUCTS_COLOR, 'bold': True,
            'font_size': TABLE_FONT_SIZE, 'num_format': '0%'
            },
        
        'general_retail_amount': {
            'bg_color': constants.GENERAL_RETAIL_COLOR, 'bold': True,
            'font_color': 'white', 'font_size': TABLE_FONT_SIZE, 
            'num_format': 0x05
            },
        
        'general_retail_percent': {
            'bg_color': constants.GENERAL_RETAIL_COLOR, 'bold': True,
            'font_color': 'white', 'font_size': TABLE_FONT_SIZE, 
            'num_format': '0%'
            },
        
        'header': {
            'align': 'right', 'bold': True, 'font_size': TABLE_FONT_SIZE
            },
        
        'legend_header': {'bold': True, 'bottom': True, 'font_size': 11},
        
        'miscellaneous_amount': {
            'bg_color': constants.MISC_COLOR, 'bold': True,
            'font_color': 'white', 'font_size': TABLE_FONT_SIZE, 
            'num_format': 0x05
            },
        
        'miscellaneous_percent': {
            'bg_color': constants.MISC_COLOR, 'bold': True,
            'font_color': 'white', 'font_size': TABLE_FONT_SIZE, 
            'num_format': '0%'
            },
        
        'segment_amount': {
            'bg_color': constants.GRAY_COLOR, 'bold': True, 
            'font_size': TABLE_FONT_SIZE, 'num_format': 0x05
            },
        
        'segment_percent': {
            'bg_color': constants.GRAY_COLOR, 'bold': True, 
            'font_size': TABLE_FONT_SIZE, 'num_format': '0%'
            },
        
        'title': {'align': 'center', 'bold': True, 'font_size': 14},
        
        'total_amount': {
            'bold': True, 'bottom': 2, 'font_size': TABLE_FONT_SIZE, 
            'num_format': 0x06, 'top': True
            },
        
        'total_border' : {'bottom': 2, 'bg_color': 'black', 'top': True},
        
        'total_percent': {
            'bold': True, 'bottom': 2, 'font_size': TABLE_FONT_SIZE, 
            'num_format': '0%', 'top': True
            },
        
        'transportation_amount': {
            'bg_color': constants.TRANSPORTATION_COLOR, 'bold': True,
            'font_color': 'white', 'font_size': TABLE_FONT_SIZE, 
            'num_format': 0x05
            },
        
        'transportation_percent': {
            'bg_color': constants.TRANSPORTATION_COLOR, 'bold': True,
            'font_color': 'white', 'font_size': TABLE_FONT_SIZE, 
            'num_format': '0%'
            },
        
        'verbiage': {
            'align': 'left', 'font_size': TABLE_FONT_SIZE, 'indent': 0, 
            'italic': True
            }
        }
    
    sheet_properties = {
        'column_widths': {0: 2, 1: 25, 2: 20, 3: 20, 4: 20, 5: 15},
        
        'columns': {'last': 5},
        
        'name': 'STCL',
        
        'row_heights': {0: 18, 2: 40},
        
        'rows': {'header': 4, 'table': 5, 'title': 0, 'verbiage': 2},
        
        'table_row_height': 12.75
        }
    
    chart_sheet_properties = {
        'data_row': 0,
        
        'first_column': 4,
        
        'first_row': 0,
        
        'label_column': 0,
        
        'last_column': 18,
        
        'last_row': 38,
        
        'legend_row': 31,
        
        'message_column': 8,
        
        'name': 'Chart',
        
        'value_column': 1 
    }
    
    chart_properties = {
        'gap': 50,
        'height': 600,
        'width': 950
        }
    
    consumer_categories = [
        'general retail', 'food products', 'transportation', 'construction'
        ]
    
    output_name = 'STCL'
    
    output_type = 'xlsx'
    
    
    def __init__(self, contorller):
        self.controller = contorller
        self.selections = self.controller.selections
        
        self.chart_message = ''
        self.bmy_periods_string = ''
        self.bmy_periods_string_county = ''
        self.output_path = ''
        self.report_title = ''
        self.verbiage = ''
        
        self.business_to_business_rate = 0
        self.consumer_total_rate = 0
        self.jurisdiction_consumer_total = 0
        self.jurisdiction_ebi = 0
        self.jurisdiction_total = 0
        self.last_row = 0
        self.miscellaneous_rate = 0
        self.potential_consumer_total = 0
        self.potential_total = 0
        self.region_ebi = 0
        self.region_share = 0
        
        self.category_format = None
        
        self.is_countywide = False
        
        self.data_available = False
        self.output_saved = False
        
        self.business_code_totals = {}
        self.business_code_totals_region = {}
        self.category_totals = {}
        self.category_totals_region = {}
        self.segment_totals = {}
        self.segment_totals_region = {}
        
        self.chart_data = {}
        
        self._set_business_codes()
        self._set_segments()
        self._set_categories()
        
        
    def _set_business_codes(self):
        '''
            Stores the business codes and their ids in a dictionary with the 
            id as the key and the name as the value inside a nested dictionary
            with the sgment_id as the key.
        '''
        self.business_codes = {}
          
        query = f'''
            SELECT {constants.SEGMENT_ID_COLUMN_NAME}, 
                Id, name
            
            FROM {constants.BUSINESS_CODES_TABLE}
            '''
          
        results = utilities.execute_sql(
            sql_code=query, db_name=constants.STARS_DB, fetchall=True
            )
          
        if results:
            # sorts by the business code name
            results = sorted(results, key=itemgetter(2))
            
            for segment_id, business_code_id, name in results:
                if name != 'BLANK':
                    if segment_id not in self.business_codes:
                        self.business_codes[segment_id] = {}
                        
                    self.business_codes[segment_id][business_code_id] = name
         
 
    def _set_segments(self):
        '''
            Stores the segment ids and their names.
        '''
        self.segments = {}
          
        query = f'''
            SELECT {constants.CATEGORY_ID_COLUMN_NAME}, 
                Id, name
            
            FROM {constants.SEGMENTS_TABLE}
            '''
          
        results = utilities.execute_sql(
            sql_code=query, db_name=constants.STARS_DB, fetchall=True
            )
          
        if results:
            # sorts by the segment name
            results = sorted(results, key=itemgetter(2))
            
            for category_id, segment_id, name in results:
                if category_id not in self.segments:
                    self.segments[category_id] = {}
                    
                self.segments[category_id][segment_id] = name
                 
                 
    def _set_categories(self):
        query = f'''
            SELECT Id, name
            FROM {constants.CATEGORIES_TABLE}
            '''
          
        self.categories = utilities.execute_sql(
            sql_code=query, db_name=constants.STARS_DB, fetchall=True
            )
        
    
    def main(self, jurisdiction):
        self.jurisdiction = jurisdiction
        
        self.controller.update_progress(
            0, f'{self.jurisdiction.id}: Fetching EBI data.'
            )
        
        self.is_countywide = ('Countywide' in self.jurisdiction.name)
        
        self._set_jurisdiction_ebi()
        self._set_region_ebi()
        
        if self.jurisdiction_ebi and self.region_ebi:
            self.controller.update_progress(
                5, f'{self.jurisdiction.id}: Fetching economic totals.'
                )
              
            self.region_share = self.jurisdiction_ebi / self.region_ebi
                
            self._set_bmy_periods_string()
            
            self._set_data()
            
            # if all the data is ready for both the jurisdiction and the region
            if self.data_available:
                self.verbiage = (
                    f"Actual Sales Tax: {self.jurisdiction.name}'s sales tax by "
                    "economic category, economic segment and business code.\n"
                    f"Potential Sales Tax: {self.jurisdiction.name}'s actual sales "
                    "tax multiplied by its effective buying income divided by the "
                    "regional effective buying income. In other words, the potential "
                    f"sales tax from {self.jurisdiction.name}'s residents' income when "
                    f"following the {self.jurisdiction.region_name.title()} region's buying patterns."
                    )
                    
                self.chart_message = (
                    "The chart provides an overview of how well "
                    f"{self.jurisdiction.name} is capturing potential sales tax "
                    "based on its residents' effective buying income "
                    "(disposable income) compared to "
                    f"{self.jurisdiction.region_name.title()} regional "
                    "purchasing habits. The dotted line is at 100% capture."
                    )
                        
                self._set_report_title()
                        
                self._set_output_path()
                    
                self.controller.update_progress(
                    20, 
                    f'{self.jurisdiction.id}: Writing {self.output_type} file.'
                    )
                  
                self._write_output()
                     
                self.controller.update_progress(
                    100, f'{self.jurisdiction.id}: Finished.'
                    )
                     
                if self.output_saved and self.selections.open_output:
                    utilities.open_file(self.output_path)
            
            
    def _set_jurisdiction_ebi(self):
        if self.is_countywide:
            query = f'''
                SELECT SUM({EBI_COLUMN_NAME}) 
                
                FROM {EBI_COLUMN_NAME} e,
                    {constants.JURISDICTIONS_TABLE} j
                    
                WHERE e.Id=j.{constants.TAC_COLUMN_NAME}
                    AND j.HasData=1
                    AND j.{constants.COUNTY_ID_COLUMN_NAME}=?
                '''
            args = (self.jurisdiction.county_id, )
            attach_db = 'starsdb'
            
        else:
            query = f'''
                SELECT {EBI_COLUMN_NAME}
                FROM {EBI_COLUMN_NAME}
                WHERE Id=?
                '''
            args = (self.jurisdiction.tac, )
            attach_db = ''
        
        results = utilities.execute_sql(
            sql_code=query, args=args, attach_db=attach_db,
            db_name=constants.STATEWIDE_DATASETS_DB
            )
        
        if results and results[0] is not None:
            self.jurisdiction_ebi = results[0] // 1000
        
            
    def _set_region_ebi(self):
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
            query = f'''
                SELECT SUM(ebi)
                
                FROM ebi e, {constants.COUNTIES_TABLE} c, 
                    {constants.JURISDICTIONS_TABLE} j
                    
                WHERE e.Id=j.{constants.TAC_COLUMN_NAME}
                    AND j.HasData=1
                    AND j.{constants.COUNTY_ID_COLUMN_NAME}=c.Id
                    AND c.{constants.REGION_ID_COLUMN_NAME}=?
                '''
            
            args = (self.jurisdiction.region_id, )
            
            results = utilities.execute_sql(
                sql_code=query, args=args, open_con=con
                )
             
            if results:
                self.region_ebi = results[0] // 1000
            
            
    def _set_bmy_periods_string(self):
        '''
            Concatenates string with the column names of the most recent four 
            periods to use when querying the data.
        '''
        periods = []
        
        year = self.selections.year
        quarter = self.selections.quarter
        
        for _ in range(constants.BMY_PERIOD_COUNT):
            periods.append(f'{constants.QUARTER_COLUMN_PREFIX}{year}Q{quarter}')
            
            if quarter == 1:
                quarter = 4
                year -= 1
            
            else:
                quarter -= 1
            
        self.bmy_periods_string = '+'.join(periods)
        
        if self.is_countywide:
            self.bmy_periods_string_county = '+'.join(
                [f'SUM({period})' for period in periods]
                )
        
        
    def _set_data(self):
        if self.is_countywide:
            self._set_category_totals_countywide()
        else:
            self._set_category_totals()
        
        if self.category_totals:
            self._set_category_totals_region()
             
            if self.category_totals_region:
                if self.is_countywide:
                    self._set_segment_totals_countywide()
                else:
                    self._set_segment_totals()
                
                if self.segment_totals:
                    self._set_segment_totals_region()
                    
                    if self.segment_totals_region:
                        if self.is_countywide:
                            self._set_business_code_totals_countywide()
                        else:
                            self._set_business_code_totals()
                        
                        if self.business_code_totals:
                            self._set_business_code_totals_region()
                              
                            if self.business_code_totals_region:
                                self.data_available = True
        

    def _set_category_totals(self):
        '''
            Fetches the current period category totals for the jurisdiction 
            and stores the amounts in a dictionary with the category id as the 
            key and the amount as the value.
        '''
        query = f'''
            SELECT {constants.CATEGORY_ID_COLUMN_NAME}, {self.bmy_periods_string}
            FROM {constants.CATEGORY_TOTALS_TABLE}
            WHERE {constants.TAC_COLUMN_NAME}=?
            '''
        
        args = (self.jurisdiction.tac, )
         
        results = utilities.execute_sql(
            sql_code=query, args=args, 
            db_name=constants.STATEWIDE_DATASETS_DB, fetchall=True
            )
        
        if results:
            for category_id, amount in results:
                self.category_totals[category_id] = amount
                
                
    def _set_category_totals_countywide(self):
        query = f'''
            SELECT {constants.CATEGORY_ID_COLUMN_NAME}, {self.bmy_periods_string_county}
            
            FROM {constants.CATEGORY_TOTALS_TABLE} t,
                {constants.JURISDICTIONS_TABLE} j
            
            WHERE t.{constants.TAC_COLUMN_NAME}=j.{constants.TAC_COLUMN_NAME}
                AND j.{constants.COUNTY_ID_COLUMN_NAME}=?
            
            GROUP BY {constants.CATEGORY_ID_COLUMN_NAME}
            '''
        
        args = (self.jurisdiction.county_id, )
         
        results = utilities.execute_sql(
            sql_code=query, args=args, attach_db='starsdb',
            db_name=constants.STATEWIDE_DATASETS_DB, fetchall=True
            )
        
        if results:
            for category_id, amount in results:
                self.category_totals[category_id] = amount
                 
                 
    def _set_category_totals_region(self):
        '''
        '''
        query = f'''
            SELECT {constants.CATEGORY_ID_COLUMN_NAME}, {self.bmy_periods_string}
            FROM {constants.CATEGORY_TOTALS_TABLE}{constants.REGION_SUFFIX}
            WHERE {constants.REGION_ID_COLUMN_NAME}=?
            '''
        
        args = (self.jurisdiction.region_id, )
        
        results = utilities.execute_sql(
            sql_code=query, args=args, db_name=constants.STATEWIDE_DATASETS_DB, 
            fetchall=True
            )
        
        if results:
            for category_id, amount in results:
                self.category_totals_region[category_id] = amount
                
                
    def _set_segment_totals(self):
        '''
            Fetches the current period segment totals for the jurisdiction
            and stores in a dictionary with the segment id as the key
            amount as the value.
        '''
        query = f'''
            SELECT {constants.SEGMENT_ID_COLUMN_NAME}, {self.bmy_periods_string}
            FROM {constants.SEGMENT_TOTALS_TABLE}
            WHERE {constants.TAC_COLUMN_NAME}=?
            '''
        
        args = (self.jurisdiction.tac, )
        
        results = utilities.execute_sql(
            sql_code=query, args=args, db_name=constants.STATEWIDE_DATASETS_DB, 
            fetchall=True
            )
        
        if results:
            for segment_id, amount in results:
                self.segment_totals[segment_id] = amount
                
                
    def _set_segment_totals_countywide(self):
        query = f'''
            SELECT {constants.SEGMENT_ID_COLUMN_NAME}, {self.bmy_periods_string_county}
            
            FROM {constants.SEGMENT_TOTALS_TABLE} t,
                {constants.JURISDICTIONS_TABLE} j
            
            WHERE t.{constants.TAC_COLUMN_NAME}=j.{constants.TAC_COLUMN_NAME}
                AND j.{constants.COUNTY_ID_COLUMN_NAME}=?
            
            GROUP BY {constants.SEGMENT_ID_COLUMN_NAME}
            '''
        
        args = (self.jurisdiction.county_id, )
        
        results = utilities.execute_sql(
            sql_code=query, args=args, db_name=constants.STATEWIDE_DATASETS_DB, 
            fetchall=True, attach_db='starsdb'
            )
        
        if results:
            for segment_id, amount in results:
                self.segment_totals[segment_id] = amount
    
    
    def _set_segment_totals_region(self):
        query = f'''
            SELECT {constants.SEGMENT_ID_COLUMN_NAME}, {self.bmy_periods_string}
            FROM {constants.SEGMENT_TOTALS_TABLE}{constants.REGION_SUFFIX}
            WHERE {constants.REGION_ID_COLUMN_NAME}=?
            '''
        
        args = (self.jurisdiction.region_id, )
        
        results = utilities.execute_sql(
            sql_code=query, args=args, db_name=constants.STATEWIDE_DATASETS_DB, 
            fetchall=True
            )
        
        if results:
            for segment_id, amount in results:
                self.segment_totals_region[segment_id] = amount
                
                
    def _set_business_code_totals(self):
        '''
            Fetches the current period business code totals for the jurisdiction
        '''
        query = f'''
            SELECT {constants.BUSINESS_CODE_ID_COLUMN_NAME}, {self.bmy_periods_string}
            FROM {constants.BUSINESS_CODE_TOTALS_TABLE}
            WHERE {constants.TAC_COLUMN_NAME}=?
            '''
        
        args = (self.jurisdiction.tac, )
        
        results = utilities.execute_sql(
            sql_code=query, args=args, db_name=constants.STATEWIDE_DATASETS_DB,
            fetchall=True
            )
        
        if results:
            for business_code_id, amount in results:
                self.business_code_totals[business_code_id] = amount
                
                
    def _set_business_code_totals_countywide(self):
        query = f'''
            SELECT {constants.BUSINESS_CODE_ID_COLUMN_NAME}, {self.bmy_periods_string_county}
            
            FROM {constants.BUSINESS_CODE_TOTALS_TABLE} t,
                {constants.JURISDICTIONS_TABLE} j
            
            WHERE t.{constants.TAC_COLUMN_NAME}=j.{constants.TAC_COLUMN_NAME}
                AND j.{constants.COUNTY_ID_COLUMN_NAME}=?
            
            GROUP BY {constants.BUSINESS_CODE_ID_COLUMN_NAME}
            '''
        
        args = (self.jurisdiction.county_id, )
        
        results = utilities.execute_sql(
            sql_code=query, args=args, db_name=constants.STATEWIDE_DATASETS_DB,
            fetchall=True, attach_db='starsdb'
            )
        
        if results:
            for business_code_id, amount in results:
                self.business_code_totals[business_code_id] = amount
    
    
    def _set_business_code_totals_region(self):
        query = f'''
            SELECT {constants.BUSINESS_CODE_ID_COLUMN_NAME}, {self.bmy_periods_string}
            FROM {constants.BUSINESS_CODE_TOTALS_TABLE}{constants.REGION_SUFFIX}
            WHERE {constants.REGION_ID_COLUMN_NAME}=?
            '''
        
        args = (self.jurisdiction.region_id, )
        
        results = utilities.execute_sql(
            sql_code=query, args=args, db_name=constants.STATEWIDE_DATASETS_DB, 
            fetchall=True
            )
        
        if results:
            for business_code_id, amount in results:
                self.business_code_totals_region[business_code_id] = amount
            

    def _set_report_title(self):
        quarter_suffix = self._quarter_suffix()
        
        self.report_title = (
            f'{self.jurisdiction.name}: {self.selections.quarter}'
            f'{quarter_suffix} Quarter {self.selections.year} Sales Tax '
            'Capture & Gap Analysis'
            )
        
        
    def _quarter_suffix(self):
        quarter = self.selections.quarter
        
        if quarter == 1:
            suffix = 'st'
        
        elif quarter == 2:
            suffix = 'nd'
        
        elif quarter == 3:
            suffix = 'rd'
        
        else:
            suffix = 'th'
            
        return suffix
          
            
    def _set_output_path(self):
        name = (
            f'{self.jurisdiction.id} {self.selections.period} {self.output_name}'
            )
        self.output_path = f'{self.jurisdiction.folder}{name}.{self.output_type}'
        
        
    def _write_output(self):
        self.wb = xlsxwriter.Workbook(self.output_path)
        
        self._write_table_sheet()
        self._write_chart_sheet()
        
        try:
            self.wb.close()
            
            self.output_saved = True
            
        except PermissionError:
            msg.showerror(
                self.selections.title, 
                f'Could not save to:\n\n{self.output_path}\n\nThere is '
                'a file with that name currently open.'
                )
            
            
    def _write_table_sheet(self):
        self.table_ws = self.wb.add_worksheet(self.sheet_properties['name'])
        
        # repeats all the rows up to the header
        self.table_ws.repeat_rows(0, self._sheet_row('header'))
        
        # hides the printed gridlines
        self.table_ws.hide_gridlines()
        
        self._set_formats()
        
        self._write_report_title(self.table_ws)
        
        self._write_verbiage()
        
        self._write_header()
        
        self._write_table_data()
        
        self._write_total_row()
        
        self._write_table_sheet_footer()
        
        self._set_top_rows()
        self._set_table_rows()
        
        self._set_columns()
        
        self._set_table_page()
        
 
    def _set_formats(self):
        self.formats = {
            name: self.wb.add_format(properties) 
            for name, properties in self.format_properties.items()
            }
        
        self.formats['chart_message'].set_text_wrap()
        self.formats['verbiage'].set_text_wrap()
                    
                    
    def _sheet_row(self, name):
        return self.sheet_properties['rows'][name]
    
    
    def _sheet_column(self, name):
        return self.sheet_properties['columns'][name]
            
          
    def _write_report_title(self, worksheet):
        row = self._sheet_row('title')
        last_column = self._sheet_column('last')
        
        cell_format = self.formats['title']
        
        worksheet.merge_range(
            row, 0, row, last_column, self.report_title, cell_format
            )
        
        
    def _write_verbiage(self):
        row = self._sheet_row('verbiage')
        last_column = self._sheet_column('last')
        
        cell_format = self.formats['verbiage']
        
        self.table_ws.merge_range(
            row, 0, row, last_column, self.verbiage, cell_format
            )
        
        
    def _write_header(self):
        row = self._sheet_row('header')
        
        cell_format = self.formats['header']
        
        for column_index, value in self.table_headers.items():
            self.table_ws.write(row, column_index, value, cell_format)
            
            
    def _write_table_data(self):
        row = self._sheet_row('table')
        
        for category_id, category_name in self.categories:
            self._write_category_row(row, category_id, category_name)
            row += 1
            
            self.chart_data[category_name] = {}
            
            category_segments = self.segments[category_id]
            
            for segment_id, segment_name in category_segments.items():
                self._write_segment_row(
                    row, segment_id, segment_name, category_name
                    )
                row += 1
                
                business_codes = self.business_codes[segment_id]
                
                # if these is more than one business code for the segment
                if len(business_codes) > 1:
                    for business_code_id, business_code_name in business_codes.items():
                        self._write_business_code_row(
                            row, business_code_id, business_code_name
                            )
                        
                        row += 1
            
            # if its the last consumer category
            if category_name.lower() == 'construction':
                row += 1
                self._write_consumer_total_row(row)
                row += 1
            
            row += 1
            
        self.last_row = row + 1
        
            
    def _write_category_row(self, row, category_id, category_name):
        self.category_format = self.formats[
            f'{category_name.lower().replace(" ", "_")}_amount'
            ]
            
        percent_format = self.formats[
            f'{category_name.lower().replace(" ", "_")}_percent'
            ]
        
        actual = self._category_actual(category_id)
        self.jurisdiction_total += actual
        
        actual_region = self._category_actual_region(category_id)
        
        potential = actual_region * self.region_share
        self.potential_total += potential
        
        variance = actual - potential
        
        rate = actual / potential if potential else 0
        
        if category_name.lower() in self.consumer_categories:
            self.jurisdiction_consumer_total += actual
            self.potential_consumer_total += potential
            
        else:
            if category_name.lower() == 'business to business':
                self.business_to_business_rate = rate
                
            else:
                self.miscellaneous_rate = rate
        
        # colors the empty column used as border
        self._write_category_border(row)
        
        column = 1
        
        # writes the category name
        self.table_ws.write(
            row, column, category_name.title(), self.category_format
            )
        column += 1
        
        # writes the category actual sales tax
        self.table_ws.write(
            row, column, actual, self.category_format
            )
        column += 1
        
        # writes the category potential amount
        self.table_ws.write(
            row, column, potential, self.category_format
            )
        column += 1
        
        # writes the category variance amount
        self.table_ws.write(
            row, column, variance, self.category_format
            )
        column += 1
        
        # writes the percent rate for the category
        self.table_ws.write(row, column, rate, percent_format)
                
                
    def _category_actual(self, category_id):
        return (
            self.category_totals[category_id] 
            if category_id in self.category_totals else 0
            )
        
        
    def _category_actual_region(self, category_id):
        return (
            self.category_totals_region[category_id]
            if category_id in self.category_totals_region else 0
            )
        
        
    def _write_category_border(self, row):
        self.table_ws.write(row, 0, '', self.category_format)
        
        
    def _write_segment_row(self, row, segment_id, segment_name, category_name):
        actual = self._segment_actual(segment_id)
        actual_region = self._segment_actual_region(segment_id)
        
        potential = actual_region * self.region_share
        
        variance = actual - potential
        
        rate = actual / potential if potential else 0
        
        amount_format = self.formats['segment_amount']
        
        self._write_category_border(row)
        
        column = 1
         
        # writes the segment name
        self.table_ws.write(
            row, column, segment_name.title(), 
            self.formats['segment_amount']
            )
        column += 1
        
        # writes the segment actual amount
        self.table_ws.write(row, column, actual, amount_format)
        column += 1
        
        # writes the segment potential amount
        self.table_ws.write(row, column, potential, amount_format)
        column += 1
        
        # writes the segment variance amount
        self.table_ws.write(row, column, variance, amount_format)
        column += 1
        
        # writes the segment rate percent
        self.table_ws.write(row, column, rate, self.formats['segment_percent'])
        
        if category_name.lower() in self.consumer_categories:
            self.chart_data[category_name][segment_name] = rate
        
        
    def _segment_actual(self, segment_id):
        return (
            self.segment_totals[segment_id] 
            if segment_id in self.segment_totals else 0
            )
        
        
    def _segment_actual_region(self, segment_id):
        return (
            self.segment_totals_region[segment_id]
            if segment_id in self.segment_totals_region else 0
            )
         

    def _write_business_code_row(self, row, business_code_id, business_code_name):
        actual = self._business_code_actual(business_code_id)
        actual_region = self._business_code_actual_region(business_code_id)
        
        potential = actual_region * self.region_share
        
        variance = actual - potential
        
        rate = actual / potential if potential else 0
        
        amount_format = self.formats['business_code_amount']
        
        self._write_category_border(row)
        
        column = 1
        
        # writes the business code name
        self.table_ws.write(
            row, column, business_code_name.title().replace("'S", "'s"), 
            self.formats['business_code_name']
            )
        column += 1
        
        # writes the business code actual amount
        self.table_ws.write(row, column, actual, amount_format)
        column += 1
        
        # write the potential amount
        self.table_ws.write(row, column, potential, amount_format)
        column += 1
        
        # write the variance
        self.table_ws.write(row, column, variance, amount_format)
        column += 1
        
        # write the rate
        self.table_ws.write(row, column, rate, self.formats['business_code_percent'])
        
        
    def _business_code_actual(self, business_code_id):   
        return (
            self.business_code_totals[business_code_id]
            if business_code_id in self.business_code_totals else 0
            )  
        
        
    def _business_code_actual_region(self, business_code_id):  
        return (
            self.business_code_totals_region[business_code_id]
            if business_code_id in self.business_code_totals_region else 0
            ) 
        
        
    def _write_consumer_total_row(self, row):
        variance = self.jurisdiction_consumer_total - self.potential_consumer_total
        
        rate = (
            self.jurisdiction_consumer_total / self.potential_consumer_total 
            if self.potential_consumer_total else 0
            )
        
        column = 0
        
        amount_format = self.formats['total_amount']
        
        # writes the empty border
        self.table_ws.write(row, column, '', self.formats['total_border'])
        column += 1
        
        # writes the row name
        self.table_ws.write(
            row, column, 'consumer-driven total'.upper(), amount_format
            )
        column += 1
        
        # writes the consumer driven total
        self.table_ws.write(
            row, column, self.jurisdiction_consumer_total, amount_format
            )
        column += 1
        
        # writes the potential consumer driven total
        self.table_ws.write(
            row, column, self.potential_consumer_total, amount_format
            )
        column += 1
        
        # writes the variance
        self.table_ws.write(row, column, variance, amount_format)
        column += 1
        
        # writes the rate
        self.table_ws.write(row, column, rate, self.formats['total_percent'])
        
        self.consumer_total_rate = rate
        

    def _write_total_row(self):
        variance = self.jurisdiction_total - self.potential_total
        
        rate = (
            self.jurisdiction_total / self.potential_total 
            if self.potential_total else 0
            )
        
        column = 0
        
        amount_format = self.formats['total_amount']
        
        # writes the empty border
        self.table_ws.write(
            self.last_row, column, '', self.formats['total_border']
            )  
        column += 1
        
        # writes the row name
        self.table_ws.write(
            self.last_row, column, 'grand total'.upper(), amount_format
            )
        column += 1
        
        # writes the jurisdiction total
        self.table_ws.write(
            self.last_row, column, self.jurisdiction_total, amount_format
            ) 
        column += 1
        
        # writes the potential total
        self.table_ws.write(
            self.last_row, column, self.potential_total, amount_format
            )
        column += 1
        
        # writes the variance 
        self.table_ws.write(
            self.last_row, column, variance, amount_format
            )
        column += 1
        
        # writes the rate
        self.table_ws.write(
            self.last_row, column, rate, self.formats['total_percent']
            )
        
        
    def _write_table_sheet_footer(self):
        footer = (
            f'&L{constants.LEFT_CONFIDENTIAL_FOOTER}'
            f'&RSources: {constants.RIGHT_FOOTER} and Claritas'
            )
        
        self.table_ws.set_footer(footer)
            
        
    def _set_top_rows(self):
        '''
            Sets the row heights in the worksheet.
        '''
        row_heights = self.sheet_properties['row_heights'].items()
        
        for row_index, row_height in row_heights:
            self.table_ws.set_row(row_index, row_height)
            
            
    def _set_table_rows(self):
        first_row = self._sheet_row('table')
        
        height = self.sheet_properties['table_row_height']
        
        for i in range(first_row, self.last_row):
            self.table_ws.set_row(i, height) 
            
            
    def _set_columns(self):
        '''
            Sets the column widths in the worksheet.
        '''
        column_widths = self.sheet_properties['column_widths'].items()
        
        for column_index, column_width in column_widths:
            self.table_ws.set_column(column_index, column_index, column_width)
            
            
    def _set_table_page(self):
        self.table_ws.set_margins(left=0.75, right=0.75, top=0.5, bottom=0.5)
        
        last_column = self._sheet_column('last')
        
        self.table_ws.print_area(0, 0, self.last_row, last_column)
        
        # 1 page wide and as 2 pages long 
        self.table_ws.fit_to_pages(width=1, height=2)
        
        
    def _write_chart_sheet(self):
        sheet_name = self.chart_sheet_properties['name']
        
        self.chart_ws = self.wb.add_worksheet(sheet_name)
        
        first_row = self.chart_sheet_properties['data_row']
        end_row = first_row
        
        label_column = self.chart_sheet_properties['label_column']
        value_column = self.chart_sheet_properties['value_column']
        
        # initializes the lists of chart data with the data for consumer total
        all_labels = ['Consumer Total']
        all_values = [self.consumer_total_rate]
        point_colors = [{'fill': {'color': 'black'}}]
        
        for category_name, data in self.chart_data.items():
            # the color that will be used for the series
            color = constants.THEME_COLORS[
                category_name.lower().replace(' ', '_')
                ]
            
            labels = data.keys()
            values = data.values()
                
            labels = [label.title() for label in labels]
            all_labels.extend(labels)
            
            all_values.extend(values)
            
            value_count = len(values)
            
            for _ in range(value_count):
                point_colors.append({'fill': {'color': color}})
            
            end_row += value_count
            
        # inserts the chart data for business to business category
        all_labels.append('Business to Business')
        all_values.append(self.business_to_business_rate)
        point_colors.append({'fill': {'color': constants.B2B_COLOR}})
        
        # inserts the chart data for the miscellaneous category
        all_labels.append('Miscellaneous')
        all_values.append(self.miscellaneous_rate)
        point_colors.append({'fill': {'color': constants.MISC_COLOR}})
        
        # increments the row to include the categories
        end_row += 2
        
        self.chart_ws.write_column(first_row, label_column, all_labels)
        self.chart_ws.write_column(first_row, value_column, all_values)
        
        self.chart_ws.write_column(
            first_row, value_column+1, [1 for _ in range(len(all_values))]
            )
        
        # creates the chart
        chart = self.wb.add_chart({'type': 'column'})
        #chart.set_style(4)
        chart.set_title({'name': self.report_title})
        
        chart.add_series({
            'categories': [
                sheet_name, first_row, label_column, end_row, label_column
                ],
            
            'data_labels': {
                'value': True,  'num_format': '0%', 
                'font': {
                    'bold': True, 
                    'size': CHART_FONT_SIZE
                    },
                
                },
            
            'values': [
                sheet_name, first_row, value_column, end_row, value_column
                ],
            
            'points': point_colors, 
            
            'gap': self.chart_properties['gap']
            })
        
        chart.set_x_axis({
            'num_font': {'bold': True}
            })
        
        chart.set_y_axis({
            'visible': False, 
            
            'major_gridlines': {
                'visible': False
                }
            })
        
        chart.set_legend({'none': True})
        
        chart.set_plotarea({
            'fill': {'none': True}
            })
        
        chart.set_chartarea({
            'border': {'none': True},
            'fill': {'none': True}
            })
        
        chart.set_size({
            'width': self.chart_properties['width'], 
            'height': self.chart_properties['height']
            })
        
        
        line_chart = self.wb.add_chart({'type': 'line'})
        
        line_chart.add_series({
            'values': [
                sheet_name, first_row, value_column+1, end_row, value_column+1
                ],
            
            'categories': [
                sheet_name, first_row, label_column, end_row, label_column
                ],
            
            'line': {
                'color': constants.BLUE_THEME_COLOR,
                'dash_type': 'round_dot'
                }
            })
        
        chart.combine(line_chart)
             
        self.chart_ws.insert_chart(
            self.chart_sheet_properties['first_row'], 
            self.chart_sheet_properties['first_column'], chart
            )
        
        self._write_chart_legend()
        
        self._write_chart_message()
        
        self._write_chart_sheet_footer()
        
        self._set_chart_page()
        
        
    def _write_chart_legend(self):
        row = self.chart_sheet_properties['legend_row']
        color_column = self.chart_sheet_properties['first_column']
        name_column = color_column + 1
        
        self.chart_ws.merge_range(
            row, name_column, row, name_column + 1, 'Economic Category', 
            self.formats['legend_header']
            )
        row += 1
        
        # writes the color and the name for the consumer total
        self.chart_ws.write(row, color_column, '', self.formats['total_border'])
        self.chart_ws.write(row, name_column, 'Consumer Total')
        row += 1
        
        chart_categories = self.chart_data.keys()
        
        for category in chart_categories:
            format_name = f'{category.lower().replace(" ", "_")}_amount'
            
            # writes the legend color
            self.chart_ws.write(
                row, color_column, '', self.formats[format_name]
                )
            
            # writes the category name
            self.chart_ws.write(row, name_column, category.title())
              
            row += 1
            
            
    def _write_chart_message(self):
        row = self.chart_sheet_properties['legend_row']
        column = self.chart_sheet_properties['message_column']
        
        self.chart_ws.merge_range(
            row, column, row, column + 1, "Chart's Message", 
            self.formats['legend_header']
            )
        row += 1
        
        last_column = self.chart_sheet_properties['last_column']
        
        self.chart_ws.merge_range(
            row, column, row + 2, last_column, self.chart_message, 
            self.formats['chart_message']
            )
        
        
    def _write_chart_sheet_footer(self):
        footer = f'&R{constants.RIGHT_FOOTER}'
        
        self.chart_ws.set_footer(footer)
        
        
    def _set_chart_page(self):
        self.chart_ws.set_landscape()
        
        self.chart_ws.set_margins(left=0.5, right=0.5, top=0.5, bottom=0.5)
        
        self.chart_ws.print_area(
            self.chart_sheet_properties['first_row'], 
            self.chart_sheet_properties['first_column'],
            self.chart_sheet_properties['last_row'],
            self.chart_sheet_properties['last_column']
            )
        
        self.chart_ws.fit_to_pages(width=1, height=1)
    
    
    
            
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
