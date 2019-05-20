'''
Created on Mar 29, 2019

@author: vahidrogo
'''

from contextlib import suppress
import datetime
import getpass
import numpy as np
from operator import itemgetter
import re
import sqlite3 as sql
import threading
import tkinter as tk
from tkinter import messagebox as msg
from tkinter import ttk
from _tkinter import TclError
from TkinterDnD2 import TkinterDnD
import traceback

from adjustments import BusinessLevelAdjustments
from businessdetailtotals import BusinessDetailTotals
import businesslookup
from cashanomalies import CashAnomalies
from cashreceiptsanalysis import CashReceiptsAnalysis
from ccomp import Ccomp
import cdtfaallocations
from comboboxautocomplete import ComboboxAutoComplete
import comparefiles
import constants
from countypool import CountyPool
import database
from downloadbusinessdetail import DownloadBusinessDetail
from dropfile import DropDetail
from dropfile import DropDetailJoin
from econtotals import EconTotals
from exportbusinessdetail import ExportBusinessDetail
import loadbusinesscodetotals
import loadgeoranges
from packet import CompilePacket
import parseaddresses
from priorperiodpayments import PriorPeriodPayments
from progress import Progress
import rolluptotals
from showjurisdictioninformation import ShowJurisdictionInformation
from stcl import Stcl
from summary import Summary
from rundictionary import RunDictionary
from updatebusinesscodetotals import UpdateBusinessCodeTotals
from selections import Selections
from tooltip import ToolTip
import updatepayment
import utilities
import verifypermit


class Model(threading.Thread):
    '''
    '''
    
    
    def __init__(self, controller, selections):
        super().__init__()
        
        self.controller = controller
        self.selections = selections
        
        self.progress = Progress(self, self.selections.title)
        
        self.abort = False
        
        
    def run(self):
        process = self.selections.process_name
        jurisdictions = self.selections.jurisdiction_list
        
        for i, jurisdiction in enumerate(jurisdictions, start=1):
            if self.controller.end_processes or self.abort:
                break
            
            else:
                self.counter = i
                
                try:
                    if process == 'Business Detail Totals':
                        business_detail_totals = BusinessDetailTotals(
                            self, self.selections
                            )
                        business_detail_totals.main(jurisdiction)
                        
                    elif process == 'Business Level Adjustments (AFBC)':
                        business_adjustments = BusinessLevelAdjustments(
                            self, self.selections
                            )
                        business_adjustments.main(jurisdiction)
                    
                    elif process == 'Cash Receipts Analysis (CRA)':
                        cra = CashReceiptsAnalysis(self, self.selections)
                        cra.main(jurisdiction)
                        
                    elif process == 'Compile Packet':
                        compile_packet = CompilePacket(self)
                        compile_packet.main(jurisdiction)
                    
                    elif process == 'County Pool Analysis':
                        county_pool = CountyPool(self)
                        county_pool.main(jurisdiction)
                    
                    elif process == 'Export Business Detail (QC/QE)':
                        export_detail = ExportBusinessDetail(self)
                        export_detail.main(jurisdiction)
                    
                    elif process == 'Load Business Detail':
                        download_detail = DownloadBusinessDetail(
                            self, self.selections
                            )
                        download_detail.main(jurisdiction)
                    
                    elif process == 'Prior Period Payments (PYBG)':
                        prior_period_payments = PriorPeriodPayments(self)
                        prior_period_payments.main(jurisdiction)
                    
                    elif process == 'Regional Comparison (CCOMP)':
                        ccomp = Ccomp(self)
                        ccomp.main(jurisdiction)
                    
                    elif process == 'Run Dictionary':
                        run_dictionary = RunDictionary(self)
                        run_dictionary.main(
                            jurisdiction, self.selections.type_option
                            )
                    elif process == 'Sales Tax Capture & Leakage Analysis (STCL)':
                        stcl = Stcl(self)
                        stcl.main(jurisdiction)
                    
                    elif process == 'Show Jurisdiction Information':
                        show_info = ShowJurisdictionInformation()
                        show_info.main(jurisdiction)
                        
                    elif process == 'Summarized Cash Anomalies':
                        cash_anomalies = CashAnomalies(self, self.selections)
                        cash_anomalies.main(jurisdiction)
                    
                    elif process == 'Summary':
                        summary = Summary(self)
                        summary.main(jurisdiction)
                    
                    elif process == 'Update Business Code Totals':
                        update_bc_totals = UpdateBusinessCodeTotals(self)
                        update_bc_totals.main(jurisdiction)
                
                except Exception:
                    msg.showerror(
                        self.selections.process_name, 
                        'Unhandled exception occurred:\n\n'
                        f'{traceback.format_exc()}'
                        )
                finally:
                    # if its the last jurisdiction
                    if i == self.selections.jurisdiction_count:
                        self.progress.destroy()
            

    def update_progress(self, progress, message):
        self.progress.update_progress(
            progress, message, self.counter, self.selections.jurisdiction_count
            )


