'''
Created on Dec 28, 2018

@author: vahidrogo
'''

import sqlite3 as sql
import threading
import tkinter as tk
from tkinter import ttk

import constants
from jurisdiction import Jurisdiction
from tooltip import ToolTip
import progress
import utilities



class Model(threading.Thread):
    '''
    '''
    
    
    def __init__(
            self, lookup_value, by, basis, condition, jurisdiction_type, 
            region, output, title, columns
            ):
        super().__init__()
        self.daemon = True
        
        self.lookup_value = lookup_value
        self.by = by
        self.basis = basis
        self.condition = condition
        self.type = jurisdiction_type
        self.region = region
        self.output_type = output
        self.title = title
        self.columns = columns
        
        self.values_db = (
            constants.QUARTERLY_CASH_DB if self.basis == 'cash' 
            else constants.QUARTERLY_ECONOMIC_DB
            )
        
        self.query = ''
        self.query_condition = ''
        self.output_path = ''
        
        self.result_count = 0
        
        self.business_tables = []
        self.lookup_tables = []
        self.value_tables = {}
        
        self.results = []
        
        self.con = None
        
        self.abort = False
        
        
    def run(self):
        self.progress = progress.Progress(self, self.title)
        
        self.progress.update_progress(0, f'Verifying {self.region} tables.')
        
        self._set_business_tables()
        self._set_value_tables()
        self._set_lookup_tables()
        
        self._set_query_condition()
        self._set_query()
        
        self._set_con()
        self._attach_values_db()
        
        self._query_tables()
        
        self.con.close()
        
        if not self.abort:
            if self.results:
                self._set_output_path()
                
                utilities.Output.output(
                        self.results, self.output_path, self.columns
                        )
                
                self.progress.update_progress(100, 'Finished.')
                 
                utilities.open_file(self.output_path)
            
            self.progress.destroy()
        
        
    def _set_business_tables(self):
        self.business_tables = utilities.get_table_names(constants.BUSINESSES_DB)
    
    
    def _set_value_tables(self):
        self.value_tables = set(utilities.get_table_names(self.values_db))
        
        
    def _set_lookup_tables(self):
        '''
            Sets the final list of tables that will be queried.
        '''
        for table_name in self.business_tables:
            # if the table has a corresponding table with amounts
            if table_name in self.value_tables:
                if self._include_table(table_name):
                    self.lookup_tables.append(table_name)
        
        
    def _set_query_condition(self):
        if self.condition == 'begins with':
            self.query_condition = f' LIKE "{self.lookup_value}%"'
        
        elif self.condition == 'contains':
            self.query_condition = f' LIKE "%{self.lookup_value}%"'
        
        elif self.condition == 'ends with':
            self.query_condition = f' LIKE "%{self.lookup_value}"'
        
        else:
            self.query_condition = f' ="{self.lookup_value}"'
        
        
    def _set_query(self):
        self.query = f'''
            SELECT {','.join(self.columns)}
            
            FROM table_name
            
            NATURAL JOIN {self.values_db}.table_name
            
            WHERE {self.by}{self.query_condition}
            
            COLLATE NOCASE
            '''
        
        
    def _set_con(self):
        self.con = sql.connect(
            constants.DB_PATHS[constants.BUSINESSES_DB], uri=True,
            timeout=constants.DB_TIMEOUT
            )
        
        
    def _attach_values_db(self):
        sql_code = 'ATTACH DATABASE ? AS ?'
        
        args = (str(constants.DB_PATHS[self.values_db]), self.values_db)
        
        utilities.execute_sql(
            sql_code=sql_code, args=args, open_con=self.con, dontfetch=True
            )
        
 
    def _include_table(self, table_name):
        include = False
        
        jurisdiction = Jurisdiction(jurisdiction_id=table_name)
        
        if self._in_region(jurisdiction):
            if self.type == 'addon':
                include = jurisdiction.type in ['addon', 'transit']
            
            else:
                include = jurisdiction.type == 'jurisdiction'
        
        return include
    
    
    def _in_region(self, jurisdiction):
        in_region = False
        
        if self.region == 'Statewide':
            in_region = True
        
        elif self.region == 'Southern California':
            in_region = jurisdiction.is_southern == 1
        
        elif self.region == 'Northern California':
            in_region = jurisdiction.is_southern == 0
        
        else:
            in_region = jurisdiction.region_name.lower() == self.region.lower()
        
        return in_region
        
        
    def _query_tables(self):
        table_count = len(self.lookup_tables)
        
        progress = 1
        
        for i, table_name in enumerate(self.lookup_tables, start=1):
            if not self.abort:
                self.progress.update_progress(
                    progress, 
                    f'Querying table {i} of {table_count}: {table_name}'
                    '    Results for "{}" = {:,}'.format(
                        self.lookup_value, self.result_count
                        )
                    )
                
                query = self.query.replace('table_name', table_name)
                
                results = utilities.execute_sql(
                    sql_code=query, open_con=self.con, fetchall=True, 
                    show_error=False
                    )
                    
                if results:
                    self.results.extend(results)
                    
                    self.result_count += len(results)
                
            progress += 100 / table_count
            
            
    def _set_output_path(self):
        folder = constants.TEMP_FILE_PATH
        
        name = (
            f'{self.lookup_value}_{self.region}_lookup'
            f'_{utilities.timestamp()}.{self.output_type}'
            )
        
        self.output_path = str(folder.joinpath(name))
        

