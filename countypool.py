'''
Created on Oct 16, 2018

@author: vahidrogo
'''

from tkinter import messagebox as msg
import xlsxwriter

import constants
from internaldata import InternalData
import utilities


class CountyPool:
    '''
    '''
    
    
    QUARTER_COUNT = 12
    RANK_QUARTERS = 4
    
    TOP_PERMIT_COUNT = 25
    
    business_column = 'BUSINESS'
    permit_column = 'PERMIT'
    
    bmy_column = 'bmy_total'
    
    other_row_name = 'ALL OTHER'
    
    output_type = 'xlsx'
    
    gray_color = '#dbdbdb'
    
    total_descriptions = {
        'county_pool_amounts' : 'Total County Pool', 
        'juri_pool_amounts' : 'jurisdiction Share', 
        'percent_share' : 'jurisdiction % of Total'}
    
    sheet_properties = {
        'name' : 'County Pool', 'quarter_row_height' : 46.5,
        
        'business_row_height' : 19,
        
        'columns' : {
            'current_quarter' : 12, 'first_quarter' : 1, 'last_column' : 13,
            'prior_year' : 8},
        
        'rows' : {
            other_row_name : 36, 'business_description' : 9, 
            'juri_pool_amounts' : 6, 'first_business' : 11, 
            'percent_share' : 7, 
            
            'quarter_headers' : {'one' : 4, 'two' : 10},
            
            'county_pool_amounts' : 5, 'report_description' : 2, 'report_header' : 0, 
            'report_title' : 1}}
    
    format_properties = {
        'amount' : {'num_format' : '#,##0'},
        
        'amount_color' : {'num_format' : '#,##0', 'bg_color' : gray_color},
        
        'amount_color_bold' : {
            'num_format' : '#,##0', 'bg_color' : gray_color, 'bold' : True},
        
        'business' : {'align' : 'left'},
        
        'business_color' : {'align' : 'left', 'bg_color' : gray_color},
        
        'business_description' : {'bold' : True, 'font_size' : 12},
        
        'current_amount' : {
            'num_format' : '#,##0', 'left' : True, 'right' : True},
        
        'current_amount_color' : {
            'num_format' : '#,##0', 'bg_color' : gray_color, 'left' : True, 
            'right' : True},
        
        'current_amount_color_bold' : {
            'num_format' : '#,##0', 'bg_color' : gray_color, 'left' : True, 
            'right' : True, 'bold' : True},
        
        'current_percent_share' : {
            'num_format' : '0.0%', 'left' : True, 'bottom' : True, 
            'right' : True, 'bg_color' : gray_color},
        
        'current_quarter' : {
            'left' : True, 'top' : True, 'right' : True, 'bottom' : True,
            'align' : 'center', 'valign' : 'vcenter', 'bg_color' : gray_color},
        
        'description' : {'align' : 'center', 'font_size' : 12},
        
        'header' : {
            'align' : 'center', 'font_size' : 20, 'font_color' : 'white', 
            'bg_color' : constants.BLUE_THEME_COLOR},
        
        'percent_header' : {
            'left' : True, 'top' : True, 'right' : True, 'bottom' : True, 
            'align' : 'center', 'valign' : 'vcenter'},
        
        'percent_share' : {'num_format' : '0.0%'},
        
        'quarter' : {
            'left' : True, 'top' : True, 'right' : True, 'bottom' : True, 
            'align' : 'center', 'valign' : 'vcenter'},
        
        'quarter_change' : {'num_format' : '0.0%'},
        
        'quarter_change_color' : {'num_format' : '0.0%', 'bg_color' : gray_color},
        
        'title' : {'align' : 'center', 'bold' : True, 'font_size' : 14},
        
        'total_description' : {'align' : 'right'},
        
        'total_description_color' : {
            'align' : 'right', 'bold' : True, 'bg_color' : gray_color
            },
        }
    
    report_title = 'County Pool Recap'
    report_description = 'Cash Basis by Quarter'
    business_description = f'Top {TOP_PERMIT_COUNT} County Pool Receipts'
    
    output_name = 'County Pool Analysis'
    
    
    def __init__(self, controller):
        self.controller = controller
        self.selections = self.controller.selections
        
        self.output_saved = False

        self.quarter_changes = {}
        
        self.blank_business_names = []
        self.juri_pool_amounts = []
        self.county_pool_amounts = []
        self.top_businesses = []
        self.top_business_amounts = []
        
        self.period_headers = utilities.get_period_headers(
            self.QUARTER_COUNT, self.selections
            )
        

    def main(self, jurisdiction):
        self.jurisdiction = jurisdiction
        
        self.controller.update_progress(
            0, f'{self.jurisdiction.id}: Fetching county pool amounts.'
            )
         
        self._set_jurisdiction_pool_amounts()
        
        if self.juri_pool_amounts:
            # don't need to check if the county has amounts because if 
            # the jurisdiction has amounts then the county will at least 
            # have those amounts
            self._set_county_pool_amounts()
            self._set_percent_juri_shares()
            
            self.controller.update_progress(
                0, f'{self.jurisdiction.id}: Fetching top {self.TOP_PERMIT_COUNT} permits.'
                )
            
            self._process_top_businesses()
            
            if self.top_businesses:
                self.controller.update_progress(
                    0, f'{self.jurisdiction.id}: Creating output.'
                    )
                
                self._insert_quarter_change(
                    self.county_pool_amounts, 'county_pool_amounts'
                    )
                 
                self._insert_quarter_change(
                    self.juri_pool_amounts, 'juri_pool_amounts'
                    )
                
                self._set_all_other_row()                  
                self._set_output_path() 
                self._create_excel_output()
                
                if self.blank_business_names:
                    self._create_blank_businesses_file()
                     
                self.controller.update_progress(
                    100, f'{self.jurisdiction.id}: Finished'
                    )
                 
                if self.output_saved and self.selections.open_output:
                    utilities.open_file(self.output_path)
                
        else:
            msg.showinfo(
                self.selections.title, 
                f'No data returned for ({self.jurisdiction.tac}) from table:\n'
                f'{constants.STATEWIDE_DATASETS_DB}.{constants.CDTFA_ALLOCATION_TABLE}.'
                )
            
        
    def _set_jurisdiction_pool_amounts(self):
        query = f'''
            SELECT county_pool_amount
            
            FROM {constants.CDTFA_ALLOCATION_TABLE}
            
            WHERE {constants.TAC_COLUMN_NAME} = ?
                AND period IN {tuple(self.period_headers)}
                
            ORDER BY period
            '''
        
        amounts = utilities.execute_sql(
            sql_code=query, 
            args=(self.jurisdiction.tac, ),
            db_name=constants.STATEWIDE_DATASETS_DB,
            fetchall=True
            )
        
        if amounts:
            self.juri_pool_amounts = [int(x[0]) for x in amounts]
            
            
    def _set_county_pool_amounts(self):
        query = f'''
            SELECT SUM(county_pool_amount)
            
            FROM {constants.CDTFA_ALLOCATION_TABLE} c,
                {constants.JURISDICTIONS_TABLE} j
            
            WHERE c.{constants.TAC_COLUMN_NAME} = j.{constants.TAC_COLUMN_NAME}
                AND j.{constants.COUNTY_ID_COLUMN_NAME} = ?
                AND period IN {tuple(self.period_headers)}
                
            GROUP BY period
                
            ORDER BY period
            '''
        
        amounts = utilities.execute_sql(
            sql_code=query, 
            args=(self.jurisdiction.county_id, ),
            db_name=constants.STATEWIDE_DATASETS_DB,
            attach_db=constants.STARS_DB,
            fetchall=True
            )
        
        if amounts:
            self.county_pool_amounts = [int(x[0]) for x in amounts]
            
            
    def _set_percent_juri_shares(self):
        self.jurisdiction_percent_shares = []
        
        for i, amount in enumerate(self.county_pool_amounts):
            percent_share = self.juri_pool_amounts[i] / amount if amount else 0
            
            self.jurisdiction_percent_shares.append(percent_share)
            
            
    def _process_top_businesses(self):
        # Concatenates a string with each of the period headers including 
        # the prefix that is used in the SQL table separated by commas.
        # This will be part of a SQL code snippet that twill be used to pull
        # the totals from the county pool data.
        period_columns_string = ','.join(
            f'{constants.QUARTER_COLUMN_PREFIX}{quarter}' 
            for quarter in self.period_headers
            )

        # Concatenates a string with each of the most recent four periods 
        # including the prefix that is used in the SQL table separated by 
        # "+" as the first part of a SQL snippet that will be used to 
        # sum up the most recent four periods. The other part of the SQL 
        # code snippet is the "AS" statement and a string to bind the sum
        # that will be calculated.
        bmy_total_string = '+'.join(
            f'{constants.QUARTER_COLUMN_PREFIX}{quarter}'
            for quarter in self.period_headers[-self.RANK_QUARTERS:]
            )
        bmy_total_string += f' AS {self.bmy_column}'
            
        # columns that will be pulled with the SQL query
        columns = ','.join([
            constants.PERMIT_COLUMN_NAME, constants.BUSINESS_COLUMN_NAME,
            period_columns_string, bmy_total_string
            ])
        
        pool_id = f'{self.jurisdiction.tac[:2]}9'
        
        # gets the top businesses from the county pool data using a SQL query
        # the businesses are grouped by the permit and then ordered highest to
        # lowest by the sum of the most recent columns specified by the count 
        # of RANK_QUARTERS. The number of businesses returned is specified by 
        # the TOP_PERMIT_COUNT constant
        internal_data = InternalData(
            is_cash=True, juri_abbrev=pool_id,
            columns=columns, group_by=constants.PERMIT_COLUMN_NAME, 
            order_by=self.bmy_column, descending=True, 
            limit=self.TOP_PERMIT_COUNT
            )
          
        data = internal_data.get_data()
        
        if data:
            quarter_totals = [[] for _ in range(self.QUARTER_COUNT)]
        
            for business in data['data']:
                permit = business[0]
                name = business[1]
                
                if not name:
                    self.blank_business_names.append(permit)
                
                self.top_businesses.append(name)
                
                # gets the amounts from the list which are between the permit 
                # and name in the beginning and the bmy total at the end 
                amounts = business[2:-1]
                
                # gets the amounts multiplied by the percent share for the juri
                amounts = self._get_juri_share_amounts(amounts)
                
                self.top_business_amounts.append(amounts)
                
                # appends each amount into a list for its quarter
                for i, amount in enumerate(amounts):
                    quarter_totals[i].append(amount)
                
                # inserts the percent change for the current quarter at the end
                amounts = self._insert_quarter_change(amounts, name)
                
            self.quarter_totals = [sum(amounts) for amounts in quarter_totals]
            
            
    def _get_juri_share_amounts(self, amounts):
        return [
            amount * self.jurisdiction_percent_shares[i] 
            for i, amount in enumerate(amounts)]
        

    def _insert_quarter_change(self, amounts, name):
        new_amount = amounts[-1]
        old_amount = amounts[-5]
        
        quarter_change = utilities.percent_change(new_amount, old_amount)
        
        self.quarter_changes[name] = quarter_change
    

    def _set_all_other_row(self):
        # list of amounts that are the difference of the total pool for 
        # the juri and the total for the top businesses 
        amounts = [
            total - self.quarter_totals[i] 
            for i, total in enumerate(self.juri_pool_amounts)]
        
        self._insert_quarter_change(amounts, self.other_row_name)
        
        self.all_others = amounts
        
            
    def _set_output_path(self):
        name = (
            f'{self.jurisdiction.id} {self.selections.period} {self.output_name}'
            )
        self.output_path = f'{self.jurisdiction.folder}{name}.{self.output_type}'
        

    def _create_excel_output(self):
        self.wb = xlsxwriter.Workbook(self.output_path)
        
        self._set_formats()
        
        self.ws = self.wb.add_worksheet(self.sheet_properties['name'])
        
        self._write_report_header()
        self._write_report_title()
        self._write_report_description()
        
        self._write_quarters(
            self.sheet_properties['rows']['quarter_headers']['one'])
        
        self._write_quarters(
            self.sheet_properties['rows']['quarter_headers']['two'])
        
        self._write_totals(
            self.county_pool_amounts, 'county_pool_amounts')
        
        self._write_totals(
            self.juri_pool_amounts, 'juri_pool_amounts', color=True,
            juri_total=True)
        
        self._write_juri_share()
        self._write_businesses()
        self._write_all_other()
        self._write_business_descriptions()
        self._write_footer()
        
        self._set_rows()
        self._set_columns()
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
            for name, properties in self.format_properties.items()}
        
        self.formats['percent_header'].set_text_wrap()
        
        
    def _get_sheet_column(self, name):
        return self.sheet_properties['columns'][name]
        
        
    def _get_sheet_row(self, name):
        return self.sheet_properties['rows'][name]
    

    def _is_current_period(self, column_numer):
        current_column = self._get_sheet_column('current_quarter')
        
        prior_year_column = self._get_sheet_column('prior_year')
        
        return column_numer in [current_column, prior_year_column]
        
        
    def _write_report_header(self):
        header = utilities.fetch_jurisdiction_header(self.jurisdiction.name)
        
        sheet_row = self._get_sheet_row('report_header')
        last_col = self._get_sheet_column('last_column')
        
        self.ws.merge_range(
            sheet_row, 0, sheet_row, last_col, header, 
            self.formats['header'])
        
        
    def _write_report_title(self):
        sheet_row = self._get_sheet_row('report_title')
        last_col = self._get_sheet_column('last_column')
        
        self.ws.merge_range(
            sheet_row, 0, sheet_row, last_col, self.report_title, 
            self.formats['title'])
        
        
    def _write_report_description(self):
        sheet_row = self._get_sheet_row('report_description')
        last_col = self._get_sheet_column('last_column')
        
        self.ws.merge_range(
                sheet_row, 0, sheet_row, last_col, self.report_description,
                self.formats['description'])
        
        
    def _write_amounts(self, amounts, sheet_row, color=False, juri_total=False):
        sheet_col = self._get_sheet_column('first_quarter')
        
        for amount in amounts:
            if self._is_current_period(sheet_col):
                format_name = (
                    'current_amount_color_bold' if juri_total 
                    else 'current_amount_color')
            
            else:
                if juri_total:
                    format_name = 'amount_color_bold'
                
                else:
                    format_name = 'amount_color' if color else 'amount'
                    
            cell_format = self.formats[format_name]
                    
            self.ws.write(sheet_row, sheet_col, amount, cell_format)
            
            sheet_col += 1
            
            
    def _write_quarter_change(self, sheet_row, name, color=False):
        sheet_col = self._get_sheet_column('last_column')
        
        quarter_change = self.quarter_changes[name]
        
        cell_format = (
            self.formats['quarter_change_color'] if color 
            else self.formats['quarter_change'])
        
        self.ws.write(sheet_row, sheet_col, quarter_change, cell_format)
        
        
    def _write_totals(self, amounts, name, color=False, juri_total=False):
        sheet_row = self._get_sheet_row(name)
        
        description = self.total_descriptions[name]
        
        format_name = (
            'total_description_color' if color else 'total_description')
        
        self.ws.write(
            sheet_row, 0, description, self.formats[format_name])
        
        self._write_amounts(
            amounts, sheet_row, juri_total=juri_total)
        
        self._write_quarter_change(sheet_row, name)
        
        
    def _write_juri_share(self):
        name = 'percent_share' 
        
        sheet_row = self._get_sheet_row('percent_share')
        
        description = self.total_descriptions[name]
        
        self.ws.write(
            sheet_row, 0, description, self.formats['total_description'])
        
        sheet_col = self._get_sheet_column('first_quarter')
        
        for percent in self.jurisdiction_percent_shares:
            format_name = (
                'current_percent_share' if self._is_current_period(sheet_col)
                else 'percent_share')
            
            cell_format = self.formats[format_name]
            
            self.ws.write(
                sheet_row, sheet_col, percent, cell_format)
        
            sheet_col += 1
        
        
    def _write_businesses(self):
        color = False
        
        sheet_row = self._get_sheet_row('first_business')
        
        for i, business in enumerate(self.top_businesses):
            amounts = self.top_business_amounts[i] 
            
            name_format_name = 'business_color' if color else 'business'
            name_format = self.formats[name_format_name]
            
            self.ws.write(sheet_row, 0, business, name_format)
            
            self._write_amounts(amounts, sheet_row, color)
            
            self._write_quarter_change(sheet_row, business, color)
            
            sheet_row += 1
            
            color = False if color else True
            
            
    def _write_all_other(self):
        sheet_row = self._get_sheet_row(self.other_row_name)
        
        self.ws.write(
            sheet_row, 0, self.other_row_name, self.formats['business_color'])
        
        self._write_amounts(
            self.all_others, sheet_row, color=True)
        
        self._write_quarter_change(
            sheet_row, self.other_row_name, color=True)
        
        
    def _write_quarters(self, sheet_row):
        sheet_col = self.sheet_properties['columns']['first_quarter']
        
        for period in self.period_headers:
            format_name = (
                'current_quarter' if self._is_current_period(sheet_col)
                else 'quarter')
            
            cell_format = self.formats[format_name]
            
            self.ws.write(
                sheet_row, sheet_col, period, cell_format)
            
            sheet_col += 1
            
        self.ws.write(
            sheet_row, sheet_col, 'Quarter Over Quarter', 
            self.formats['percent_header'])
        
        self.ws.set_row(
            sheet_row, self.sheet_properties['quarter_row_height'])
        
        
    def _write_business_descriptions(self):
        sheet_row = self._get_sheet_row('business_description')
        sheet_col = 0
        
        self.ws.write(
            sheet_row, sheet_col, self.business_description, 
            self.formats['business_description'])
        
        sheet_row += 1
        
        self.ws.write(
            sheet_row, sheet_col, 'Business', self.formats['quarter'])
        
        
    def _set_columns(self):
        # sets the width of the column width the business names
        self.ws.set_column(0, 0, 32)
        
        first_quarter_column = self._get_sheet_column('first_quarter')
        last_quarter_column = self._get_sheet_column('current_quarter')
        
        # sets the width of the quarter columns
        self.ws.set_column(first_quarter_column, last_quarter_column, 10.9)
        
        last_column = self._get_sheet_column('last_column')
        
        # sets the width of the percent change column
        self.ws.set_column(last_column, last_column, 8.5)
        
        
    def _set_rows(self):
        row_height = self.sheet_properties['business_row_height']
        
        # sets the business rows
        sheet_row = self._get_sheet_row('first_business')
        for _ in range(self.TOP_PERMIT_COUNT + 1):
            self.ws.set_row(sheet_row, row_height)
            
            sheet_row += 1
            
        # sets the total rows
        sheet_row = self._get_sheet_row('county_pool_amounts')
        for _ in range(3):
            self.ws.set_row(sheet_row, row_height)
            
            sheet_row += 1
        
        
    def _write_footer(self):
        footer = (
            f'&L{constants.LEFT_CONFIDENTIAL_FOOTER}&R{constants.RIGHT_FOOTER}'
            )
        
        self.ws.set_footer(footer)
        
        
    def _set_page(self):
        self.ws.set_landscape()
        
        self.ws.set_margins(left=0.25, right=0.15, top=0.5, bottom=0.5)
        
        self.ws.print_area(
            0, 0, self._get_sheet_row(self.other_row_name),  
            self._get_sheet_column('last_column')
            )
        
        self.ws.fit_to_pages(1, 1)
        
        
    def _create_blank_businesses_file(self):
        name = f'{self.jurisdiction.id} - Permits With Blank Names.txt'
        
        path = str(constants.TEMP_FILE_PATH.joinpath(name))
        
        with open(path, 'w+') as file:
            for permit in self.blank_business_names:
                file.write(f'{permit}\n')
                
        utilities.open_file(path)
        
        
        
        
        
        
        
        
        
        