class View(TkinterDnD.Tk):
    '''
    '''
    
    
    WINDOW_HEIGHT = 700
    WINDOW_WIDTH = 800
    
    juri_columns = ['ID', 'TAC', 'NAME']
    
    
    def __init__(self, controller):
        super().__init__()
        
        self.controller = controller
        
        self.option_cbos = {}
        self.option_widgets = {}
        
        self.fifo_chk_state = tk.IntVar()
        
        self.ascending_chk_state = tk.IntVar()
        self.estimates_chk_state = tk.IntVar()
        self.exclude_files_chk_state = tk.IntVar()
        self.geos_chk_state = tk.IntVar()
        self.open_chk_state = tk.IntVar()
        self.pdf_only_chk_state = tk.IntVar()
        
        self.juri_prg_var = tk.DoubleVar()
        
        self.process_name = tk.StringVar()
        self.process_name.trace('w', self.controller.on_process_change)
        
        self.protocol('WM_DELETE_WINDOW', self.controller.exit)
        
        self.title(constants.APP_NAME)
        
        self.option_frm_one_widgets = [
            'Ascending', 'Count', 'Estimates', 'Exclude Files', 'Geos', 
            'Order', 'PDF Only', 'type'
            ]
        
        self.option_frm_two_widgets = [
            'Basis', 'Interval', 'Open', 'Output'
            ]
        
        self._center_window()
        
        self._make_frames()
        self._make_widgets()
        
        self.option_cbos['Basis'] = self.basis_cbo
        self.option_cbos['Count'] = self.count_cbo
        self.option_cbos['Interval'] = self.interval_cbo
        self.option_cbos['Order'] = self.order_cbo
        self.option_cbos['Output'] = self.output_cbo
        self.option_cbos['type'] = self.type_cbo
        
        self.option_widgets['Ascending'] = self.ascending_chk
        self.option_widgets['Estimates'] = self.estimates_chk
        self.option_widgets['Exclude Files'] = self.exclude_files_chk
        self.option_widgets['Geos'] = self.geos_chk
        self.option_widgets['Open'] = self.open_chk
        self.option_widgets['PDF Only'] = self.pdf_only_chk
        self.option_widgets['Basis'] = self.basis_frm
        self.option_widgets['Count'] = self.count_frm
        self.option_widgets['Interval'] = self.interval_frm
        self.option_widgets['Order'] = self.order_frm
        self.option_widgets['Output'] = self.output_frm
        self.option_widgets['type'] = self.type_frm
        
        self._configure_option_cbos()
        
        self._make_tooltips()
        
        self._pack_frames()
        self._pack_widgets()
        
        self.focus()
        
        
    def _center_window(self):
        x_offset = (self.winfo_screenwidth() - int(self.WINDOW_WIDTH )) // 2
        y_offset = (self.winfo_screenheight() - int(self.WINDOW_HEIGHT)) // 2
        
        self.geometry(
            f'{self.WINDOW_WIDTH}x{self.WINDOW_HEIGHT}+{x_offset}+{y_offset}'
            )
      
        
    def _make_frames(self):
        self.controller_frm = ttk.Frame()
        
        self.controller_top_frm = ttk.Frame(self.controller_frm)
        self.controller_bot_frm = ttk.Frame(self.controller_frm)
        
        self.top_left_frm = ttk.Frame(self.controller_top_frm)
        self.top_right_frm = ttk.Frame(self.controller_top_frm)
        
        self.bot_left_frm = ttk.Frame(self.controller_bot_frm)
        self.bot_right_frm = ttk.Frame(self.controller_bot_frm)
        
        self.juri_frm = ttk.Frame(self.top_left_frm)
        self.sel_btn_frm = ttk.Frame(self.top_left_frm)
        
        self.fifo_period_frm = ttk.Frame(self.top_right_frm)
        self.queue_lst_frm = ttk.Frame(self.top_right_frm)
        
        self.fifo_frm = ttk.Frame(self.fifo_period_frm)
        self.period_frm = ttk.Frame(self.fifo_period_frm)
        
        self.src_frm = ttk.Frame(self.juri_frm)
        self.juri_lst_frm = ttk.Frame(self.juri_frm)
        
        self.process_frm = ttk.Frame(self.bot_left_frm)
        self.options_frm = ttk.Labelframe(self.bot_left_frm, text='Options')
        
        self.options_frm_one = ttk.Frame(self.options_frm)
        self.options_frm_two = ttk.Frame(self.options_frm)
        
        self.basis_frm = ttk.Frame(self.options_frm_two)
        self.count_frm = ttk.Frame(self.options_frm_one)
        self.interval_frm = ttk.Frame(self.options_frm_two)
        self.order_frm = ttk.Frame(self.options_frm_one)
        self.output_frm = ttk.Frame(self.options_frm_two)
        self.type_frm = ttk.Frame(self.options_frm_one)
        

    def _make_widgets(self):
        move_btn_w = 5
        self.src_lbl = ttk.Label(self.src_frm, text='Search:')
        
        self.search_entry = tk.Entry(self.src_frm)
        
        self.search_entry.bind('<Key>', self.controller.on_search_key_press)
        self.search_entry.bind('<Return>', self.controller.on_search_return)
        
        self.juri_vsb = ttk.Scrollbar(self.juri_lst_frm)
        
        self.juri_tree = ttk.Treeview(
            self.juri_lst_frm, columns=self.juri_columns, show='headings',
            yscrollcommand=self.juri_vsb.set, takefocus=False
            )
        
        self.juri_vsb.config(command=self.juri_tree.yview)
        
        # sets the headers that will be displayed in the columns
        self.juri_tree.heading(
            self.juri_columns[0], text=self.juri_columns[0])
        self.juri_tree.heading(
            self.juri_columns[1], text=self.juri_columns[1])
        self.juri_tree.heading(
            self.juri_columns[-1], text=self.juri_columns[-1])
        
        self.juri_tree.column('#1', width=30)
        self.juri_tree.column('#2', width=35)
        
        self.juri_tree.bind('<Return>', self.controller.on_juri_tree_return)
        
        self.juri_tree.bind(
            '<Button-1>', self.controller.on_available_tree_view_click
            )
        
        self.juri_tree.bind(
            '<Double-Button-1>', self.controller.on_juri_tree_double_click
            )
        
        self.move_all_right_btn = ttk.Button(
            self.sel_btn_frm, text='>>', width=move_btn_w,
            command=self.controller.move_all_right, takefocus=False
            )
        
        self.move_right_btn = ttk.Button(
            self.sel_btn_frm, text='>', width=move_btn_w,
            command=self.controller.move_right, takefocus=False
            )
        
        self.move_left_btn = ttk.Button(
            self.sel_btn_frm, text='<', width=move_btn_w,
            command=self.controller.move_left, takefocus=False
            )
        
        self.move_all_left_btn = ttk.Button(
            self.sel_btn_frm, text='<<', width=move_btn_w,
            command=self.controller.move_all_left, takefocus=False
            )
         
        self.fifo_chk = ttk.Checkbutton(
            self.fifo_frm, text='FIFO', var=self.fifo_chk_state, 
            takefocus=False
            )
        
        self.period_lbl = ttk.Label(
            self.period_frm,  text='Period:', anchor='e', justify='right'
            )
        
        self.period_cbo = ttk.Combobox(
            self.period_frm, justify='right', state='readonly', 
            takefocus=False, width=8
            )
        
        self.queue_vsb = ttk.Scrollbar(self.queue_lst_frm)
           
        self.queue_tree = ttk.Treeview(
            self.queue_lst_frm, columns=self.juri_columns, show='headings',
            yscrollcommand=self.queue_vsb.set, takefocus=False
            )
        
        self.queue_vsb.config(command=self.queue_tree.yview)
        
        # sets the headers that will be displayed in the columns
        self.queue_tree.heading(
            self.juri_columns[0], text=self.juri_columns[0])
        self.queue_tree.heading(
            self.juri_columns[1], text=self.juri_columns[1])
        self.queue_tree.heading(
            self.juri_columns[-1], text=self.juri_columns[-1])
        
        self.queue_tree.column('#1', width=30)
        self.queue_tree.column('#2', width=35)
        
        self.queue_tree.bind('<Return>', self.controller.on_queue_return)
        
        self.queue_tree.bind(
            '<Double-Button-1>', self.controller.on_sel_tree_double_click)
        
        self.process_lbl = ttk.Label(
            self.process_frm, text='Process:', anchor='e'
            )
        
        self.process_cbo = ComboboxAutoComplete(
            self.process_frm,  textvariable=self.process_name, width=40
            )
        
        self.ascending_chk = ttk.Checkbutton(
            self.options_frm_one, text='Ascending', 
            var=self.ascending_chk_state
            )
        
        self.estimates_chk = ttk.Checkbutton(
            self.options_frm_one, text='Estimates', var=self.estimates_chk_state
            )
        
        self.exclude_files_chk = ttk.Checkbutton(
            self.options_frm_one, text='Exclude Files', var=self.exclude_files_chk_state
            )
        
        self.geos_chk = ttk.Checkbutton(
            self.options_frm_one, text='Geos', var=self.geos_chk_state
            )
        
        self.open_chk = ttk.Checkbutton(
            self.options_frm_two, text='Open', var=self.open_chk_state
            )
        
        self.pdf_only_chk = ttk.Checkbutton(
            self.options_frm_one, text='PDF Only', var=self.pdf_only_chk_state
            )
        
        self.basis_lbl = ttk.Label(self.basis_frm, text='Basis:')
        self.basis_cbo = ttk.Combobox(self.basis_frm)
        
        self.count_lbl = ttk.Label(self.count_frm, text='Count:')
        self.count_cbo = ttk.Combobox(self.count_frm)
        
        self.interval_lbl = ttk.Label(self.interval_frm, text='Interval:')
        self.interval_cbo = ttk.Combobox(self.interval_frm)
        
        self.order_lbl = ttk.Label(self.order_frm, text='Order:')
        self.order_cbo = ttk.Combobox(self.order_frm)
        
        self.output_lbl = ttk.Label(self.output_frm, text='Output:')
        self.output_cbo = ttk.Combobox(self.output_frm)
        
        self.type_lbl = ttk.Label(self.type_frm, text='Type:')
        self.type_cbo = ttk.Combobox(self.type_frm)
        
        self.run_btn = ttk.Button(
            self.bot_right_frm, text='Run', state='disabled', 
            command=self.controller.on_run_click
            )
        
        self.exit_btn = ttk.Button(
            self.bot_right_frm, text='Exit', command=self.controller.exit
            )
        
        
    def _resize_cbo(self, cbo_name):
        cbo = self.option_cbos[cbo_name]
        cbo.config(width=len(cbo.get()) + 2)


    def _configure_option_cbos(self):
        for name, cbo in self.option_cbos.items():
            cbo.config(
                justify='center', postcommand=self._resize_cbo(name), 
                state='readonly'
                )
        
        
    def _make_tooltips(self):
        # creates a tooltip for the first in first out checkbox
        ToolTip(
            self.fifo_chk, 
            'Check this to process jurisdictions in the order they are '
            'selected.'
            )
        
        # creates a tooltip for the open checkbox
        ToolTip(
            self.open_chk,
            'Check this to automatically open any output file(s) created '
            'by this process.'
            )
        

    def _pack_frames(self):
        self.controller_frm.pack(
            fill='both', expand=1, padx=constants.OUT_PAD, 
            pady=constants.OUT_PAD
            )
        
        self.controller_top_frm.pack(fill='both', expand=1)
        self.controller_bot_frm.pack(fill='x')
        
        self.top_left_frm.pack(side='left', fill='both', expand=1)
        self.top_right_frm.pack(side='right', fill='both', expand=1)
        
        self.juri_frm.pack(side='left', fill='both', expand=1)
        self.sel_btn_frm.pack(side='right', padx=constants.IN_PAD)
        
        self.bot_left_frm.pack(side='left', fill='x', expand=1)
        self.bot_right_frm.pack(side='right', fill='y')
        
        self.src_frm.pack(fill='x')
        
        '''
            TODO move to _make_widgets, also move selected_label
        '''
        self.available_label = ttk.Label(self.juri_lst_frm, text='Available:')
        self.available_label.pack(anchor='w', side='top')
        
        self.juri_lst_frm.pack(fill='both', expand=1, pady=constants.OUT_PAD)
        
        self.fifo_period_frm.pack(fill='x')
        self.queue_lst_frm.pack(fill='both', expand=1, pady=constants.OUT_PAD)
        
        self.fifo_frm.pack(side='left')
        self.period_frm.pack(anchor='e')
        
        self.selected_label = ttk.Label(self.queue_lst_frm, text='Selected: 0')
        self.selected_label.pack(anchor='w')
        
        self.process_frm.pack(anchor='w')
        
        
    def _pack_widgets(self):
        self.src_lbl.pack(side='left')
        self.search_entry.pack(fill='x', expand=1)
        
        self.juri_tree.pack(fill='both',expand=1, side='left')
        self.juri_vsb.pack(fill='y', expand=1)
        
        self.move_all_right_btn.pack()
        self.move_right_btn.pack()
        self.move_left_btn.pack()
        self.move_all_left_btn.pack()
        
        self.fifo_chk.pack(side='left')
        
        self.period_lbl.pack(side='left')
        self.period_cbo.pack(anchor='e')
        
        self.queue_tree.pack(fill='both', expand=1, side='left')
        
        self.process_lbl.pack(side='left')
        self.process_cbo.pack(anchor='w')
        
        self.basis_lbl.pack(side='left')
        self.basis_cbo.pack()
        
        self.count_lbl.pack(side='left')
        self.count_cbo.pack()
        
        self.interval_lbl.pack(side='left')
        self.interval_cbo.pack()
        
        self.order_lbl.pack(side='left')
        self.order_cbo.pack()
        
        self.output_lbl.pack(side='left')
        self.output_cbo.pack()
        
        self.type_lbl.pack(side='left')
        self.type_cbo.pack()
        
        self.run_btn.pack(anchor='s', side='left', padx=constants.OUT_PAD)
        self.exit_btn.pack(anchor='s', side='right')
        
        
    def show_queue_scrollbar(self):
        self.queue_vsb.pack(fill='y', expand=1)
    
    
    def hide_queue_scrollbar(self):
        self.queue_vsb.pack_forget()
        
        
    def _show_options_frm(self):
        self.options_frm.pack(anchor='w')
        
        
    def _hide_options_frm(self):
        self.options_frm.pack_forget()
        
        
    def _show_options_frm_one(self):
        self.options_frm_one.pack(anchor='w', padx=constants.IN_PAD)
        
        
    def _hide_options_frm_one(self):
        self.options_frm_one.pack_forget()
        
        
    def _show_options_frm_two(self):
        self.options_frm_two.pack(anchor='w', padx=constants.IN_PAD)
        
        
    def _hide_options_frm_two(self):
        self.options_frm_two.pack_forget()
        
        
    def show_option_widgets(self, process_name):
        options = self.controller.processes[process_name]
        
        if options:
            self._show_options_frm()
            
            self._hide_options_frm_one()
            self._hide_options_frm_two()
            
            if any(
                option in self.option_frm_one_widgets 
                for option in options['primary_options']
                ):
                self._show_options_frm_one()
                
            if any(
                option in self.option_frm_two_widgets 
                for option in options['primary_options']
                ):
                self._show_options_frm_two()
            
            option_frm_one_pads = []
            option_frm_two_pads = []
            
            for option in options['primary_options']:
                if option == 'type':
                    if process_name == 'Business Detail Totals':
                        default_name = 'Totals Type'
                        
                    elif process_name == 'Compile Packet':
                        default_name = 'Packet Type'
                        
                    elif process_name == 'Run Dictionary':
                        default_name = 'Dictionary Type'
                        
                else:
                    default_name = option
                    
                default = self.controller.user_defaults[default_name]
                
                if option == 'Basis':
                    self.basis_cbo.set(default)
                    
                elif option == 'Count':
                    self.count_cbo.set(default)
                    
                elif option == 'Estimates':
                    self.estimates_chk_state.set(default)
                    
                elif option == 'Exclude Files':
                    self.exclude_files_chk_state.set(default)
                    
                elif option == 'Geos':
                    self.geos_chk_state.set(default)
                    
                elif option == 'Interval':
                    self.interval_cbo.set(default)
                    
                elif option == 'Open':
                    self.open_chk_state.set(default)
                    
                elif option == 'Order':
                    self.order_cbo.set(default)
                    
                elif option == 'Output':
                    self.output_cbo.set(default)
                    
                elif option == 'PDF Only':
                    self.pdf_only_chk_state.set(default)
                    
                elif option == 'type':
                    values = options['secondary_options']['type']
                    self.type_cbo.config(values=values) 
                    
                    self.type_cbo.set(default)
                
                if option in self.option_frm_one_widgets:
                    if not option_frm_one_pads:
                        padx = 0
                    else:
                        padx = 0 if option_frm_one_pads[-1] else constants.OUT_PAD
                        
                    option_frm_one_pads.append(padx)
                else:
                    if not option_frm_two_pads:
                        padx = 0
                    else:
                        padx = 0 if option_frm_two_pads[-1] else constants.OUT_PAD
                        
                    option_frm_two_pads.append(padx)
                
                self.option_widgets[option].pack(
                    padx=padx, pady=constants.IN_PAD, side='left'
                    )
                
                if option in self.option_cbos:
                    self._resize_cbo(option)

        else:
            self._hide_options_frm()
            
            
    def hide_option_widgets(self):
        for widget in self.option_widgets.values():
            widget.pack_forget()
        
        
    def enable_run_btn(self):
        self.run_btn.config(state='enabled')
        
        
    def disable_run_btn(self):
        self.run_btn.config(state='disabled')
        