class Controller:
    '''
        Queries each table in businesses.db joined with the table from 
        either quarterly_cash.db or quarterly_econmic.db for each jurisdiction.
    '''
    
    
    title = f'{constants.APP_NAME} - Business Lookup'
    
    options = {
        'basis' : ['cash', 'economic'], 
        
        'by' : ['business', 'permit'],
        
        'condition' : ['begins with', 'contains', 'ends with', 'equals'],
        
        'region' : [
            'Central Coast', 'Central Valley', 'Inland Empire', 'North Coast',
            'Northern California', 'Other Northern', 'Other Southern', 
            'S.F. Bay Area', 'Sacramento Valley', 'South Coast', 
            'Southern California', 'Statewide'
            ],
        
        'type' : ['addon', 'jurisdiction'],
        
        'output' : ['csv', 'xlsx']
        }
    
    DEFAULT_YEARS = 5
    
    
    def __init__(self, period_options, selected_period):
        self.period_options = period_options
        self.selected_period = selected_period
        
        self.by = ''
        
        self.run_enabled = False
        
        self.columns = constants.BUSINESS_TABLE_COLUMNS
        
        self.gui = View(self)
        
        self._set_to_period()
        self._set_default_options()
        
        
    def _set_to_period(self):
        year, quarter = self.selected_period.split('Q')
        
        to_year = int(year) - self.DEFAULT_YEARS
        
        self.to_period = f'{to_year}Q{quarter}'
        
        
    def _set_default_options(self):
        # sets the default value for the basis combobox to "economic"
        self.gui.basis_var.set(self.options['basis'][1])
        
        # sets the default value for the by combobox to "business"
        self.gui.by_var.set(self.options['by'][0])
        
        # sets the default value for the condition combobox to "begins with"
        self.gui.condition_var.set(self.options['condition'][0])
        
        # sets the default value for the output combobox to "csv"
        self.gui.output_var.set(self.options['output'][0])
        
        # sets the default value for the type combobox to "jurisdiction"
        self.gui.type_var.set(self.options['type'][1])
        
        # sets the default value for the region combobox to "statewide"
        self.gui.region_var.set(self.options['region'][-1])
        
        # sets the default value for the from combobox to the selected period
        self.gui.from_var.set(self.selected_period)
        
        # sets the default value for the to combobox to the default to period
        self.gui.to_var.set(self.to_period)
    
    
    def on_run_click(self):
        lookup_value = self.gui.lookup_var.get().strip()
        
        if lookup_value:
            self._set_columns()
            
            by = self.gui.by_var.get()
            
            valid_lookup_value = True
            
            if self._is_by_permit(by):
                # check that the format of the permit is correct
                # if it is not the correct format then set the 
                # valid lookup to false
                print('looking by permit', lookup_value)
            
            if valid_lookup_value:
                basis = self.gui.basis_var.get()
                condition = self.gui.condition_var.get()
                jurisdiction_type = self.gui.type_var.get()
                region = self.gui.region_var.get()
                output = self.gui.output_var.get()
                
                self.Model = Model(
                    lookup_value, by, basis, condition, jurisdiction_type, region,
                    output, self.title, self.columns
                    )
                 
                self.Model.start()
            
            
    def on_by_change(self, *args):
        by = self.gui.by_var.get()
        
        # if its not the first time changing the by option
        if self.by:
            # if the by option has changed
            if by != self.by:
                if self._is_by_permit(by):
                    self.gui.make_permit_tooltip()
                
                else:
                    self.gui.permit_tooltip.delete()
                    
                self.by = by
                
        else:
            # sets the initial state of the by option
            self.by = by
            
            
    def _is_by_permit(self, by):
        return by == 'permit'
        
        
    def on_lookup_value_change(self, *args):
        lookup_value = self.gui.lookup_var.get()
        
        if lookup_value:
            if not self.run_enabled:
                self.gui.enable_run_button()
                
                self.run_enabled = True
        
        else:
            if self.run_enabled:
                self.gui.disable_run_button()
                
                self.run_enabled = False
                
                
    def _set_columns(self):
        from_period = self.gui.from_var.get()
        to_period = self.gui.to_var.get()
        
        from_index = self.period_options.index(from_period)
        to_index = self.period_options.index(to_period)
        
        periods = self.period_options[to_index : from_index + 1]
        
        periods = [f'{constants.QUARTER_COLUMN_PREFIX}{i}' for i in periods]
        
        self.columns = constants.BUSINESS_TABLE_COLUMNS + periods


