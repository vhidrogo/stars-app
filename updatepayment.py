'''
Created on Jan 17, 2019

@author: vahidrogo
'''

import threading
import tkinter as tk
from tkinter import ttk

from comboboxautocomplete import ComboboxAutoComplete
import constants
import progress
import utilities


class Controller:
    '''
    '''
    
    
    title = f'{constants.APP_NAME} - Update Payment'
    
    basis_options = ['cash', 'economic']
    default_basis = basis_options[1]
    
    
    def __init__(self, period_options, selected_period):
        self.period_options = period_options
        self.selected_period = selected_period
        
        self.db_name = constants.QUARTERLY_ECONOMIC_DB
        self.permit = ''
        self.table_name = ''
        
        self.new = 0
        self.sub = 0
        
        self.fetch_enabled = False
        self.update_enabled = False
        
        self._set_table_names()
        
        self.gui = View(self, self.title)
        self.gui.disable_fetch_button()
        self.gui.disable_update_button()
        
        
    def _set_table_names(self):
        table_names = utilities.get_table_names(constants.BUSINESSES_DB)
        table_names.sort()
        self.table_names = table_names
        
        
    def on_basis_change(self, *args):
        basis = self.gui.basis.get()
        
        if basis != self.basis:
            self.basis = basis
            
            if basis == 'economic':
                self.db_name = constants.QUARTERLY_ECONOMIC_DB
                
            else:
                self.db_name = constants.QUARTERLY_CASH_DB
        
        
    def on_table_change(self, *args):
        table_name = self.gui.table.get().strip()
        
        if table_name:
            if table_name != self.table_name and table_name in self.table_names:
                self.table_name = table_name
                
                if self.permit and self.sub:
                    if not self.fetch_enabled:
                        self._enable_fetch()
                        
                    if self.new:
                        if not self.update_enabled:
                            self._enable_update()
        else:
            self.table_name = ''
            
            if self.fetch_enabled:
                self._disable_fetch()
                
            if self.update_enabled:
                self._disable_update()
                
                
    def on_permit_change(self, *args):
        permit = self.gui.permit.get().strip()
        
        if permit:
            if permit != self.permit:
                self.permit = permit
                
                if self.table_name and self.sub:
                    if not self.fetch_enabled:
                        self._enable_fetch()
                        
                    if self.new:
                        if not self.update_enabled:
                            self._enable_fetch()
                
        else:
            self.permit = ''
            
            if self.fetch_enabled:
                self._disable_fetch()
                
            if self.update_enabled:
                self._disable_update()
    
    
    def on_sub_change(self, *args):
        sub = self.gui.sub.get().strip()
        
        if sub:
            if sub != self.sub:
                self.sub = sub
                
                if self.table_name and self.permit:
                    if not self.fetch_enabled:
                        self._enable_fetch()
                        
                    if self.new:
                        if not self.update_enabled:
                            self._enable_update()
                
        else:
            sub = 0
            
            if self.fetch_enabled:
                self._disable_fetch()
                
            if self.update_enabled:
                self._disable_update()
                
                
    def on_new_change(self, *args):
        new = self.gui.new.get()
        
        if new:
            if new != self.new:
                self.new = new
                
                if self.table_name and self.permit and self.sub:
                    if not self.update_enabled:
                        self._enable_update()
        
        else:
            self.new = 0
            
            if self.update_enabled:
                self._disable_update()
            
            
    def _enable_fetch(self):
        self.gui.enable_fetch_button()
        self.fetch_enabled = True
        
        
    def _disable_fetch(self):
        self.gui.disable_fetch_button()
        self.fetch_enabled = False
        
        
    def _enable_update(self):
        self.gui.enable_update_button()
        self.update_enabled = True
        
        
    def _disable_update(self):
        self.gui.disable_update_button()
        self.update_enabled = False
                

    def on_fetch_click(self):
        thread = threading.Thread(target=self._fetch)
        
        thread.daemon = True                           
        thread.start()
        

    def _fetch(self):
        loading_circle = progress.LoadingCircle(self.gui, text='Fetching')
        loading_circle.start()
        
        column = self._period_column()
        
        query = f'''
            SELECT {column}
            FROM {self.table_name}
            WHERE {constants.ID_COLUMN_NAME} LIKE "{self.permit}-{self.sub}%"
            '''
        
        results = utilities.execute_sql(sql_code=query, db_name=self.db_name)
        
        if results:
            value = '{:,}'.format(results[0])
            
        else:
            value = ''
            
        self.gui.current.set(value)
            
        loading_circle.end()
        
        
    def _period_column(self):
        period = self.gui.period.get()
        
        column = f'{constants.QUARTER_COLUMN_PREFIX}{period.lower()}'
        
        return column
        
        
    def on_update_click(self):
        new = self.gui.new.get().strip()
        
        if new:
            new = int(new)
            
            thread = threading.Thread(target=self._update, args=(new, ))
            
            thread.daemon = True
            thread.start()
        
        
    def _update(self, new):
        loading_circle = progress.LoadingCircle(self.gui, text='Updating')
        loading_circle.start()
        
        column = self._period_column()
        
        sql_code = f'''
            UPDATE {self.table_name} 
            SET {column}=?
            WHERE {constants.ID_COLUMN_NAME} LIKE "{self.permit}-{self.sub}%"
            '''
        
        updated = utilities.execute_sql(
            sql_code=sql_code, args=(new, ), db_name=self.db_name, dml=True
            )
        
        if updated:
            message = f'{self.permit}-{self.sub} updated.'
            
            self._set_messge_label(message)
        
        loading_circle.end()
        
        
    def _set_messge_label(self, message):
        self.gui.message_label.config(text=message)
        
        
