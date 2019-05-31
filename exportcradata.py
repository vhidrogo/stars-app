'''
Created on May 31, 2019

@author: vahidrogo
'''

import pandas as pd
import threading
import tkinter as tk
from tkinter import messagebox as msg
from tkinter import ttk
import traceback

import constants
from progress import LoadingCircle
from sqlquery import SqlQuery
import utilities


class Model(threading.Thread):
    '''
    '''
    
    
    amount_column = 'Amount'
    period_column = 'CashQtr_PeriodName'
    period_key_column = 'Quarter_Key'
    state_column = 'StateAbbr'
    tac_column = 'StateTaxCode'
    
    fetch_columns = [
        tac_column,
        'JurisdictionName',
        'JurisdictionNameCnty',
        'Permits',
        period_column,
        amount_column,
        ]
    
    table = 'stars.CountyCashFullwCnt_Py_R'
    
 
    def __init__(self, output_path, period, view, title):
        super().__init__()
        
        self.output_path = output_path
        self.view = view
        self.title = title
        
        self.query = f'''
            SELECT {','.join(self.fetch_columns)}
            
            FROM {self.table}
            
            WHERE {self.state_column} = ?
                AND {self.period_key_column} <= ?
            '''
        
        self.query_args = ('CA', int(f'{period[:4]}0{period[-1]}'))
        
        self.df = None
        
        
    def run(self):
        loading_circle = LoadingCircle(self.view, 'Exporting')
        loading_circle.start()
        
        try:
            sql_query = SqlQuery()
            
            self.df = sql_query.query_to_pandas_df(self.query, self.query_args)
            
            if self.df is not None:
                self._set_df()
                
                utilities.Output.output(
                    self.df, self.output_path, list(self.df)
                    )
        except:
            msg.showerror(
                self.title, 
                'Unhandled exception occurred:\n\n'
                f'{traceback.format_exc()}',
                parent=self.view
                )
        
        finally:
            sql_query.close()
            loading_circle.end()
            
            
    def _set_df(self):
        periods = set(self.df[self.period_column].values.tolist())
        periods = {period: 0 for period in sorted(periods)}
        
        transposed = {}
        
        for row in self.df.itertuples(index=False):
            tac = getattr(row, self.tac_column)
             
            if tac not in transposed:
                transposed[tac] = {
                    'permit_data': row[:4], 
                    'amounts': dict(periods)
                }
                 
            period = getattr(row, self.period_column)
            amount = int(getattr(row, self.amount_column))
            
            transposed[tac]['amounts'][period] += amount
            
        transposed = [
            x['permit_data'] + tuple(x['amounts'].values())
            for x in transposed.values()
            ]
            
        columns = list(self.df)[:4] + list(periods)
        
        self.df = pd.DataFrame(
            transposed, columns=columns
            )
    
    
class View(tk.Toplevel):
    '''
    '''
    
    LABEL_WIDTH = 12
    WINDOW_HEIGHT = 80
    WINDOW_WIDTH = 500
    
    
    def __init__(self, controller, output_path):
        super().__init__()
        
        self.controller = controller
        
        self.output_path_var = tk.StringVar(value=output_path)
        self.period_var = tk.StringVar(value=self.controller.period)
        
        self._center_window()
        self._make_widgets()
    
    
    def _center_window(self):
        x_offset = (self.winfo_screenwidth() - self.WINDOW_WIDTH) // 2
        y_offset = (self.winfo_screenheight() - self.WINDOW_HEIGHT) // 2
        
        self.geometry(
            f'{self.WINDOW_WIDTH}x{self.WINDOW_HEIGHT}+{x_offset}+{y_offset}'
            )
    
    
    def _make_widgets(self):
        path_frm = ttk.Frame(self)
        
        path_lbl = ttk.Label(
            path_frm, text='Output Path:', width=self.LABEL_WIDTH
            )
        
        path_ent = ttk.Entry(path_frm, textvariable=self.output_path_var)
        
        bottom_frm = ttk.Frame(self)
        
        period_frm = ttk.Frame(bottom_frm)
        
        period_lbl = ttk.Label(
            period_frm, text='Period:', width=self.LABEL_WIDTH
            )
        
        period_cbo = ttk.Combobox(
            period_frm, textvariable=self.period_var, 
            values=self.controller.period_options, width=7
            )
        
        period_cbo.bind(
            '<<ComboboxSelected>>', self.controller.on_period_select
            )
        
        btn = ttk.Button(
            bottom_frm, text='Export', command=self.controller.on_export_click
            )
        
        path_frm.pack(
            anchor='w', fill='x', padx=constants.OUT_PAD, pady=constants.OUT_PAD
            )
        path_lbl.pack(side='left')
        path_ent.pack(fill='x')
        
        bottom_frm.pack(fill='x', padx=constants.OUT_PAD)
        
        period_frm.pack(anchor='w', side='left')
        period_lbl.pack(side='left')
        period_cbo.pack()
        
        btn.pack(anchor='e')
    
    
class Controller:
    '''
    '''
    
    
    default_output_name = 'countywide_cash_receipts'
    
    output_type = 'csv'
    
    title = f'{constants.APP_NAME} Export CRA Data'
    

    def __init__(self, period_options, period):
        self.period_options = period_options
        self.period = period
        
        output_path = (
            f'N:/{self.period.replace("Q", " Q")}/'
            f'{self.period}_{self.default_output_name}.{self.output_type}'
            )
        
        self.view = View(self, output_path)
        
        
    def on_period_select(self, event):
        period = self.view.period_var.get()
        
        if period != self.period:
            year = self.period[:4]
            quarter = self.period[-2:]
            
            self.period = period
            
            new_year = self.period[:4]
            new_quarter = self.period[-2:]
            
            path = self.view.output_path_var.get()
            
            new_path = path.replace(year, new_year)
            new_path = new_path.replace(quarter, new_quarter)
            
            self.view.output_path_var.set(new_path)
        
        
    def on_export_click(self):
        output_path = self.view.output_path_var.get()
        
        if output_path:
            output_type = output_path.rsplit('.', 1)[1]
            
            if output_type.lower() == self.output_type:
                model = Model(output_path, self.period, self.view, self.title)
                model.start()
            
            else:
                msg.showinfo(
                    self.title, f'Output type must be: {self.output_type}',
                    parent=self.view
                    )
        else:
            msg.showinfo(self.title, 'Output path required!', parent=self.view)