class View(tk.Toplevel):
    '''
    '''
    
    
    WINDOW_HEIGHT = 157
    WINDOW_WIDTH = 500
    
    COMBO_WIDTH = 25
    ENTRY_WIDTH = COMBO_WIDTH
    LEFT_LABEL_WIDTH = 5
    RIGHT_LABEL_WIDTH = 10
    
    
    def __init__(self, controller):
        super().__init__()
        
        self.controller = controller
        
        self.permit_tooltip = None
        
        self.basis_var = tk.StringVar()
        self.by_var = tk.StringVar()
        self.condition_var = tk.StringVar()
        self.from_var = tk.StringVar()
        self.lookup_var = tk.StringVar()
        self.output_var = tk.StringVar()
        self.region_var = tk.StringVar()
        self.to_var = tk.StringVar()
        self.type_var = tk.StringVar()
        
        self.by_var.trace('w', self.controller.on_by_change)
        self.lookup_var.trace('w', self.controller.on_lookup_value_change)
        
        self.title(self.controller.title)
        
        self._center_window()
        
        self._make_widgets()
        
        # prevents the window from being resized
        self.resizable(width=False, height=False)
        

    def _center_window(self):
        x_offset = (self.winfo_screenwidth() - self.WINDOW_WIDTH) // 2
        y_offset = (self.winfo_screenheight() - self.WINDOW_HEIGHT) // 2
        
        self.geometry(f'+{x_offset}+{y_offset}')
        
        
    def _make_widgets(self):
        self.lookup_frm = ttk.Frame(self)
        options_frm = ttk.Labelframe(self, text='Options')
        button_frm = ttk.Frame(self)
        
        option_frm_one = ttk.Frame(options_frm)
        option_frm_two = ttk.Frame(options_frm)
        option_frm_three = ttk.Frame(options_frm)
        option_frm_four = ttk.Frame(options_frm)
        
        by_frm = ttk.Frame(option_frm_one)
        condition_frm = ttk.Frame(option_frm_one)
        type_frm = ttk.Frame(option_frm_two)
        region_frm = ttk.Frame(option_frm_two)
        from_frm = ttk.Frame(option_frm_three)
        to_frm = ttk.Frame(option_frm_three)
        basis_frm = ttk.Frame(option_frm_four)
        output_frm = ttk.Frame(option_frm_four)
        
        lookup_lbl = ttk.Label(self.lookup_frm, text='Lookup:')
        
        lookup_ent = ttk.Entry(self.lookup_frm, textvariable=self.lookup_var)
        lookup_ent.focus()
        
        by_lbl = ttk.Label(by_frm, text='By:', width=self.LEFT_LABEL_WIDTH)
        
        by_cbo = ttk.Combobox(
            by_frm, values=self.controller.options['by'], state='readonly',
            textvariable=self.by_var, width=self.COMBO_WIDTH
            )
        
        condition_lbl = ttk.Label(
            condition_frm, text='Condition:', width=self.RIGHT_LABEL_WIDTH
            )
        
        condition_cbo = ttk.Combobox(
            condition_frm, values=self.controller.options['condition'], 
            state='readonly', textvariable=self.condition_var, 
            width=self.COMBO_WIDTH
            )
        
        type_lbl = ttk.Label(type_frm, text='Type:', width=self.LEFT_LABEL_WIDTH)
        
        type_cbo = ttk.Combobox(
            type_frm, values=self.controller.options['type'], state='readonly',
            textvariable=self.type_var, width=self.COMBO_WIDTH
            )
        
        region_lbl = ttk.Label(
            region_frm, text='Region:', width=self.RIGHT_LABEL_WIDTH
            )
        
        region_cbo = ttk.Combobox(
            region_frm, values=self.controller.options['region'],
            state='readonly', textvariable=self.region_var, 
            width=self.COMBO_WIDTH
            )
        
        from_lbl = ttk.Label(
            from_frm, text='From:', width=self.LEFT_LABEL_WIDTH
            )
        
        from_cbo = ttk.Combobox(
            from_frm, values=self.controller.period_options, state='readonly', 
            textvariable=self.from_var, width=self.COMBO_WIDTH
            )
        
        to_lbl = ttk.Label(to_frm, text='To:', width=self.RIGHT_LABEL_WIDTH)
        
        to_cbo = ttk.Combobox(
            to_frm, values=self.controller.period_options, state='readonly',
            textvariable=self.to_var, width=self.COMBO_WIDTH
            )
        
        basis_lbl = ttk.Label(
            basis_frm, text='Basis:', width=self.LEFT_LABEL_WIDTH
            )
        
        basis_cbo = ttk.Combobox(
            basis_frm, values=self.controller.options['basis'], state='readonly', 
            textvariable=self.basis_var, width=self.COMBO_WIDTH
            )
        
        output_lbl = ttk.Label(
            output_frm, text='Output:', width=self.RIGHT_LABEL_WIDTH
            )
        
        output_cbo = ttk.Combobox(
            output_frm, values=self.controller.options['output'], state='readonly',
            textvariable=self.output_var, width=self.COMBO_WIDTH
            )
        
        self.run_btn = ttk.Button(
            button_frm, text='Run', command=self.controller.on_run_click
            )
        
        self.disable_run_button()
        
        cancel_btn = ttk.Button(button_frm, text='Cancel', command=self.destroy)
        
        self.lookup_frm.pack(
            fill='x', padx=constants.OUT_PAD, pady=constants.OUT_PAD
            )
        
        options_frm.pack(fill='x', padx=constants.OUT_PAD)
        
        button_frm.pack(anchor='e', pady=constants.OUT_PAD)
        
        option_frm_one.pack()
        option_frm_two.pack(pady=constants.IN_PAD)
        option_frm_three.pack()
        option_frm_four.pack(pady=constants.IN_PAD)
        
        by_frm.pack(side='left', padx=constants.OUT_PAD)
        condition_frm.pack(padx=constants.OUT_PAD)
        
        type_frm.pack(side='left', padx=constants.OUT_PAD)
        region_frm.pack(padx=constants.OUT_PAD)
        
        from_frm.pack(side='left', padx=constants.OUT_PAD)
        to_frm.pack(padx=constants.OUT_PAD)
        
        basis_frm.pack(side='left', padx=constants.OUT_PAD)
        output_frm.pack(padx=constants.OUT_PAD)
        
        lookup_lbl.pack(side='left')
        lookup_ent.pack(fill='x')
        
        by_lbl.pack(side='left')
        by_cbo.pack()
        
        condition_lbl.pack(side='left')
        condition_cbo.pack()
        
        type_lbl.pack(side='left')
        type_cbo.pack()
        
        region_lbl.pack(side='left')
        region_cbo.pack()
        
        from_lbl.pack(side='left')
        from_cbo.pack()
        
        to_lbl.pack(side='left')
        to_cbo.pack()
        
        basis_lbl.pack(side='left')
        basis_cbo.pack()
        
        output_lbl.pack(side='left')
        output_cbo.pack()
        
        self.run_btn.pack(side='left')
        cancel_btn.pack(padx=constants.OUT_PAD)
        
        
    def disable_run_button(self):
        self.run_btn.config(state='disabled')
    
    
    def enable_run_button(self):
        self.run_btn.config(state='enabled')
        
        
    def make_permit_tooltip(self):
        self.permit_tooltip = ToolTip(
            self.lookup_frm, 
            f'Format: {constants.PERMIT_FORMAT}\n"-" is optional.'
            )
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        