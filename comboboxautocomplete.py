'''
Created on Nov 30, 2018

@author: vahidrogo
'''

from tkinter import ttk


class ComboboxAutoComplete(ttk.Combobox):
    '''
        Adds typing autocomplete functionality to the Combobox widget
        from the ttk module.
    
        %d = Type of action (1=insert, 0=delete, -1 for others)
        %i = index of char string to be inserted/deleted, or -1
        %P = value of the entry if the edit is allowed
        %s = value of entry prior to editing
        %S = the text string being inserted or deleted, if any
        %v = the type of validation that is currently set
        %V = the type of validation that triggered the callback
            (key, focusin, focusout, forced)
        %W = the tk name of the widget
    '''
    
    
    def __init__(self, parent, selected_function=None, value_list=[], **kwargs):
        super().__init__(parent, **kwargs)
        
        self.selected_function = selected_function
        self.value_list = []
        
        if value_list:
            self.set_value_list(value_list)
            
        self.cursor_position = 0
        
        vcmd = (self.register(self._on_validate), '%d', '%i', '%P')
            
        self.config(validate='key', validatecommand=vcmd)
          
        self.bind('<<ComboboxSelected>>', self._selected)
        self.bind('<Tab>', self._selected)
        self.bind('<KeyRelease>', self._key_handler)
        
        
    def _selected(self, event=None):
        value = self.get()
        
        if value and value in self.value_list:
            if self.selected_function:
                self.icursor('end')
                self.select_range(0, 'end')
                
                self.selected_function()
        
        
    def _key_handler(self, event):
        keysm = event.keysym
        
        if keysm in ['Return', 'Right']:
            self._selected()
        
        elif keysm in ['BackSpace', 'Left']:
            self.delete(self.cursor_position, 'end')
            
            self.cursor_position += 1
            self.icursor(self.cursor_position)
        
        
    def _on_validate(self, d, i, P):
        '''
            Args:
                d: type of action "1" = insert, "0" = delete, "-1" = others 
                i: index of char string to be inserted
                P: value of entry if the edit is allowed
        '''
        # if a character is being inserted
        if d == '1':
            self.cursor_position = int(i) + 1
            
            if P:
                match_value = ''
                 
                for value in self.value_list:
                    if value.lower().startswith(P.lower()):
                        match_value = value 
                         
                        break
                     
                if match_value:
                    self.set(match_value)
                    
                    # places the cursor after the character that was just inserted
                    self.icursor(self.cursor_position)
                    
                    # highlights all the characters to the right of the one inserted
                    self.select_range(self.cursor_position, 'end')
             
        return True
        
        
    def set_value_list(self, value_list):
        self.config(values=value_list)
        
        self.value_list = value_list
        