class Menu(tk.Menu):
    '''
        This class is for the menu bar of the controller view window.
    '''
    
    
    def __init__(self, controller):
        super().__init__()
        
        self.controller = controller
        
        self._set_option_vars()
 
        self._create_file_menu()
        self._create_edit_menu()
        self._create_view_menu()
        self._create_data_menu()
        self._create_tools_menu()
        self._create_preferences_menu()
        self._create_help_menu()
        
        
    def _set_option_vars(self):
        self.option_vars = {}
        
        for name, options in self.controller.options.items():
            default = self.controller.user_defaults[name]
            
            index = (
                options.index(default) if isinstance(options, list) else default
                )
            
            self.option_vars[name] = tk.IntVar(value=index)
         
         
    def _create_file_menu(self):
        file_menu = tk.Menu(self, tearoff=False)
        
        self.add_cascade(label='File', menu=file_menu)
        
        file_menu.add_command(
            label='Refresh', command=self.controller.refresh, accelerator='Ctrl+r'
            )
        
        file_menu.add_command(
            label='Exit', command=self.controller.exit, accelerator='Ctrl+q'
            )
        
        
    def _create_edit_menu(self):
        edit_menu = tk.Menu(self, tearoff=False)
        
        self.add_cascade(label='Edit', menu=edit_menu)
        
        edit_menu.add_command(
            label='Database', accelerator='Ctrl+d',
            command=lambda:database.Controller(
                self.option_vars['DB Mode'].get()
                )
            )
        
        
    def _create_view_menu(self):
        view_menu = tk.Menu(self)
        
        view_menu.add_checkbutton(
            label='Show Add-ons', variable=self.controller.show_addons,
            command=self.controller.set_jurisdiction_list
            )
        
        view_menu.add_checkbutton(
            label='Show Jurisdictions', variable=self.controller.show_jurisdictions,
            command=self.controller.set_jurisdiction_list
            )
          
        view_menu.add_checkbutton(
            label='Show Non-Clients', variable=self.controller.show_non_clients,
            command=self.controller.set_jurisdiction_list
            )
              
        view_menu.add_checkbutton(
            label='Show Transits', variable=self.controller.show_transits,
            command=self.controller.set_jurisdiction_list
            )
         
        self.add_cascade(label='View', menu=view_menu)
        
        
    def _create_data_menu(self):
        data_menu = tk.Menu(self, tearoff=False)
        build_menu = tk.Menu(self)
        export_menu = tk.Menu(self, tearoff=False)
        load_menu = tk.Menu(self, tearoff=False)
        
        build_menu.add_command(
            label='Business Code Totals Region', 
            command=rolluptotals.BusinessCodeTotalsRegion
            )
        
        build_menu.add_command(
            label='Category Totals', command=rolluptotals.CategoryTotals
            )
          
        build_menu.add_command(
            label='Category Totals Add-on', 
            command=lambda:rolluptotals.CategoryTotals(is_addon=True)
            )
          
        build_menu.add_command(
            label='Category Totals Region', 
            command=rolluptotals.CategoryTotalsRegion
            )
        
        build_menu.add_command(
            label='Segment Totals', command=rolluptotals.SegmentTotals
            )
          
        build_menu.add_command(
            label='Segment Totals Add-on', 
            command=lambda:rolluptotals.SegmentTotals(is_addon=True)
            )
          
        build_menu.add_command(
            label='Segment Totals Region', 
            command=rolluptotals.SegmentTotalsRegion
            )
        
        export_menu.add_command(
            label='All Econ Totals', command=self._export_econ_totals
            )
          
        load_menu.add_command(
            label='Business Code Totals', 
            command=lambda:loadbusinesscodetotals.Controller(
                self.controller.get_period_options(), self.controller.get_period()
                )
            )
         
        load_menu.add_command(
            label='Business Detail', command=lambda:DropDetail(self.controller)
            )
         
        load_menu.add_command(
            label='Business Detail (Join)', 
            command=lambda:DropDetailJoin(self.controller)
            )
        
        load_menu.add_command(
            label='CDTFA Allocations', 
            command=lambda:cdtfaallocations.Controller(
                self.controller.get_period_options(), self.controller.get_period()
                )
            )
        
        load_menu.add_command(
            label='Geo Ranges', command=loadgeoranges.Controller
            )
        
        data_menu.add_cascade(label='Build', menu=build_menu)
        data_menu.add_cascade(label='Export', menu=export_menu)
        data_menu.add_cascade(label='Load', menu=load_menu)
        
        self.add_cascade(label='Data', menu=data_menu)
        
        
    def _export_econ_totals(self):
        window = self.controller.get_view()
        period = self.controller.get_period()
        
        econ_totals = EconTotals(window, period)
        econ_totals.start()
            

    def _create_tools_menu(self):
        tools_menu = tk.Menu(self, tearoff=False)
        
        self.add_cascade(label='Tools', underline=0, menu=tools_menu)
        
        tools_menu.add_command(
            label='Business Lookup', 
            command=lambda:businesslookup.Controller(
                self.controller.get_period_options(), self.controller.get_period()
                )
            )
        
        tools_menu.add_command(
            label='Compare Files', command=comparefiles.Controller
            )
        
        tools_menu.add_command(
            label='Parse Addresses', command=parseaddresses.Controller
            )
        
        tools_menu.add_command(
            label='Update Payment', 
            command=lambda:updatepayment.Controller(
                self.controller.get_period_options(), self.controller.get_period()
                )
            )
        
        tools_menu.add_command(
            label='Verify Permit (CDTFA)', accelerator='Ctrl+shift+v', 
            command=verifypermit.Controller
            )
        
        
    def _create_preferences_menu(self):
        preferences_menu = tk.Menu(self, tearoff=False)
        defaults_menu = tk.Menu(self, tearoff=False)
        
        for name, options in self.controller.options.items():
            menu = tk.Menu(self, tearoff=False)
               
            variable = self.option_vars[name]
               
            if isinstance(options, dict):
                for i, option in options.items():
                    menu.add_radiobutton(
                        label=option, value=i, variable=variable,
                        command=(
                            lambda default_name=name, default=i:
                                utilities.set_default(
                                    default_name, self.controller.user_id, 
                                    default
                                    )
                                )
                        )
              
            else:
                for i, option in enumerate(options):
                    menu.add_radiobutton(
                        label=option, value=i, variable=variable,
                        command=(
                            lambda default_name=name, default=option: 
                                utilities.set_default(
                                    default_name, self.controller.user_id, default
                                    )
                                )
                        )
                       
            defaults_menu.add_cascade(label=name, menu=menu)
            
        preferences_menu.add_cascade(label='Defaults', menu=defaults_menu)
        self.add_cascade(label='Preferences', menu=preferences_menu)
    

    def _create_help_menu(self):
        help_menu = tk.Menu(self, tearoff=False)
        
        self.add_cascade(label='Help', underline=0, menu=help_menu)
        
        help_menu.add_command(
            label='Main Window',
            command=lambda:utilities.open_file(
                constants.HELP_PATH.joinpath('Main_Window_Help.txt')
                )
            )
        
        help_menu.add_command(
            label='Database',
            command=lambda:utilities.open_file(
                constants.HELP_PATH.joinpath('Database_Help.txt')
                )
            )
        
        
