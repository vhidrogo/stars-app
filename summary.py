'''
Created on Dec 19, 2018

@author: vahidrogo
'''

from operator import itemgetter
import pandas as pd
from tkinter import messagebox as msg
import xlsxwriter

import constants
from internaldata import InternalData
import utilities


class Summary:
    '''
    '''
    
    
    CASH_CHANGE_PERIOD_COUNT = 17
    TOP_GENERATOR_COUNT = 25
    TOP_SEGMENT_COUNT = 14
    
    output_type = 'xlsx'
    
    report_name = 'Sales Tax Summary'
    
    format_properties = {
        'bold_centered' : {'bold' : True, 'align' : 'center'},
        
        'center_wrapped' : {'align' : 'center'},
        
        'jurisdiction_quarter_change' : {
            'align' : 'center', 'bold' : True, 'num_format' : '0.0%',
            },
        
        'jurisdiction_quarter_change_border' : {
            'align' : 'center', 'bold' : True, 'num_format' : '0.0%', 
            'top' : True, 'top_color' : constants.BLUE_THEME_COLOR
            },
        
        'jurisdiction_total_change' : {
            'align' : 'center' , 'bg_color' : constants.GRAY_COLOR, 
            'bold' : True, 'num_format' : '0.0%'
            },
        
        'jurisdiction_year_change' : {
            'align' : 'center', 'bold' : True, 'num_format' : '0.0%', 
            'left' : True, 'left_color' : constants.BLUE_THEME_COLOR
            },
        
        'jurisdiction_change_header' : {
            'bg_color' : constants.GRAY_COLOR, 'bold' : True, 
            'num_format' : '0.0%'
            },
        
        'jurisdiction_name' : {
            'bg_color' : constants.BLUE_THEME_COLOR, 'bold' : True, 
            'font_color' : 'white', 'font_size' : 24, 'valign' : 'vcenter'
            }, 
        
        'news_header' : {
            'bg_color' : constants.GRAY_COLOR, 'bold' : True, 'font_size' : 14
            },
        
        'percent_change' : {'align' : 'center', 'num_format' : '0.0%'},
        
        'period' : {
            'bg_color' : constants.BLUE_THEME_COLOR, 'font_color' : 'white', 
            'font_size' : 12, 'valign' : 'vcenter'
            },
        
        'quarter_change_header' : {
            'align' : 'center', 'right' : True, 
            'right_color' : constants.BLUE_THEME_COLOR
            },
        
        'region_change' : {'align' : 'center', 'num_format' : '0.0%'},
        
        'region_change_first' : {
            'align' : 'center', 'num_format' : '0.0%', 'top' : True, 
            'top_color' : constants.BLUE_THEME_COLOR
            },
        
        'region_total_change' : {
            'align' : 'center', 'bg_color' : constants.GRAY_COLOR,
            'num_format' : '0.0%'
            },
        
        'report_name' : {
            'bg_color' : constants.BLUE_THEME_COLOR, 'bold' : True, 
            'font_color' : 'white', 'font_size' : 14
            }, 
        
        'section_header' : {
            'bg_color' : constants.BLUE_THEME_COLOR, 'bold' : True,
            'font_color' : 'white', 'font_size' : 14, 'valign' : 'vcenter'
            },
        
        'segment_name' : {'indent' : 1},
        
        'segment_name_first' : {
            'indent' : 1, 'top' : True, 'top_color' : constants.BLUE_THEME_COLOR
            },
        
        'state_change' : {
            'align' : 'center', 'num_format' : '0.0%', 'right' : True, 
            'right_color' : constants.BLUE_THEME_COLOR
            },
        
        'state_change_first' : {
            'align' : 'center', 'num_format' : '0.0%', 'right' : True,
            'right_color' : constants.BLUE_THEME_COLOR, 'top' : True,
            'top_color' : constants.BLUE_THEME_COLOR
            },
        
        'statewide_name' : {
            'align' : 'center', 'right' : True, 
            'right_color' : constants.BLUE_THEME_COLOR
            },
        
        'statewide_total_change' : {
            'align' : 'center', 'bg_color' : constants.GRAY_COLOR,
            'num_format' : '0.0%', 'right' : True, 
            'right_color' : constants.BLUE_THEME_COLOR
            },
        
        'top_generators' : {'font_size' : 10},
        
        'total_name' : {'bg_color' : constants.GRAY_COLOR, 'bold' : True},
        
        'verbiage' : {'valign' : 'vcenter', 'font_size': 10}, 
        
        'year_change_header' : {'align' : 'center'}
        }
    
    wrap_text_formats = ['bold_centered', 'center_wrapped', 'verbiage']
    
    sheet_properties = {
        'column_widths' : {
            0 : 22, 1 : 12, 2 : 12, 3 : 12, 4 : 6, 5 : 6, 6 : 12, 7 : 12
            },
        
        'columns' : {
            'chart_data' : 9, 'last' : 7, 'first' : 0, 'jurisdiction_name_first' : 0, 
            'jurisdiction_name_last' : 5, 'news_first' : 0, 'news_last' : 7, 
            'period_first' : 6, 'period_last' : 7,
            'quarter_change_first' : 1, 'quarter_change_last' : 3,
            'report_name_first' : 6, 'report_name_last' : 7, 
            'top_generators_first' : 0, 'top_generators_last' : 5, 'top_generators_middle' : 2,
            'year_change_first' : 4, 'year_change_last' : 7
            },
        
        'name' : 'Summary',
        
        # row 27 has height 30 in the two page summary
        'row_heights' : {0 : 24, 1 : 24, 27 : 30},
        
        # chart one header row is 48 in the two page summary
        # for now changing to 25 where the business activity would be
        # lst row in two page summary is 95
        'rows' : {
            'business_activity_header' : 25, 'category_first' : 29, 'change_header' : 26, 'change_names' : 27,
            'chart_one' : 26, 'chart_one_header' : 25, 'chart_two_header' : 72,
            'jurisdiction_name_first' : 0, 'jurisdiction_name_last' : 1, 
            'last' : 50, 'news_header' : 3, 'news_first' : 4, 'period' : 1, 
            'segment_first' : 34,
            'top_generators' : 15, 'top_generators_header' : 14, 'total_change' : 28 
            }
        }
    
    cash_chart_properties = {
        'height' : 475,
        'width' : 700, 
        'line_width' : 4
        }
    
    output_name = 'Summary'

    
    def __init__(self, controller):
        self.controller = controller
        self.selections = self.controller.selections
        
        self.jurisdiction_table = ''
        self.output_path = ''
        
        self.jurisdiction_current_bmy_total = 0
        self.jurisdiction_current_total = 0
        self.jurisdiction_prior_bmy_total = 0
        self.jurisdiction_prior_total = 0
        self.region_current_bmy_total = 0
        self.region_current_total = 0
        self.region_prior_bmy_total = 0
        self.region_prior_total = 0
        self.state_current_bmy_total = 0
        self.state_current_total = 0
        self.state_prior_bmy_total = 0
        self.state_prior_total = 0
        
        self.output_saved = False
        
        self.jurisdiction = None
        
        self.top_segment_ids = ()
        
        self.cash_change_data = []
        self.top_generators = []
        
        self.formats = {}
        self.jurisdiction_category_totals = {}
        self.region_category_totals = {}
        self.state_category_totals = {}
        self.top_segments = {}
        self.top_segments_region = {}
        self.top_segments_state = {}
        
        self._set_months()
        self._set_periods()
        
        self._set_bmy_sum_strings()
        '''
            TODO check if I still need the bmy sum string two
        '''
        self.periods_string = ','.join(self.periods)
        
        self._set_verbiage()
        
        self._set_category_names()
        self._set_segment_names()
        
        self.cash_change_periods = utilities.get_period_headers(
            self.CASH_CHANGE_PERIOD_COUNT, self.selections
            )
        
        
    def _set_months(self):
        '''
            Sets the months strings that will be used for the report header.
        '''
        quarter = self.selections.quarter
        year = self.selections.year
        
        if quarter == 1:
            month_one = 'April'
            month_two = 'March'
            
            year_one = year - 1
            year_two = year
        
        elif quarter == 2:
            month_one = 'July'
            month_two = 'June'
            
            year_one = year - 1
            year_two = year
        
        elif quarter == 3:
            month_one = 'Oct'
            month_two = 'Sep'
            
            year_one = year - 1
            year_two = year
        
        else:
            month_one = 'Jan'
            month_two = 'Dec'
            
            year_one = year_two = year
        
        self.month_one = f'{month_one} {year_one}'
        self.month_two = f'{month_two} {year_two}'
        
        
    def _set_periods(self):
        '''
            Sets the list of periods required for the report.
        '''
        self.periods = []
         
        year = self.selections.year
        quarter = self.selections.quarter
         
        # need eight quarter for two bmy self.periods
        for _ in range(8):
            period = f'{constants.QUARTER_COLUMN_PREFIX}{year}q{quarter}'
             
            self.periods.append(period)
             
            # reduces the period by one
            if quarter == 1:
                quarter = 4
                year -= 1
                 
            else:
                quarter -= 1
         
         
    def _set_bmy_sum_strings(self):
        # string to sum the first four periods to get most current bmy
        self.bmy_sum_string_one = '+'.join(
            self.periods[:constants.BMY_PERIOD_COUNT]
            )
          
        # string to sum the next four periods to get the next bmy
        self.bmy_sum_string_two = '+'.join(
            self.periods[constants.BMY_PERIOD_COUNT:]
            )
        
        
    def _set_verbiage(self):
        '''
            Fetches the verbiage items that will be used for the news section.
        '''
        self.verbiage = {}
        
        query = f'''
            SELECT position, verbiage
            FROM summary_verbiage
            WHERE period=?
            '''
        
        args = (self.selections.period, )
        
        results = utilities.execute_sql(
            sql_code=query, args=args, db_name=constants.STARS_DB, 
            fetchall=True
            )
        
        if results:
            for position, verbiage in sorted(results, key=itemgetter(0)):
                self.verbiage[position] = verbiage
                
                
    def _set_category_names(self):
        '''
            Stores the category_id and category name in a dictionary 
            where the category id is the key and the category name is 
            its associated value.
        '''
        self.categories = {}
         
        query = f'''
            SELECT {constants.ID_COLUMN_NAME}, name
            FROM {constants.CATEGORIES_TABLE}
            '''
         
        results = utilities.execute_sql(
            sql_code=query, db_name=constants.STARS_DB, fetchall=True
            )
         
        if results:
            for category_id, category_name in results:
                self.categories[category_id] = category_name
                 
                 
    def _set_segment_names(self):
        '''
            Stores the segment id and segment name in a dictionary where 
            the segment id is the key and the segment name is its 
            associated value.
        '''
        self.segment_names = {}
         
        query = f'''
            SELECT {constants.ID_COLUMN_NAME}, name
            FROM {constants.SEGMENTS_TABLE}
            '''
         
        results = utilities.execute_sql(
            sql_code=query, db_name=constants.STARS_DB, fetchall=True
            )
         
        if results:
            for segment_id, segment_name in results:
                self.segment_names[segment_id] = segment_name
    
    
    def main(self, jurisdiction):
        self.jurisdiction = jurisdiction
        
        self.jurisdiction_table = utilities.get_jurisdiction_table_name(
            self.jurisdiction.id
            )
        
        self._set_top_generators()
        self._set_jurisdiction_category_totals()
        self._set_region_category_totals()
        self._set_state_category_totals()
        self._set_top_segments()
        self._set_top_segment_ids()
        self._set_top_segments_region()
        self._set_top_segments_state()
        
        self._set_output_path()
        
        self._write_output()
                 
        self._save_output()
                 
        if self.output_saved and self.selections.open_output:
            utilities.open_file(self.output_path)
             
            
    def _set_top_generators(self):
        '''
            Fetches the top 25 generators for the jurisdiction grouped by 
            business name and ranked by the most recent bmy period.  
        '''
        order_by = '+'.join(
            [f'sum({i})' for i in self.periods[:constants.BMY_PERIOD_COUNT]]
            )
        
        # pulls the top 25 businesses ordered by the most recent bmy amount
        internal_data = InternalData(
            is_cash=False, juri_abbrev=self.jurisdiction.id, 
            columns='business', group_by='business', order_by=order_by, 
            descending=True, limit=self.TOP_GENERATOR_COUNT
            )
        
        results = internal_data.get_data()
        
        if results:
            data = results['data']
            
            for i in data:
                self.top_generators.append(i[0])
                
            self.top_generators.sort()
                
    # for annualized cash change chart, will need to find somewhere to pull this from        
    #===========================================================================
    # def _set_cash_change_data(self):
    #     columns = [
    #         f'{constants.QUARTER_COLUMN_PREFIX}{i.replace("Q", "")}'
    #         for i in self.cash_change_periods
    #         ]
    #     
    #     columns.insert(0, constants.ID_COLUMN_NAME)
    #     
    #     jurisdictions = tuple([
    #         self.jurisdiction.tac, f'{self.jurisdiction.tac[:2]}TOT', 'STATE'
    #         ])
    #     
    #     query = f'''
    #         SELECT {','.join(columns)}
    #         FROM bmy_cash_changes
    #         WHERE {constants.ID_COLUMN_NAME} IN {jurisdictions}
    #         '''
    #     
    #     results = utilities.execute_sql(
    #         sql_code=query, db_name=constants.STATEWIDE_DATASETS_DB, 
    #         fetchall=True
    #         )
    #     
    #     if results:
    #         self.cash_change_data = results
    #===========================================================================
                
                
    def _set_jurisdiction_category_totals(self):
        '''
            Fetches the category totals for the jurisdiction.
        '''
        query = f'''
            SELECT {constants.CATEGORY_ID_COLUMN_NAME}, {self.periods_string}
            FROM {constants.CATEGORY_TOTALS_TABLE}
            WHERE {constants.TAC_COLUMN_NAME}=?
            '''
         
        args = (self.jurisdiction.tac, )
         
        results = utilities.execute_sql(
            sql_code=query, args=args, db_name=constants.STATEWIDE_DATASETS_DB,
            fetchall=True
            )
         
        if results:
            for result in results:
                category_id = result[0]
                amounts = result[1:]
                 
                self.jurisdiction_category_totals[category_id] = amounts
    
    
    def _set_region_category_totals(self):
        '''
            Fetches the category totals for the region.
        '''
        query = f'''
            SELECT {constants.CATEGORY_ID_COLUMN_NAME}, {self.periods_string}
            FROM {constants.CATEGORY_TOTALS_TABLE}{constants.REGION_SUFFIX}
            WHERE {constants.REGION_ID_COLUMN_NAME}=?
            '''
         
        args = (self.jurisdiction.region_id, )
         
        results = utilities.execute_sql(
            sql_code=query, args=args, db_name=constants.STATEWIDE_DATASETS_DB,
            fetchall=True
            )
         
        if results:
            for result in results:
                category_id = result[0]
                amounts = result[1:]
                 
                self.region_category_totals[category_id] = amounts
    
    
    def _set_state_category_totals(self):
        '''
            Fetches the category totals for the state.
        '''
        query = f'''    
            SELECT {constants.CATEGORY_ID_COLUMN_NAME}, {self.periods_string}
            FROM {constants.CATEGORY_TOTALS_TABLE}{constants.REGION_SUFFIX}
            '''
         
        results = utilities.execute_sql(
            sql_code=query, db_name=constants.STATEWIDE_DATASETS_DB, 
            fetchall=True
            )
         
        if results:
            df = pd.DataFrame(results)
             
            columns = list(df)
             
            # sums all the quarters by category id 
            df = df.groupby(
                columns[0], as_index=False, sort=False
                )[columns[1:]].sum()
             
            for row in df.itertuples(index=False):
                category_id = row[0]
                amounts = row[1:]
                 
                self.state_category_totals[category_id] = amounts
            
                
    def _set_top_segments(self):
        '''
            Fetches the required number of top segments for the 
            jurisdiction ordered by the most recent bmy period.
        '''
        query = f'''
            SELECT {constants.SEGMENT_ID_COLUMN_NAME}, {self.periods_string}
             
            FROM {constants.SEGMENT_TOTALS_TABLE}
             
            WHERE {constants.TAC_COLUMN_NAME}=? 
        
            ORDER BY {self.bmy_sum_string_one} DESC
             
            LIMIT {self.TOP_SEGMENT_COUNT}
            '''
         
        args = (self.jurisdiction.tac, )
         
        results = utilities.execute_sql(
            sql_code=query, args=args, db_name=constants.STATEWIDE_DATASETS_DB,
            fetchall=True
            )
         
        if results:
            for result in results:
                segment_id = result[0]
                amounts = result[1:]
                 
                self.top_segments[segment_id] = amounts
                
                
    def _set_top_segment_ids(self):
        '''
            Sets a tuple with the top segment ids that will be used to 
            pull the top segments for the region and state.
        '''
        self.top_segment_ids = tuple(self.top_segments.keys())
                
                
    def _set_top_segments_region(self):
        '''
            Fetches the top segments for the region using the top segment ids
            from the top segments for the jurisdiction.
        '''
        query = f'''
            SELECT {constants.SEGMENT_ID_COLUMN_NAME}, {self.periods_string}
             
            FROM {constants.SEGMENT_TOTALS_TABLE}{constants.REGION_SUFFIX}
             
            WHERE {constants.REGION_ID_COLUMN_NAME}=?
                AND {constants.SEGMENT_ID_COLUMN_NAME} IN {self.top_segment_ids}
            '''
         
        args = (self.jurisdiction.region_id, )
         
        results = utilities.execute_sql(
            sql_code=query, args=args, db_name=constants.STATEWIDE_DATASETS_DB, 
            fetchall=True
            )
         
        if results:
            for result in results:
                segment_id = result[0]
                amounts = result[1:]
                 
                self.top_segments_region[segment_id] = amounts
                
                
    def _set_top_segments_state(self):
        '''
            Fetches the top segments for the sate using the top
            segment ids for the jurisdiction.
        '''
        columns = ','.join([f'sum({i})' for i in self.periods])
         
        query = f'''
            SELECT {constants.SEGMENT_ID_COLUMN_NAME}, {columns}
             
            FROM {constants.SEGMENT_TOTALS_TABLE}
             
            WHERE {constants.SEGMENT_ID_COLUMN_NAME} IN {self.top_segment_ids}
             
            GROUP BY {constants.SEGMENT_ID_COLUMN_NAME}
            '''
         
        results = utilities.execute_sql(
            sql_code=query, db_name=constants.STATEWIDE_DATASETS_DB, 
            fetchall=True
            )
         
        if results:
            for result in results:
                segment_id = result[0]
                amounts = result[1:]
                 
                self.top_segments_state[segment_id] = amounts
                    

    def _set_output_path(self):
        name = (
            f'{self.jurisdiction.id} {self.selections.period} {self.output_name}'
            )
        
        self.output_path = f'{self.jurisdiction.folder}{name}.{self.output_type}'
    
    
    def _write_output(self):
        '''
            Writes the data to an Excel workbook with formatting.
        '''
        self.wb = xlsxwriter.Workbook(self.output_path)
        self.ws = self.wb.add_worksheet(self.sheet_properties['name'])
        
        # hides the printed grid lines
        self.ws.hide_gridlines()
        
        self._set_formats()
        
        self._write_jurisdiction_name()
        self._write_report_name()
        self._write_period_timeframe()
        self._write_news_header()
        self._write_news()
        self._write_top_generators_header()
        self._write_top_generators()
        
        self._write_business_activity_header()
        self._write_quarter_change_header()
        self._write_year_change_header()
        self._write_quarter_change_names()
        self._write_year_change_names()
        self._write_category_changes()
        self._write_total_change_row()
        self._write_jurisdiction_segments()
        self._write_region_segments()
        self._write_state_segments()
        
        # will implement back in when i work on the two page summary
        #self._write_chart_two_header()
        
        self._set_rows()
        self._set_columns()
        
        self._set_footer()
        self._set_page()
        
        
    def _set_formats(self):
        '''
            Creates format objects for each of the format properties.
        '''
        for name, properties in self.format_properties.items():
            self.formats[name] = self.wb.add_format(properties)
            
        for format_name in self.wrap_text_formats:
            self.formats[format_name].set_text_wrap()
            
            
    def _sheet_row(self, name):
        '''
            Returns the row number given then name of the property
        '''
        return self.sheet_properties['rows'][name]
    
    
    def _sheet_column(self, name):
        '''
            Returns the column number given the name of the property.
        '''
        return self.sheet_properties['columns'][name]
    
    
    def _write_jurisdiction_name(self):
        '''
            Writes the jurisdiction name on the report header.
        '''
        first_row = self._sheet_row('jurisdiction_name_first')
        last_row = self._sheet_row('jurisdiction_name_last')
        first_column = self._sheet_column('jurisdiction_name_first')
        last_column = self._sheet_column('jurisdiction_name_last')
        
        name = utilities.fetch_jurisdiction_header(self.jurisdiction.name)
        
        self.ws.merge_range(
            first_row, first_column, last_row, last_column, 
            name, self.formats['jurisdiction_name'] 
            )


    def _write_report_name(self):
        '''
            Writes the report title on the report header.
        '''
        first_row = last_row = self._sheet_row('jurisdiction_name_first')
        first_column = self._sheet_column('report_name_first')
        last_column = self._sheet_column('report_name_last')
        
        self.ws.merge_range(
            first_row, first_column, last_row, last_column, 
            self.report_name, self.formats['report_name']
            )
        
        
    def _write_period_timeframe(self):
        '''
            Writes the timeframe of the data in the report on the report header.
        '''
        first_row = last_row = self._sheet_row('period')
        first_column = self._sheet_column('period_first')
        last_column = self._sheet_column('period_last')
        
        self.ws.merge_range(
            first_row, first_column, last_row, last_column, 
            f'{self.month_one} to {self.month_two}', self.formats['period']
            )
        
        
    def _write_news_header(self):
        '''
            Writes the formatted header for the new section.
        '''
        first_row = last_row = self._sheet_row('news_header')
        first_column = self._sheet_column('news_first')
        last_column = self._sheet_column('news_last')
        
        self.ws.merge_range(
            first_row, first_column, last_row, last_column, 'NEWS', 
            self.formats['news_header']
            )
        
        
    def _write_news(self):
        '''
            Writes the verbiage in the news section.
        '''
        row = self._sheet_row('news_first')
        first_column = self._sheet_column('news_first')
        last_column = self._sheet_column('news_last')
        
        for verbiage in self.verbiage.values():
            self.ws.merge_range(
                row, first_column, row + 2, last_column, verbiage, 
                self.formats['verbiage']
                )
            
            row += 3


    def _write_top_generators_header(self):
        '''
            Writes the formatted header for the top generators section.
        '''
        first_row = last_row = self._sheet_row('top_generators_header')
        first_column = self._sheet_column('first')
        last_column = self._sheet_column('last')
        
        self.ws.merge_range(
            first_row, first_column, last_row, last_column, 
            'Top 25 Sales Tax Generators', self.formats['section_header']
            )
        
        
    def _write_top_generators(self):
        '''
            Writes the top generators to the top generator section.
        '''
        row = self._sheet_row('top_generators')
        
        left_column = self._sheet_column('top_generators_first')
        middle_column = self._sheet_column('top_generators_middle')
        right_column = self._sheet_column('top_generators_last')
        
        left_businesses = self.top_generators[:9]
        middle_businesses = self.top_generators[9: 17]
        right_businesses = self.top_generators[17: ]
        
        # writes the first nine businesses
        self.ws.write_column(
            row, left_column, left_businesses, self.formats['top_generators'] 
            )
        
        # writes the next eight businesses
        self.ws.write_column(
            row, middle_column, middle_businesses, self.formats['top_generators']
            )
        
        self.ws.write_column(
            row, right_column, right_businesses, self.formats['top_generators']
            )
        
        
    def _write_business_activity_header(self):
        '''
            Writes the formatted header for the business activity section.
        '''
        first_row = last_row = self._sheet_row('business_activity_header')
        first_column = self._sheet_column('first')
        last_column = self._sheet_column('last')
         
        self.ws.merge_range(
            first_row, first_column, last_row, last_column, 
            'Business Activity', self.formats['section_header']
            )
        
        
    def _write_quarter_change_header(self):
        '''
            Writes the header for the quarter over quarter change section
            of the business activity.
        '''
        first_row = last_row = self._sheet_row('change_header')
        first_column = self._sheet_column('quarter_change_first')
        last_column = self._sheet_column('quarter_change_last')
         
        self.ws.merge_range(
            first_row, first_column, last_row, last_column, 
            'Quarter over Quarter', self.formats['quarter_change_header']
            )
        
        
    def _write_year_change_header(self):
        '''
            Writes the header for the year over year section in the 
            business activity section.
        '''
        first_row = last_row = self._sheet_row('change_header')
        first_column = self._sheet_column('year_change_first')
        last_column = self._sheet_column('year_change_last')
         
        self.ws.merge_range(
            first_row, first_column, last_row, last_column, 
            'Year over Year', self.formats['year_change_header']
            )
        
        
    def _write_quarter_change_names(self):
        '''
            Writes the names of the jurisdiction, region and statewide
            in the quarter over quarter change section in the business 
            activity section.
        '''
        row = self._sheet_row('change_names')
        column = self._sheet_column('quarter_change_first')
         
        # writes the jurisdiction name
        self.ws.write(
            row, column, self.jurisdiction.name.title(), 
            self.formats['bold_centered']
            )
        column += 1
         
        # writes the region name
        self.ws.write(
            row, column, self.jurisdiction.region_name.title(), 
            self.formats['center_wrapped']
            )
        column += 1
         
        self.ws.write(
            row, column, 'California', self.formats['statewide_name']
            )
    
    
    def _write_year_change_names(self):
        '''
            Writes the names of the jurisdiction, region and state 
            in the year over year section of the business activity section.
        '''
        row = self._sheet_row('change_names')
        column = self._sheet_column('year_change_first')
         
        # writes the jurisdiction name
        self.ws.merge_range(
            row, column, row, column + 1, self.jurisdiction.name.title(), 
            self.formats['bold_centered']
            )
        column += 2
         
        # writes the region name
        self.ws.write(
            row, column, self.jurisdiction.region_name.title(), 
            self.formats['center_wrapped']
            )
        column += 1
         
        # writes "statewide"
        self.ws.write(row, column, 'California', self.formats['center_wrapped'])
        
        
    def _write_category_changes(self):
        '''
            Writes the category percent changes in the business activity section
            for the jurisdiction, region and state.
        '''
        row = self._sheet_row('category_first')
         
        first_quarter_column = self._sheet_column('quarter_change_first')
        first_year_column = self._sheet_column('year_change_first')
         
        name_column = 0
         
        for category_id, category_name in self.categories.items():
            # quarterly amounts for the category
            if category_id in self.jurisdiction_category_totals:
                jurisdiction_quarterly = self.jurisdiction_category_totals[category_id]
                
                jurisdiction_current = jurisdiction_quarterly[0]
                
                jurisdiction_current_bmy = sum(
                    jurisdiction_quarterly[:constants.BMY_PERIOD_COUNT]
                )
                
                jurisdiction_prior = jurisdiction_quarterly[constants.BMY_PERIOD_COUNT]
            else:
                jurisdiction_quarterly = []   
                jurisdiction_current = 0
                jurisdiction_current_bmy = 0
                jurisdiction_prior = 0
                 
            region_quarterly = self.region_category_totals[category_id]
            state_quarterly = self.state_category_totals[category_id]
             
            # current quarter amounts
            region_current = region_quarterly[0]
            state_current = state_quarterly[0]
           
            region_current_bmy = sum(region_quarterly[:constants.BMY_PERIOD_COUNT])
            state_current_bmy = sum(state_quarterly[:constants.BMY_PERIOD_COUNT])
             
            # prior quarter amount
            region_prior = region_quarterly[constants.BMY_PERIOD_COUNT]
            state_prior = state_quarterly[constants.BMY_PERIOD_COUNT]
             
            jurisdiction_prior_bmy = sum(
                jurisdiction_quarterly[-constants.BMY_PERIOD_COUNT:]
                )
            
            region_prior_bmy = sum(region_quarterly[-constants.BMY_PERIOD_COUNT:])
            state_prior_bmy = sum(state_quarterly[-constants.BMY_PERIOD_COUNT:])
             
            # updates the current and prior totals
            self.jurisdiction_current_total += jurisdiction_current
            self.jurisdiction_current_bmy_total += jurisdiction_current_bmy
            self.jurisdiction_prior_total += jurisdiction_prior
            self.jurisdiction_prior_bmy_total += jurisdiction_prior_bmy
            self.region_current_total += region_current
            self.region_current_bmy_total += region_current_bmy
            self.region_prior_total += region_prior
            self.region_prior_bmy_total += region_prior_bmy
            self.state_current_total += state_current
            self.state_current_bmy_total += state_current_bmy
            self.state_prior_total += state_prior
            self.state_prior_bmy_total += state_prior_bmy
             
            jurisdiction_quarter_change = utilities.percent_change(
                jurisdiction_current, jurisdiction_prior
                )
            region_quarter_change = utilities.percent_change(
                region_current, region_prior
                )
            state_quarter_change = utilities.percent_change(
                state_current, state_prior
                )
             
            jurisdiction_year_change = utilities.percent_change(
                jurisdiction_current_bmy, jurisdiction_prior_bmy
                )
            region_year_change = utilities.percent_change(
                region_current_bmy, region_prior_bmy
                )
            state_year_change = utilities.percent_change(
                state_current_bmy, state_prior_bmy
                )
             
            # skips the miscellaneous category
            if not category_id == 6:
                # writes the category name
                self.ws.write(row, name_column, category_name)
                 
                # writes the jurisdiction quarter change
                self.ws.write(
                    row, first_quarter_column, jurisdiction_quarter_change, 
                    self.formats['jurisdiction_quarter_change']
                    )
                 
                # writes the region quarter change
                self.ws.write(
                    row, first_quarter_column + 1, region_quarter_change,
                    self.formats['percent_change']
                    )
                 
                # writes the state quarter change
                self.ws.write(
                    row, first_quarter_column + 2, state_quarter_change,
                    self.formats['percent_change']
                    )
                 
                # writes the jurisdiction year change
                self.ws.merge_range(
                    row, first_year_column, row, first_year_column + 1,
                    jurisdiction_year_change, 
                    self.formats['jurisdiction_year_change']
                    )
                 
                # writes the region year change
                self.ws.write(
                    row, first_year_column + 2, region_year_change,
                    self.formats['percent_change']
                    )
                 
                # writes the state year change
                self.ws.write(
                    row, first_year_column + 3, state_year_change,
                    self.formats['percent_change']
                    )
                 
                row += 1
                
                
    def _write_total_change_row(self):
        '''
            Writes the total percent change for the jurisdiction, region
            and state.
        '''
        quarter_jurisdiction = utilities.percent_change(
            self.jurisdiction_current_total, self.jurisdiction_prior_total
            )
         
        quarter_region = utilities.percent_change(
            self.region_current_total, self.region_prior_total
            )
         
        quarter_state = utilities.percent_change(
            self.state_current_total, self.state_prior_total
            )
         
        year_jurisdiction = utilities.percent_change(
            self.jurisdiction_current_bmy_total, self.jurisdiction_prior_bmy_total
            )
         
        year_region = utilities.percent_change(
            self.region_current_bmy_total, self.region_prior_bmy_total
            )
         
        year_state = utilities.percent_change(
            self.state_current_bmy_total, self.state_prior_bmy_total
            )
         
        row = self._sheet_row('total_change')
        column = self._sheet_column('first')
         
        jurisdiction_format = self.formats['jurisdiction_total_change']
        region_format = self.formats['region_total_change']
        state_format = self.formats['statewide_total_change']
         
        # writes the row name
        self.ws.write(row, column, 'TOTAL', self.formats['total_name'])
        column += 1
         
        # writes the quarter jurisdiction change
        self.ws.write(row, column, quarter_jurisdiction, jurisdiction_format)
        column += 1
         
        # writes the quarterly region change
        self.ws.write(row, column, quarter_region, region_format)
        column += 1
         
        # writes the quarterly state change
        self.ws.write(row, column, quarter_state, state_format)
        column += 1
         
        # writes the yearly jurisdiction change
        self.ws.merge_range(
            row, column, row, column + 1, year_jurisdiction, jurisdiction_format
            )
        column += 2
         
        # writes the yearly region change
        self.ws.write(row, column, year_region, region_format)
        column += 1
         
        # writes the yearly state change
        self.ws.write(row, column, year_state, region_format)
        
        
    def _write_jurisdiction_segments(self):
        '''
            Writes the percent changes for the top segments in the jurisdiction.
        '''
        row = self._sheet_row('segment_first')
        name_column = self._sheet_column('first')
        quarter_column = self._sheet_column('quarter_change_first')
        year_column = self._sheet_column('year_change_first')
         
        first = True
         
        for segment_id, segment_totals in self.top_segments.items():
            current = segment_totals[0]
            prior = segment_totals[constants.BMY_PERIOD_COUNT]
             
            current_bmy = sum(segment_totals[: constants.BMY_PERIOD_COUNT])
            prior_bmy = sum(segment_totals[constants.BMY_PERIOD_COUNT : ])
             
            quarter_change = utilities.percent_change(current, prior)
            year_change = utilities.percent_change(current_bmy, prior_bmy)
             
            if first:
                name_format = 'segment_name_first'
                amount_format = 'jurisdiction_quarter_change_border'
                 
                first = False
                 
            else: 
                name_format = 'segment_name'
                amount_format = 'jurisdiction_quarter_change'
             
            segment_name = self.segment_names[segment_id]
             
            # writes the segment name
            self.ws.write(
                row, name_column, segment_name.title(), 
                self.formats[name_format]
                )
             
            # writes the quarter over quarter change
            self.ws.write(
                row, quarter_column, quarter_change, 
                self.formats[amount_format]
                )
             
            # writes the year over year change
            self.ws.merge_range(
                row, year_column, row, year_column + 1, year_change,
                self.formats[amount_format]
                )
             
            row += 1
            
            
    def _write_region_segments(self):
        '''
            Writes the percent changes of the segments in the region
            for the top segments in the jurisdiction.
        '''
        row = self._sheet_row('segment_first')
      
        first = True
         
        for segment_id in self.top_segment_ids:
            totals = self.top_segments_region[segment_id]
             
            current = totals[0]
            prior = totals[constants.BMY_PERIOD_COUNT]
             
            current_bmy = sum(totals[: constants.BMY_PERIOD_COUNT])
            prior_bmy = sum(totals[- constants.BMY_PERIOD_COUNT :])
             
            quarter_change = utilities.percent_change(current, prior)
            year_change = utilities.percent_change(current_bmy, prior_bmy)
             
            if first:
                format_name = 'region_change_first'
                 
                first = False
             
            else:
                format_name = 'region_change'
             
            # writes the quarter over quarter change
            self.ws.write(
                row, self._sheet_column('quarter_change_first') + 1, 
                quarter_change, self.formats[format_name]
                )
             
            # writes the year over year change
            self.ws.write(
                row, self._sheet_column('year_change_first') + 2, year_change,
                self.formats[format_name]
                )
             
            row += 1
            
            
    def _write_state_segments(self):
        '''
            Writes the percent changes of the segments in the state for the 
            top segments in the jurisdiction.
        '''
        row = self._sheet_row('segment_first')
         
        first = True
         
        for segment_id in self.top_segment_ids:
            totals = self.top_segments_state[segment_id]
             
            current = totals[0]
            prior = totals[constants.BMY_PERIOD_COUNT]
             
            current_bmy = sum(totals[: constants.BMY_PERIOD_COUNT])
            prior_bmy = sum(totals[- constants.BMY_PERIOD_COUNT :])
             
            quarter_change = utilities.percent_change(current, prior)
            year_change = utilities.percent_change(current_bmy, prior_bmy)
             
            if first:
                quarter_format = 'state_change_first'
                year_format = 'region_change_first'
                 
                first = False
             
            else:
                quarter_format = 'state_change'
                year_format = 'region_change'
                 
            # writes the quarter over quarter change
            self.ws.write(
                row, self._sheet_column('quarter_change_first') + 2,
                quarter_change, self.formats[quarter_format] 
                )
             
            # writes the year over year change
            self.ws.write(
                row, self._sheet_column('year_change_first') + 3,
                year_change, self.formats[year_format]
                )
             
            row += 1
            
            
    #===========================================================================
    # def _write_chart_one_header(self):
    #     '''
    #         Writes the header for chart one.
    #     '''
    #     header = f'{self.jurisdiction.name}: annualized change in sales tax cash receipts'.title()
    #     
    #     first_row = last_row = self._sheet_row('chart_one_header')
    #     first_column = self._sheet_column('first')
    #     last_column = self._sheet_column('last')
    #     
    #     self.ws.merge_range(
    #         first_row, first_column, last_row, last_column, header,
    #         self.formats['section_header']
    #         )
    #===========================================================================    


