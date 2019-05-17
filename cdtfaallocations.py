'''
Created on Jan 10, 2019

@author: vahidrogo
'''

import ntpath
import PyPDF2
import re
import requests
import threading
import tkinter as tk
from tkinter import messagebox as msg
from tkinter import ttk
import traceback

import constants
import progress
import utilities

'''
    TODO:
        1. Work on the "net" calculated amounts
        2. Add data for addons
        3. Add "RDA" data
'''

class Model(threading.Thread):
    '''
    '''
    
    
    jurisdiction_separator = '==============================================================================================================='
    
    # the indexes of the figures as they are pulled from the file
    input_indexes = {
        'month_1' : 0,
        'month_2' : 1,
        'month_3' : 2,
        'gross' : 3,
        'county_pool_percent' : 4,
        'county_pool_amount' : 5,
        'state_pool_percent' : 6,
        'state_pool_amount' : 7,
        'county_share_percent' : 8,
        'jurisdiction_share_percent' : 9,
        'adjusted_gross' : 10,
        'county_share_amount' : 11,
        'jurisdiction_share_amount' : 12,
        'state_tax' : 13,
        'local_tax' : 14,
        'prior_advance' : 15,
        'admin' : 16, 
        'total' : 17,
        }

    # the last period that has the state tax allocation
    state_tax_last_period = (2015, 4)
    
    
    def __init__(self, file_url, period, title, gui):
        super().__init__()
        
        self.daemon = True
        
        self.file_url = file_url
        self.period = period
        self.title = title
        self.gui = gui
        
        self.file_content = ''
        self.file_metadata = ''
        self.file_period = ''
        
        self.table_exists = False
        
        self.allocations = {}
        
        self.amount_pattern = re.compile(
            r'\d{0,3},?\d{0,3},?\d{1,3}\.\d{2,} ?[-|%]?'
            )
        
        # pattern to match quarter like "3q18"
        self.quarter_pattern = re.compile(
            r'([1-4])q-?(\d{2})', re.IGNORECASE
            )
        
        self.tac_pattern = re.compile(r'-? ?(\d{5}) -')
        
        self._set_output_columns()
        self._set_has_state_tax()
        self._set_table_exists()
        
        
    def _set_output_columns(self):
        columns = [
            constants.ID_COLUMN_NAME, constants.TAC_COLUMN_NAME, 'period'
            ]
        
        # adds all the names of the input columns
        columns.extend(self.input_indexes.keys())
        
        # adds the name for the net column
        columns.append('net')
        
        self.output_columns = columns
        
        
    def _set_has_state_tax(self):
        year, quarter = self.period.split('Q')
        
        self.has_state_tax = (int(year), int(quarter)) <= self.state_tax_last_period
        
        
    def _set_table_exists(self):
        table_names = utilities.get_table_names(constants.STATEWIDE_DATASETS_DB)
        
        self.table_exists = constants.CDTFA_ALLOCATION_TABLE in table_names
        
        
    def run(self):
        loading_circle = progress.LoadingCircle(parent=self.gui)
        loading_circle.start()
        
        try:
            load = True
            
            if self._period_exists():
                answer = msg.askyesno(
                    self.title, 
                    f'Data for period ({self.period}) already exists in '
                    f'({constants.STATEWIDE_DATASETS_DB}.'
                    f'{constants.CDTFA_ALLOCATION_TABLE}). Continuing will '
                    f'overwrite existing records, would you like to continue?',
                    parent=self.gui
                    )
                
                if answer:
                    self._delete_existing_records()
                    
                else:
                    load = False
            
            if load:
                self._set_file_period()
                      
                period_verified = False
                  
                if not self.file_period:
                    answer = msg.askyesno(
                        self.title, 
                        'Unable to automatically verify the period on the file.'
                        '\nWould you like to continue?',
                        parent=self.gui
                        )
                      
                    if answer:
                        period_verified = True
                          
                elif self.file_period != self.period:
                    msg.showinfo(
                        self.title, 
                        f'The period on the file ({self.file_period}) does '
                        f'not match the selected period ({self.period}).', 
                        parent=self.gui
                        )
                      
                else:
                    period_verified = True
                          
                if period_verified:
                    self._set_file_content()
                 
                    self._set_allocations()
                      
                    if not self.table_exists:
                        self._create_table()
                           
                    if self.table_exists:
                        # inserts the data from the pdf into the table
                        self._insert_values()
                        
        except:
            msg.showerror(
                self.title, 
                f'Unhandled exception occurred:\n\n{traceback.format_exc()}',
                parent=self.gui
                )
            
        finally:
            loading_circle.end()
            
            
    def _period_exists(self):
        exists = False
        
        if self.table_exists:
            query = f'''
                SELECT COUNT(*)
                FROM {constants.CDTFA_ALLOCATION_TABLE}
                WHERE period=?
                '''
            
            args = (self.period, )
            
            results = utilities.execute_sql(
                sql_code=query, args=args, db_name=constants.STATEWIDE_DATASETS_DB,
                show_error=False
                )
            
            if results:
                count = results[0]
                
                if count:
                    exists = True
                
        return exists
    
    
    def _delete_existing_records(self):
        '''
            Deletes all existing records for the period from the table.
        '''
        
        sql_code = f'''
            DELETE 
            FROM {constants.CDTFA_ALLOCATION_TABLE}
            WHERE period=?
            '''
        
        args = (self.period, )
        
        utilities.execute_sql(
            sql_code=sql_code, args=args, 
            db_name=constants.STATEWIDE_DATASETS_DB
            )
        
        
    def _set_file_period(self):
        match = re.search(self.quarter_pattern, self.file_url)
        
        year = quarter = ''
        
        if match:
            quarter = match.group(1)
            year = match.group(2)
            
        if year and quarter:
            self.file_period = f'20{year}Q{quarter}'
        

    def _set_file_content(self):
        content = ''
        
        response = requests.get(self.file_url)
        
        if response:
            content = response.content
            
            if content:
                file_name = ntpath.basename(self.file_url)
                temp_path = str(constants.TEMP_FILE_PATH.joinpath(file_name))
                
                # writes the contents to a temporary pdf file
                with open(temp_path, 'wb') as file:
                    file.write(content)
                
                # opens the temp pdf file that was just written
                file = open(temp_path, 'rb')
                
                pdf_reader = PyPDF2.PdfFileReader(file)
                
                page_count = pdf_reader.numPages
                
                for i in range(page_count):
                    page = pdf_reader.getPage(i)
                    
                    self.file_content += page.extractText()
        

    def _set_allocations(self):
        allocations = self.file_content.split(self.jurisdiction_separator)
        
        for allocation in allocations:
            allocation = allocation.strip()
            
            if allocation:
                tac = self._extract_tac(allocation)
                
                if tac:
                    amounts = self._extract_amounts(allocation)

                    if amounts:
                        self._check_unincorporated(tac, amounts)
                        self._check_state_tax(amounts)
                        
                        self._check_amount_order(amounts)
                        
                        self._convert_amounts(amounts)
                        
                        self._check_county_share_amount(amounts)
                        
                        self._insert_net(amounts)
                            
                        self.allocations[tac] = amounts


    def _extract_tac(self, allocation):
        match = re.search(self.tac_pattern, allocation)
        
        if match:
            tac = match.group(1)
            
        else:
            tac = ''
            
        return tac
    
    
    def _extract_amounts(self, allocation):
        return re.findall(self.amount_pattern, allocation)
    
    
    def _check_unincorporated(self, tac, amounts):
        '''
            If the tac is for an unincorporated jurisdiction then zeros will 
            be inserted for the county share and jurisdiction share percents
            as place holders since the unincorporated do not have those figures 
            on the file.
        '''
        if utilities.is_unincorporated(tac):
            # inserts a zero for the county share percent
            amounts.insert(self.input_indexes['county_share_percent'], 0)
            
            # inserts a zero for the jurisdiction share percent
            amounts.insert(self.input_indexes['jurisdiction_share_percent'], 0)
            
            
    def _check_state_tax(self, amounts):
        '''
            If the period is newer than 2015Q4 then a zero is put in as a place 
            holder for the state tax since that was the last period for the 
            state tax. 
        '''
        if not self.has_state_tax:
            # inserts a zero for the state tax
            amounts.insert(self.input_indexes['state_tax'], 0)
            
            
    def _check_amount_order(self, amounts):
        gross_index = self.input_indexes['gross']
        
        gross = amounts[gross_index]
        
        # if the amount has a percent in it then it is probably the county 
        # pool percent instead of the gross
        if isinstance(gross, str) and '%' in gross:
            county_pool_percent = gross
            state_pool_percent = amounts[gross_index + 1]
            gross = amounts[gross_index + 2]
            county_pool_amount = amounts[gross_index + 3]
            
            # inserts the amount in the correct order
            amounts[self.input_indexes['gross']] = gross
            amounts[self.input_indexes['county_pool_percent']] = county_pool_percent
            amounts[self.input_indexes['county_pool_amount']] = county_pool_amount
            amounts[self.input_indexes['state_pool_percent']] = state_pool_percent
    
    
    def _convert_amounts(self, amounts):
        for i, amount in enumerate(amounts):
            inverse = False
            percent = False
            
            if isinstance(amount, str):
                if ',' in amount:
                    # removes the comma
                    amount = amount.replace(',', '')
                    
                if amount[-1] == '-':
                    inverse = True
                    
                    amount = amount.replace('-', '')
                    
                if amount[-1] == '%':
                    percent = True
                    
                    amount = amount.replace('%', '')
                    
            amount = float(amount)
            
            if inverse:
                amount = -amount
                
            if percent:
                amount = amount / 100
            
            amounts[i] = amount
            
            
    def _check_county_share_amount(self, amounts):
        '''
            Converts the county share amount to negative, some files have it 
            already negative and some don't.
        '''
        county_share_amount = amounts[self.input_indexes['county_share_amount']]
                        
        # inverts the county share amount if it is not negative
        if county_share_amount > 0:
            county_share_amount = -county_share_amount
            
            amounts[self.input_indexes['county_share_amount']] = county_share_amount
            
            
    def _insert_net(self, amounts):
        '''
            Calculates the net by summing up the jurisdiction share and the 
            admin amounts then adds the net amount to the end of the list.
        '''
        jurisdiction_share = amounts[self.input_indexes['jurisdiction_share_amount']]
        admin = amounts[self.input_indexes['admin']]
        
        net = jurisdiction_share + admin 
        
        # adds the calculated net to the end of the list of amounts
        amounts.append(net)
    
    
    def _create_table(self):
        # begins the column string with the id column as the primary key
        column_string = f'{constants.ID_COLUMN_NAME} primary key, '
        
        # adds the rest of the columns to the string
        column_string += ','.join(self.output_columns[1:])
        
        sql_code = (
            f'CREATE TABLE {constants.CDTFA_ALLOCATION_TABLE} ({column_string})'
            )
        
        table_created = utilities.execute_sql(
            sql_code=sql_code, db_name=constants.STATEWIDE_DATASETS_DB, 
            dml=True
            )
        
        if table_created:
            self.table_exists = True
            
            
    def _insert_values(self):
        place_holders = ['?' for _ in range(len(self.output_columns))]
        
        sql_code = (
            f'INSERT INTO {constants.CDTFA_ALLOCATION_TABLE}'
            f'({",".join(self.output_columns)}) VALUES({",".join(place_holders)})'
            )
        
        # inserts an id consisting of the tac and the period for each of the 
        # amounts and also inserts the period in its own column
        values = [
            [f'{tac}-{self.period}', tac, self.period, ] + amounts 
            for tac, amounts in self.allocations.items()
            ]
        
        args = values
         
        utilities.execute_sql(
            sql_code=sql_code, args=args, dml=True, many=True, 
            db_name=constants.STATEWIDE_DATASETS_DB
            )
            