class Controller:
    '''
        Controls the behavior of the Mainview() user interface class.
    '''
    
    
    processes = {
        'Business Detail Totals': {
            'primary_options': [
                'type', 'Count', 'Order', 'Ascending', 
                'Open', 'Output', 'Basis', 'Interval',
                ]
            },
        
        'Business Level Adjustments (AFBC)': {'primary_options': ['Open']},
        
        'Cash Receipts Analysis (CRA)': {'primary_options': ['Open']},
        
        'Compile Packet': {
            'primary_options': ['Exclude Files', 'Open', 'PDF Only', 'type']
            },
        
        'County Pool Analysis': {'primary_options': ['Open']},
        
        'Export Business Detail (QC/QE)': {
            'primary_options': [
                'Estimates', 'Geos', 'Open','Basis', 'Interval', 'Output'
                ]
            },
        
        'Load Business Detail': {'primary_options': ['Basis']},
        
        'Prior Period Payments (PYBG)': {'primary_options': ['Open']},
        
        'Regional Comparison (CCOMP)': {'primary_options': ['Open']},
        
        'Run Dictionary': {'primary_options': ['type']},
        
        'Sales Tax Capture & Leakage Analysis (STCL)': {
            'primary_options': ['Open']
            },
        
        'Show Jurisdiction Information': {},
        
        'Summarized Cash Anomalies': {'primary_options': ['Open', 'Output']},
        
        'Summary': {'primary_options': ['Open']},
        
        'Update Business Code Totals': {}
        }
    
    process_names = list(processes.keys())
    
    chk_options = {1: 'True', 0: 'False'}

    options = {
        'Ascending': chk_options, 
        'Basis': ['Cash', 'Econ'],
        'Count': ['All'] + [i for i in range(1, constants.MAX_PERIOD_COUNT + 1)],
        'DB Mode': constants.DB_MODES,
        'Dictionary Type': ['Name', 'Permit'],
        'Estimates': chk_options,
        'Exclude Files': chk_options,
        'Geos': chk_options,
        'Interval': ['Quarter', 'Year'],
        'Open': chk_options,
        'Order': ['$ Change', '% Change', 'Name', 'Quarter', 'Year', 'None'],
        'Output': ['CSV', 'XLSX'],
        'PDF Only': chk_options,
        'Packet Type': [
            'Client by Rep', 'Client Standard', 'Custom by Rep', 
            'Custom Standard', 'Liaison by Rep', 'Liaison Standard'
            ],
        'Process': process_names,
        'Totals Type': ['Category', 'Segment']
        }
    
    processes['Business Detail Totals']['secondary_options'] = {
        'type': options['Totals Type']
        }
    
    processes['Compile Packet']['secondary_options'] = {
        'type': options['Packet Type'] 
    }
    
    processes['Run Dictionary']['secondary_options'] = {
        'type': options['Dictionary Type']
        }
    
    defaults = {
        'Ascending': 0, 
        'Basis': 'Econ',
        'Count': 'All',
        'DB Mode': 1,
        'Dictionary Type': 'Name',
        'Estimates': 1,
        'Exclude Files': 1,
        'Geos': 0,
        'Interval': 'Quarter',
        'Open': 1,
        'Order': '$ Change',
        'Output': 'XLSX',
        'PDF Only': 0,
        'Packet Type': 'Client Standard',
        'Process': 'Export Business Detail (QC/QE)',
        'Totals Type': 'Segment'
        }
    
    jurisdicitions_query = f'''
        SELECT Id, {constants.TAC_COLUMN_NAME}, name, IsClient
        FROM {constants.JURISDICTIONS_TABLE}
        '''
    
    addons_query = f'''
        SELECT a.Id, a.{constants.TAC_COLUMN_NAME}, a.name, j.IsClient
        FROM {constants.ADDONS_TABLE} a, {constants.JURISDICTIONS_TABLE} j
        WHERE a.JurisdictionId=j.id
        '''
    
    transits_query = f'''
        SELECT Id, {constants.TAC_COLUMN_NAME}, name, IsClient
        FROM {constants.TRANSITS_TABLE}
        '''
    
    # the minimum count of jurisdictions selected to show the scroll bar
    # on the queue tree
    COUNT_FOR_QUEUE_SCROLL = 30 
    
    PERIOD_YEARS = 20
    
    
    def __init__(self):
        # required for sqlite3 to support int larger than 8 bit
        sql.register_adapter(np.int64, lambda val: int(val))
        sql.register_adapter(np.int32, lambda val: int(val))
        
        self.process_name = ''
        
        self.end_processes = False
        self.processed_selected = True
        self.queue_scroll = False
        self.run_enabled = False
        
        self.juri_search_pattern = re.compile(r'(\w|\d)')
        
        self.period_options = []
        
        self.user_defaults = {}
        
        self.selected_jurisdiction_count = 0
        
        self.user_name = getpass.getuser()
        
        
    def start(self):
        self._set_period_options()
        
        self._setup_user()
        self._make_view()
        self._bind_keyboard_shortcuts()
        self._load_view()
        
        
    def _bind_keyboard_shortcuts(self):
        # to refresh the list of available jurisdictions
        self.view.bind_all('<Control-r>', self.refresh)
        
        # to exit application
        self.view.bind_all('<Control-q>', self.exit)
         
        # to open the database alter window
        self.view.bind_all('<Control-d>', self._open_database_window)
        
        # to open the verify permit window
        # the shift does not work
        #self.view.bind_all('<Control-V>', self._open_verify_permit)
        
        
    def _open_database_window(self, event):
        database.Controller(self.user_defaults['DB Mode'])
        
        
    def _open_verify_permit(self, event):
        verifypermit.Controller()
        
        
    def _set_period_options(self):
        '''
            Sets the period to display on the main window based on 
            the current year and month.
        '''
        date = datetime.date.today()
        
        year = date.year
        month = date.month
        day = date.day
        start_day = 15
        
        if month in [6,7,8]:
            if month == 6 and day < start_day:
                current_quarter = 4
                current_year = year - 1
            else:
                current_quarter = 1
                current_year = year
                
        elif month in [9,10,11]:
            current_quarter = 1 if month == 9 and day < start_day else 2
            current_year = year
            
        elif month in [12,1,2]:
            if month == 12 and day < start_day:
                current_quarter = 2
                current_year = year  
            else:
                current_quarter = 3
                current_year = year if month == 12 else year - 1
        else:
            current_quarter = 3 if month == 3 and day < start_day else 4
            current_year = year - 1
            
        self.current_period = f'{current_year}Q{current_quarter}'
        
        self.period_options = [
            f'{year}Q{quarter}'
            for year in range(year - self.PERIOD_YEARS, year + self.PERIOD_YEARS) 
            for quarter in [1,2,3,4]
            ]
        

    def _setup_user(self):
        user_exists = False
        
        if utilities.user_exists(self.user_name):
            user_exists = True
        else:
            # adds the new user
            utilities.add_new_user(self.user_name)
            
            # checks if the user was successfully added
            if utilities.user_exists(self.user_name):
                user_exists = True
                
        if user_exists:
            self._set_user_id()
            self._set_user_defaults()
            

    def _set_user_id(self):
        self.user_id = utilities.fetch_user_id(self.user_name)
        
        
    def _set_user_defaults(self):
        default_names = self.defaults.keys()
        
        for name in default_names:
            default = utilities.fetch_default(name, self.user_id)
            
            default = default if default is not None else self.defaults[name]
            
            self.user_defaults[name] = default
             
         
    def _make_view(self):
        '''
            Initializes the graphical user interface.
        '''
        self.view = View(self)
        
        self.show_addons = tk.IntVar(value=1)
        self.show_jurisdictions = tk.IntVar(value=1)
        self.show_transits = tk.IntVar(value=1)
        self.show_non_clients = tk.IntVar()
        
        self.view.config(menu=Menu(self))
        
        
    def _load_view(self):
        self.view.period_cbo.configure(values=self.period_options)
        self.view.period_cbo.set(self.current_period)
        
        self.view.process_cbo.set_value_list(self.process_names)
        self.view.process_cbo.set(self.user_defaults['Process'])
        
        self.view.basis_cbo.config(values=self.options['Basis'])
        self.view.count_cbo.config(values=self.options['Count'])
        self.view.interval_cbo.config(values=self.options['Interval'])
        self.view.order_cbo.config(values=self.options['Order'])
        self.view.output_cbo.config(values=self.options['Output'])
    
        self.set_jurisdiction_list()
        
        self.view.search_entry.focus()
        
        self.view.mainloop()
        
        
    def set_jurisdiction_list(self, clear_first=True):
        '''
            Inserts the jurisdictions into the left treeview.
        '''
        if clear_first:
            self._clear_juri_tree()
            
        self.view.search_entry.delete(0, 'end')
        
        self.juri_list = []
        
        include_addons = self.show_addons.get()
        include_jurisdictions = self.show_jurisdictions.get()
        include_transits = self.show_transits.get()
        
        if include_jurisdictions or include_addons or include_transits:
            include_nonclients = self.show_non_clients.get()
        
            union_query = ''
            
            if include_jurisdictions:
                union_query += self.jurisdicitions_query
                
            if include_addons:
                new_query = 'UNION ' if union_query else ''
                
                union_query += f'{new_query}{self.addons_query}'
                
            if include_transits:
                new_query = 'UNION ' if union_query else ''
                
                union_query += f'{new_query}{self.transits_query}'
            
            query = f'''
                SELECT Id, {constants.TAC_COLUMN_NAME},
                    name
                        
                FROM (
                    {union_query}
                    )
                
                WHERE IsClient!=?
                '''
            
            results = utilities.execute_sql(
                sql_code=query, args=(include_nonclients, ), 
                db_name=constants.STARS_DB, fetchall=True
                )
            
            if results:
                for juri_id, tac, name in sorted(results, key=itemgetter(0)):
                    if not self.view.queue_tree.exists(juri_id):
                        self.juri_list.append((juri_id, tac, name))
                        
                        self.view.juri_tree.insert(
                            '', 'end', iid=juri_id, values=(juri_id, tac, name)
                            )
                        
        self._set_available_label()

        
    def _clear_juri_tree(self):
        self.view.juri_tree.delete(*self.view.juri_tree.get_children())
        
        
    def _clear_queue_tree(self):
        self.view.queue_tree.delete(*self.view.queue_tree.get_children())
       
        
    def on_search_key_press(self, event):
        search_word = self.view.search_entry.get()
        
        if event.keysym == 'BackSpace' and len(search_word) == 1:
            self.set_jurisdiction_list()
            
            
        elif event.keysym == 'Delete':
            cursor_index = self.view.search_entry.index('insert')
            
            if not cursor_index:
                self.set_jurisdiction_list()
                
        else:
            count = 0 
            
            if re.match(self.juri_search_pattern, event.char):
                self._clear_juri_tree()
                
                search_word += event.char
                
                for juri_id, tac, name in self.juri_list:
                    juri_info = juri_id + tac + name
                    
                    if re.search(search_word, juri_info, re.IGNORECASE):
                        self.view.juri_tree.insert(
                            '', 'end', iid=juri_id, 
                            values=(juri_id, tac, name)
                            )
                        
                        count += 1
                        
            self._set_available_label(count)
                
                
    def on_search_return(self, event):
        self.move_all_right()
        
        self.set_jurisdiction_list(clear_first=False)
        
        
    def on_juri_tree_return(self, event):
        self.move_right()
     
        
    def on_juri_tree_double_click(self, event):
        self.move_right()
    
    
    def on_queue_return(self, event):
        self.move_left()
    
    
    def on_sel_tree_double_click(self, event):
        self.move_left()
        
         
    def move_all_right(self):
        '''
            Loops through all the children in the left treeview to
            insert into the right treeview.
        '''
        for iid in self.view.juri_tree.get_children():
            self._insert_one_right(iid, end=True)
            
        self._clear_juri_tree()
        
        self._set_available_label()
        self._set_selected_label()
        
        
    def move_all_left(self):
        '''
            Loops through all the children in the right treeview to
            insert into the left treeview.
        '''
        for iid in self.view.queue_tree.get_children():
            self._insert_one_left(iid, end=True)
            
        self._clear_queue_tree()
        
        self._set_available_label()
        self._set_selected_label()
        
        
    def move_right(self):
        '''
            Moves one or more selected items from the left treeview
            to the right treeview.
        '''
        selections = self.view.juri_tree.selection()
        
        for iid in selections[::-1]:
            self._insert_one_right(iid)
            
            self._remove_juri(iid)
            
        self._set_available_label()
        self._set_selected_label()
            
    
    def move_left(self):
        '''
            Moves one or more selected items from the right treeview
            to the left treeview.
        '''
        selections = self.view.queue_tree.selection()
        
        for iid in selections[::-1]:
            self._insert_one_left(iid)
            
            self.view.queue_tree.delete(iid)
            
        self._set_available_label()
        self._set_selected_label()
                    
                    
    def _insert_one_right(self, iid, end=False):
        '''
            Inserts one item into the right treeview at the appropriate 
            index.
        '''
        values = self.view.juri_tree.item(iid)['values']
        
        # formats the tac
        tac = utilities.format_tac(values[1])
        
        values[0] = str(values[0])
        values[1] = tac
        
        index = 'end' if end else self._get_right_insert_position(iid)
        
        self.view.queue_tree.insert('', index, iid=iid, values=values)
        
        self.selected_jurisdiction_count += 1
     
        self.juri_list.remove(tuple(values))
        
        if self.selected_jurisdiction_count >= self.COUNT_FOR_QUEUE_SCROLL:
            # if the scrollbar is not already showing
            if not self.queue_scroll:
                self.view.show_queue_scrollbar()
                
                self.queue_scroll = True
                
        if not self.run_enabled and self.processed_selected:
            self.view.enable_run_btn()
            
            self.run_enabled = True
            
        
    def _insert_one_left(self, iid, end=False):
        '''
            Inserts one item into the left treeview at the appropriate 
            index.
        '''
        values = self.view.queue_tree.item(iid)['values']
        
        tac = utilities.format_tac(values[1])
        
        values[0] = str(values[0])
        values[1] = tac
        
        index = 'end' if end else self._get_left_insert_position(iid)
        
        self.view.juri_tree.insert('', index, iid=iid, values=values)
        
        self.selected_jurisdiction_count -= 1
        
        if index == 'end':
            self.juri_list.append(tuple(values))
        else:
            self.juri_list.insert(index, tuple(values))
        
        if self.selected_jurisdiction_count <= self.COUNT_FOR_QUEUE_SCROLL:
            # if the scroll bar is already showing
            if self.queue_scroll:
                self.view.hide_queue_scrollbar()
                
                self.queue_scroll = False
                
        if self.run_enabled and not self.selected_jurisdiction_count:
            self.view.disable_run_btn()
            
            self.run_enabled = False
            
            
    def _get_right_insert_position(self, iid):
        '''
            Returns the index position of where to insert the item into 
            the right treeview. If there are no items or if the first-in- 
            first-out checkbox is checked then zero is returned to insert 
            the item at the top of the treeview. 
        '''
        iids = self.view.queue_tree.get_children()
        
        if iids and not self.get_is_fifo_state():
            return self._get_insert_position(iid, iids)
        else:
            return 0
            
            
    def _get_left_insert_position(self, iid):
        '''
            Returns the index position of where to insert the item into 
            the left treeview. If there are no items then zero is 
            returned to insert the item at the top of the treeview. 
        '''
        iids = self.view.juri_tree.get_children()
        
        if iids:
            return self._get_insert_position(iid, iids)
        else:
            return 0
            
            
    def _get_insert_position(self, new_iid, iids):
        '''
            Returns an integer representing the alphabetical position 
            of the abbreviation being inserted based on the present 
            abbreviations. If it is alphabetically greater than 
            all present abbreviations then a string with word "end" 
            is returned.
        '''
        for i, iid in enumerate(iids):
            if new_iid < iid:
                return i
            
        return 'end'
            
        
    def _remove_juri(self, iid):
        # ignores the error if the item is no longer in the jurisdiction 
        # tree. When a user moves an item to the right after using the search
        # entry, the juri tree will be refilled without that item, so the item
        # does not need to be deleted like when doing a move right from the 
        # full list
        with suppress(TclError):
            self.view.juri_tree.delete(iid)
            
            
    def _set_available_label(self, count=None):
        if not count:
            count = len(self.view.juri_tree.get_children())
        
        self.view.available_label.config(text=f'Available: {count}')
    
    
    def _set_selected_label(self):
        count = len(self.view.queue_tree.get_children())
        
        self.view.selected_label.config(text=f'Selected: {count}')
                 
                 
    def on_juri_chk_click(self):
        self.set_jurisdiction_list()
        
        
    def on_addon_chk_click(self):
        self.set_jurisdiction_list()
        
        
    def on_transit_chk_click(self):
        self.set_jurisdiction_list()
    
        
    def on_noncl_chk_click(self):
        self.set_jurisdiction_list()
        
        
    def on_available_tree_view_click(self, event):
        region = self.view.juri_tree.identify_region(event.x, event.y)
        
        if region == 'heading': 
            column = self.view.juri_tree.identify_column(event.x)
            
            # column is like "#1" starting at 1, last part of that minus one 
            # is equal to the index of that column
            sort_index = int(column[-1]) - 1
            
            self.juri_list.sort(key=itemgetter(sort_index))
            
            available_ids = set(self.view.juri_tree.get_children())
            
            for juri_id, tac, name in self.juri_list:
                # if the jurisdiction is still in the "available" treeview
                if juri_id in available_ids:
                    self.view.juri_tree.delete(juri_id)
                
                    self.view.juri_tree.insert(
                        '', 'end', iid=juri_id, values=(juri_id, tac, name)
                        )

        
    def refresh(self, event=None):
        self.set_jurisdiction_list()
    
    
    def exit(self, event=None):
        answer = True
        
        if threading.active_count() > 1:
            answer = msg.askyesno(
                constants.APP_NAME, 
                'One or more processes are still running. Are you sure '
                'you want to exit?'
                )
            
        if answer:
            self.end_processes = True
            self.view.destroy()
            self._delete_temp_files()
       
            
    def _delete_temp_files(self):
        for path in constants.TEMP_FILE_PATH.iterdir():
            path.unlink() 
        
        
    def on_run_click(self):
        selections = Selections(self)
        
        model = Model(self, selections)
        model.start()
        
        
    def get_ascending(self):
        return self.view.ascending_chk_state.get()
        
        
    def get_basis(self):
        return self.view.basis_cbo.get()
    
    
    def get_count(self):
        return self.view.count_cbo.get()
    
    
    def get_interval(self):
        return self.view.interval_cbo.get()
        
        
    def get_process_name(self):
        return self.process_name
            
            
    def get_estimates_state(self):
        return self.view.estimates_chk_state.get()
    
    
    def get_exclude_files_state(self):
        return self.view.exclude_files_chk_state.get()
    
    
    def get_geos_state(self):
        return self.view.geos_chk_state.get()
            
            
    def get_is_fifo_state(self):
        return self.view.fifo_chk_state.get()
            
            
    def get_open_state(self):
        return self.view.open_chk_state.get()
    
    
    def get_order(self):
        return self.view.order_cbo.get()
    
    
    def get_output_type(self):
        return self.view.output_cbo.get()
    
    
    def get_pdf_only_state(self):
        return self.view.pdf_only_chk_state.get()
    
    
    def get_period(self):
        return self.view.period_cbo.get()
    
    
    def get_period_options(self):
        return self.period_options
    
    
    def get_queue_list(self):
        return self.view.queue_tree.get_children()
    
    
    def get_type_option(self):
        return self.view.type_cbo.get()
    
    
    def get_view(self):
        return self.view
    
        
    def on_process_change(self, *args):
        process_name = self.view.process_name.get()
        
        if process_name in self.process_names:
            self.processed_selected = True
            
            if process_name != self.process_name:
                self.process_name = process_name
                
                self.view.hide_option_widgets()
                self.view.show_option_widgets(self.process_name)
            
            # if any jurisdictions are selected
            if not self.run_enabled and self.selected_jurisdiction_count:
                self.view.enable_run_btn()
                
                self.run_enabled = True
                
        else:
            self.processed_selected = False
            
            if self.run_enabled:
                self.view.disable_run_btn()
                
                self.run_enabled = False
