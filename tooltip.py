'''
Created on Dec 3, 2018

@author: vahidrogo
'''


import tkinter as tk

  
class ToolTip(object):
    '''
    Creates a ToolTip for a given widget
    '''
    
    # time to wait before showing in miliseconds
    WAIT_TIME = 500   
    
    WRAP_LENGTH = 180 
    
    
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        
        self.enter_bind = self.widget.bind('<Enter>', self.enter)
        self.leave_bind = self.widget.bind('<Leave>', self.leave)
        
        self.id = None
        self.top_window = None
        
 
    def enter(self, event=None):
        self._schedule()
        
 
    def leave(self, event=None):
        self._unschedule()
        self._hidetip()
        
 
    def _schedule(self):
        self._unschedule()
        
        self.id = self.widget.after(self.WAIT_TIME, self._showtip)
        
 
    def _unschedule(self):
        id = self.id
        
        self.id = None
        
        if id:
            self.widget.after_cancel(id)
            
 
    def _showtip(self):
        x, y, cx, cy = self.widget.bbox('insert')
        
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 20
        
        # creates a toplevel window
        self.top_window = tk.Toplevel(self.widget)
        
        # Leaves only the label and removes the app window
        self.top_window.wm_overrideredirect(True)
        
        self.top_window.wm_geometry(f'+{x}+{y}')
        
        label = tk.Label(
            self.top_window, text=self.text, justify='left', 
            background='#ffffe0', relief='solid', borderwidth=1, 
            wraplength=self.WRAP_LENGTH
            )
        
        label.pack(ipadx=1)
 
    def _hidetip(self):
        if self.top_window:
            self.top_window.destroy()
            
        self.top_window = None

            
    def delete(self):
        # Removes the bindings from the widget.
        self.widget.unbind('<Enter>', self.enter_bind)
        self.widget.unbind('<Leave>', self.leave_bind)
        
        # waits before hiding in case the tooltip was already scheduled
        self.widget.after(self.WAIT_TIME, self._hidetip)
        
        
        