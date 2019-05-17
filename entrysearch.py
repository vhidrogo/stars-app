'''
Created on Dec 6, 2018

@author: vahidrogo
'''

from contextlib import suppress
import tkinter as tk
from tkinter import ttk
from _tkinter import TclError

import constants


class EntrySearch(ttk.Frame):
    '''
        A combination of ttk widgets that consists of an entry and 
        a search button as well as a list view to display search 
        results.
    '''
    
     
    def __init__(self, parent, search_function, select_function, width):
        super().__init__(parent)
        
        # function that will be called when the user clicks on search
        self.search_function = search_function
        
        # function that will be called when the user select a value 
        # from the values in the listbox 
        self.select_function = select_function
        self.width = width
        
        self.top_window = None
        
        self.value = tk.StringVar()
        
        self._make_entry()
        
        self._make_search_button()
        
        
    def _make_entry(self):
        self.entry_frm = ttk.Frame(self)
        
        self.entry = ttk.Entry(
            self.entry_frm, textvariable=self.value, width=self.width
            )
        
        self.entry.bind('<Return>', self.search_function)
        
        self.entry_frm.pack(expand=1, fill='x', side='left')
        self.entry.pack(fill='x')
        
        
    def _make_search_button(self):
        self.search_btn = ttk.Button(
            self, text='Search', command=self.search_function, takefocus=False
            )
        
        self.search_btn.pack(padx=constants.OUT_PAD)
        
        
    def set_value_list(self, value_list):
        if value_list:
            self.hide_value_list()
            self._show_value_list()
            
            listbox_width = self.width
            
            if len(value_list) >= constants.COUNT_FOR_SCROLLBAR:
                self.y_scroll.pack(expand=1, fill='y')
                
                # to make room for the scrollbar
                listbox_width -= 3
                
            else:
                self.y_scroll.pack_forget()
                
            self.listbox.config(width=listbox_width)
            
            # ignores the error if the user chooses a value which 
            # destroys window before all values are inserted 
            with suppress(TclError):
            
                for value in value_list:
                    self.listbox.insert('end', value)
                    
                self.listbox.selection_set(0)
                self.listbox.focus()
            
        else:
            self.hide_value_list()
        
        
    def _show_value_list(self):
        x = self.entry.winfo_rootx() 
        y = self.entry.winfo_rooty() + self.entry.winfo_height()
        
        self.top_window = tk.Toplevel(self)
        self.top_window.wm_overrideredirect(True)
        
        self.top_window.wm_geometry(f'+{x}+{y}')
        
        self.y_scroll = tk.Scrollbar(self.top_window, orient='vertical')
        
        self.listbox = tk.Listbox(
            self.top_window, yscrollcommand=self.y_scroll.set, width=self.width
            )
        
        self.listbox.bind('<Double-Button-1>', self._on_value_select)
        self.listbox.bind('<Return>', self._on_value_select)
        
        self.y_scroll.config(command=self.listbox.yview)
        
        self.listbox.pack(side='left')
        
        
    def hide_value_list(self):
        if self.top_window:
            self.top_window.destroy()
            
            self.top_window = None
        

    def _on_value_select(self, event):
        selection = self.listbox.curselection()
        value = self.listbox.get(selection)
        
        self.set(value)
        
        self.hide_value_list()
        
        self.select_function()
        
        
    def get(self):
        return self.value.get()
    
    
    def set(self, value):
        self.value.set(value)
        
        self._highlight_value()
        
        
    def _highlight_value(self):
        self.entry.select_range(0, 'end')
        self.entry.icursor('end')
        self.entry.focus()