class Controller:
    '''
    '''
    
    # the urls have changed, the first one is the oldest
    # the first "{}" is for the quarter and the second is for the year
    file_url_one = 'https://www.boe.ca.gov/sutax/pdf/{}q{}-distribution.pdf'
    file_url_two = 'http://boe.ca.gov/sutax/pdf/{}q-{}-distribution.pdf'
    file_url_three = 'https://www.cdtfa.ca.gov/taxes-and-fees/{}q-{}-distribution.pdf'
    fourth_quarter_2011_url = 'https://www.boe.ca.gov/sutax/pdf/{}q{}-distribution-1.pdf'
    
    # the year and quarter that the file url changed from one to two
    file_url_change_one = (15, 3)
    
    # the year and quarter that the file url changed from two to three
    file_url_change_two = (17, 4)
    
    title = f'{constants.APP_NAME} - CDTFA Allocations'
    
    
    def __init__(self, period_options, selected_period):
        self.period_options = period_options
        self.selected_period = selected_period
        
        self._set_file_url()
        
        self.gui = View(self)
        

    def _set_file_url(self):
        year, quarter = self.selected_period.split('Q')
        
        # sets the file url based on the most current url
        self.file_url = self.file_url_three.format(quarter, year[-2:])
        
        
    def on_period_change(self, *args):
        period = self.gui.period.get()
        
        if period != self.selected_period:
            year, quarter = period.split('Q')
            
            # only need the last two digits of the year
            year = int(year[-2:])
            quarter = int(quarter)
            
            # if the period is fourth quarter 2011
            if (year, quarter) == (11, 4):
                file_url = self.fourth_quarter_2011_url
                
            elif (year, quarter) >= self.file_url_change_two:
                # if the period is newer than the most recent url change
                file_url = self.file_url_three
                
            elif (year, quarter) >= self.file_url_change_one:
                # if the period is newer than first url change
                file_url = self.file_url_two
                
            else:
                file_url = self.file_url_one
                
            self.file_url = file_url.format(quarter, year)
            
            self.gui.file_url.set(self.file_url)
            
            self.selected_period = period
        
        
    def on_load_click(self):
        file_url = self.gui.file_url.get().strip()
        
        if self.file_url:
            model = Model(file_url, self.selected_period, self.title, self.gui)
            
            model.start()
    
    