class View(tk.Toplevel):
    '''
    '''
    
    
    ENTRY_WIDTH = 25
    LEFT_LABEL_WIDTH = 7
    RIGHT_LABLE_WIDTH = 5
    WINDOW_HEIGHT = 220
    WINDOW_WIDTH = 400
    
    
    def __init__(self, controller, title):
        super().__init__()
        self.controller = controller
        
        # sets the window title
        self.title(title)
        
        self.basis = tk.StringVar(value=self.controller.default_basis)
        self.current = tk.StringVar()
        self.new = tk.StringVar()
        self.period = tk.StringVar(value=self.controller.selected_period)
        self.permit = tk.StringVar()
        self.sub = tk.StringVar()
        self.table = tk.StringVar()
        
        self.basis.trace('w', self.controller.on_basis_change)
        self.new.trace('w', self.controller.on_new_change)
        self.permit.trace('w', self.controller.on_permit_change)
        self.sub.trace('w', self.controller.on_sub_change)
        self.table.trace('w', self.controller.on_table_change)
        
        self._center_window()
        self._make_widgets()
        
        
    def _center_window(self):
        x_offset = (self.winfo_screenwidth() - self.WINDOW_WIDTH) // 2
        y_offset = (self.winfo_screenheight() - self.WINDOW_HEIGHT) // 2
        
        self.geometry(
            f'{self.WINDOW_WIDTH}x{self.WINDOW_HEIGHT}+{x_offset}+{y_offset}'
            )
        
        
    def _make_widgets(self):
        frm_one = ttk.Frame(self)
        frm_two = ttk.Frame(self)
        period_frm = ttk.Frame(self)
        frm_three = ttk.Frame(self)
        frm_four = ttk.Frame(self)
        frm_five = ttk.Frame(self)
        
        table_frm = ttk.Frame(frm_one)
        basis_frm = ttk.Frame(frm_one)
        permit_frm = ttk.Frame(frm_two)
        sub_frm = ttk.Frame(frm_two)
        current_frm = ttk.Frame(frm_three)
        new_frm = ttk.Frame(frm_four)
        
        table_lbl = ttk.Label(
            table_frm, text='Table:', width=self.LEFT_LABEL_WIDTH
            )
        
        table_cbo = ComboboxAutoComplete(
            table_frm, textvariable=self.table, 
            value_list=self.controller.table_names, width=5
            )
        
        basis_lbl = ttk.Label(
            basis_frm, text='Basis:', width=self.RIGHT_LABLE_WIDTH
            )
        
        basis_cbo = ttk.Combobox(
            basis_frm, textvariable=self.basis, state='readonly',
            values=self.controller.basis_options, width=10
            )
        
        permit_lbl = ttk.Label(
            permit_frm, text='Permit:', width=self.LEFT_LABEL_WIDTH
            )
        
        permit_ent = ttk.Entry(permit_frm, textvariable=self.permit)
        
        sub_lbl = ttk.Label(
            sub_frm, text='Sub:', width=self.LEFT_LABEL_WIDTH
            )
        
        sub_ent = ttk.Entry(
            sub_frm, textvariable=self.sub, width=self.ENTRY_WIDTH
            )
        
        horizontal_separator = ttk.Separator(self)
        
        period_lbl = ttk.Label(
            period_frm, text='Period:', width=self.LEFT_LABEL_WIDTH
            )
        
        period_cbo = ttk.Combobox(
            period_frm, justify='right', textvariable=self.period, 
            state='readonly', values=self.controller.period_options, width=7
            )
        
        current_lbl = ttk.Label(
            current_frm, text='Current:', width=self.LEFT_LABEL_WIDTH
            )
        
        current_ent = ttk.Entry(
            current_frm, textvariable=self.current, width=self.ENTRY_WIDTH
            )
        
        new_lbl = ttk.Label(new_frm, text='New:', width=self.LEFT_LABEL_WIDTH)
        
        new_ent = ttk.Entry(
            new_frm, textvariable=self.new, width=self.ENTRY_WIDTH
            )
        
        self.fetch_btn = ttk.Button(
            frm_three, text='Fetch', command=self.controller.on_fetch_click
            )
        
        self.update_btn = ttk.Button(
            frm_four, text='Update', command=self.controller.on_update_click
            )
        
        self.message_label = ttk.Label(frm_five)
        cancel_btn = ttk.Button(frm_five, text='Cancel', command=self.destroy)
    
        frm_one.pack(fill='x', pady=constants.OUT_PAD)
        frm_two.pack(fill='x')
        
        horizontal_separator.pack(
            fill='x', padx=constants.OUT_PAD, pady=constants.OUT_PAD
            )
        
        period_frm.pack(anchor='w', padx=constants.OUT_PAD)
        frm_three.pack(fill='x', pady=constants.OUT_PAD)
        frm_four.pack(fill='x')
        frm_five.pack(fill='x', padx=constants.OUT_PAD, pady=constants.OUT_PAD)
        
        table_frm.pack(side='left', padx=constants.OUT_PAD)
        basis_frm.pack(padx=constants.OUT_PAD)
        
        permit_frm.pack(side='left', padx=constants.OUT_PAD)
        sub_frm.pack(padx=constants.OUT_PAD)
        
        current_frm.pack(side='left', padx=constants.OUT_PAD)
        new_frm.pack(side='left', padx=constants.OUT_PAD)
        
        table_lbl.pack(side='left')
        table_cbo.pack()
        
        basis_lbl.pack(side='left')
        basis_cbo.pack()
        
        period_lbl.pack(side='left')
        period_cbo.pack()
        
        permit_lbl.pack(side='left')
        permit_ent.pack()
        
        sub_lbl.pack(side='left')
        sub_ent.pack()
        
        current_lbl.pack(side='left')
        current_ent.pack()
        
        new_lbl.pack(side='left')
        new_ent.pack(anchor='e')
        
        self.fetch_btn.pack(anchor='w')
        self.update_btn.pack(anchor='w')
        
        self.message_label.pack(side='left')
        cancel_btn.pack(anchor='e')
        
        
    def disable_fetch_button(self):
        self.fetch_btn.config(state='disabled')
        
        
    def enable_fetch_button(self):
        self.fetch_btn.config(state='enabled')
        
        
    def disable_update_button(self):
        self.update_btn.config(state='disabled')
        
    def enable_update_button(self):
        self.update_btn.config(state='enabled')
        
        
        
        