#===============================================================================
#     def _write_chart_one(self):
#         chart_row = chart_data_first_row = self._sheet_row('chart_one')
#         chart_column = self._sheet_column('first')
#         
#         chart_data_first_column = self._sheet_column('chart_data')
#         chart_data_last_column = chart_data_first_column + len(self.cash_change_data[0]) - 1
#         
#         categories_row = chart_data_first_row - 1
#         categories_column = values_column = chart_data_first_column + 1
# 
#         chart_categories = [
#             f'City of {self.jurisdiction.name}', 
#             f'{self.jurisdiction.county_name} Countywide', 'California'
#             ]
#         
#         # writes the series names
#         self.ws.write_column(
#             chart_row, chart_data_first_column, chart_categories
#             )
#         
#         # writes the chart categories
#         self.ws.write_row(
#             categories_row, categories_column, self.cash_change_periods
#             )
#         
#         # writes the chart series
#         row = chart_data_first_row
#         for data in self.cash_change_data:
#             values = data[1:]
#             
#             self.ws.write_row(
#                 row, chart_data_first_column + 1, values
#                 )
#             
#             row += 1
#             
#         sheet_name = self.sheet_properties['name']
#         
#         # creates the chart
#         chart = self.wb.add_chart({'type' : 'line'})
#         
#         # adds each of he series to the chart
#         row = chart_data_first_row 
#         
#         for _ in range(len(chart_categories)):
#             chart.add_series({
#                 'values' : [
#                     sheet_name, row, values_column, row, 
#                     chart_data_last_column
#                     ],
#                 
#                 'categories' : [
#                     sheet_name, categories_row, categories_column, 
#                     categories_row, chart_data_last_column 
#                     ], 
#                 
#                 'name' : [sheet_name, row, chart_data_first_column],
#                 
#                 'line' : {'width' : self.cash_chart_properties['line_width']},
#                 
#                 'smooth' : True
#                 })
#             
#             row += 1
#             
#         chart.set_x_axis({'label_position' : 'low'})
#             
#         chart.set_y_axis({'num_format' : '0%'})
#             
#         chart.set_legend({'position' : 'bottom'})
#         
#         chart.set_plotarea({
#             'border' : {'none' : True},
#             'fill' : {'none' : True}
#             })
#         
#         chart.set_chartarea({
#             'border' : {'none' : True},
#             'fill' : {'none' : True}
#             })
#             
#         chart.set_size({
#             'height' : self.cash_chart_properties['height'],
#             'width' : self.cash_chart_properties['width']
#             })
#         
#         # inserts the chart
#         self.ws.insert_chart(chart_row, chart_column, chart)
#===============================================================================
        
        
    #===========================================================================
    # def _write_chart_two_header(self):
    #     '''
    #         Writes the header for chart two.
    #     '''
    #     header = 'estimated annualized employment and gross sales tax per capita by benchmark year'.title()
    #     
    #     first_row = last_row = self._sheet_row('chart_two_header')
    #     first_column = self._sheet_column('first')
    #     last_column = self._sheet_column('last')
    #     
    #     self.ws.merge_range(
    #         first_row, first_column, last_row, last_column, header,
    #         self.formats['section_header']
    #         )
    #===========================================================================
            

    def _set_rows(self):
        '''
            Sets the row heights for the rows that have row heights specified.
        '''
        row_heights = self.sheet_properties['row_heights']
        
        for index, height in row_heights.items():
            self.ws.set_row(index, height)
            
            
    def _set_columns(self):
        '''
            Sets column widths for the columns that have the column 
            width specified.
        '''
        column_widths = self.sheet_properties['column_widths']
        
        for index, width in column_widths.items():
            self.ws.set_column(index, index, width)
            
            
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
        '''
            Sets the print area, margins and fits the workbook to one page 
            wide and two pages long.
        '''
        first_row = first_column = 0
        last_row = self._sheet_row('last')
        last_column = self._sheet_column('last')
        
        self.ws.print_area(first_row, first_column, last_row, last_column)
        
        self.ws.set_margins(left=0.5, right=0.5, top=0.5, bottom=0.5)
        
        # for now set to one page long
        # fit the pages to one page wide and two pages long
        self.ws.fit_to_pages(width=1, height=1)
        
        
    def _save_output(self):
        '''
            Tries to save the workbook. This will fail if there is another 
            workbook open with the path of the one being created. If that is 
            the case then the user will see a message telling them that. 
        '''
        try:
            self.wb.close()
            
            self.output_saved = True
            
        except:
            msg.showinfo(
                self.selections.title, 
                f'Could not save to:\n\n{self.output_path}\n\nThere is '
                'a file with that name currently open.'
                )
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