class View(tk.Toplevel):
    '''
    '''
    
    
    WINDOW_HEIGHT = 110
    WINDOW_WIDTH = 500
    
    LABEL_WIDTH = 6
    
    
    def __init__(self, controller):
        super().__init__()
        
        self.controller = controller
        
        self.file_url = tk.StringVar(value=self.controller.file_url)
        
        self.period = tk.StringVar(value=self.controller.selected_period)
        
        self.period.trace('w', self.controller.on_period_change)
        
        self.title(self.controller.title)
        
        # prevents the window from being resized
        self.resizable(width=False, height=False)
        
        self._center_window()
        
        self._make_widgets()
        
        
    def _center_window(self):
        x_offset = (self.winfo_screenwidth() - self.WINDOW_WIDTH) // 2
        y_offset = (self.winfo_screenheight() - self.WINDOW_HEIGHT) // 2
        
        self.geometry(
            f'{self.WINDOW_WIDTH}x{self.WINDOW_HEIGHT}+{x_offset}+{y_offset}'
            )
        
        
    def _make_widgets(self):
        period_frm = ttk.Frame(self)
        file_frm = ttk.Frame(self)
        button_frm = ttk.Frame(self)
        
        period_lbl = ttk.Label(
            period_frm, text='Period:', width=self.LABEL_WIDTH
            )
        
        period_cbo = ttk.Combobox(
            period_frm, justify='right', state='readonly', textvariable=self.period,
            values=self.controller.period_options, width=8
            )
        
        file_lbl = ttk.Label(file_frm, text='File:', width=self.LABEL_WIDTH)
        file_ent = ttk.Entry(file_frm, textvariable=self.file_url)
        
        load_btn = ttk.Button(
            button_frm, text='Load', command=self.controller.on_load_click
            )
        
        cancel_btn = ttk.Button(
            button_frm, text='Cancel', command=self.destroy
            )
        
        period_frm.pack(
            anchor='w', padx=constants.OUT_PAD, pady=constants.OUT_PAD
            )
        
        file_frm.pack(expand=1, fill='x', padx=constants.OUT_PAD)
        
        button_frm.pack(
            anchor='e', padx=constants.OUT_PAD, pady=constants.OUT_PAD
            )
        
        period_lbl.pack(side='left')
        period_cbo.pack()
        
        file_lbl.pack(anchor='w', side='left')
        file_ent.pack(fill='x', expand=1)
        
        load_btn.pack(side='left', padx=constants.OUT_PAD)
        cancel_btn.pack()
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
