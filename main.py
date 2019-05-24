'''
Created on Jul 9, 2018

@author: vahidrogo

To build folder with .exe:
    While in command line, navigate to directory with main.py

    Initial build command (if main.spec does not exist yet):
        pyinstaller -w main.py
    
    Add these lines to main.spec after "a.binaries," in "coll":
        Note: Update path if files have been moved
    
        Tree('N:\\python\\starsapp\\files', prefix='files\\'),
        Tree('N:\\python\\starsapp\\files\\tkdnd2.8', prefix='tkdnd2.8\\'),
        
    Re-build with command:
        pyinstaller -w main.spec
        
'''

import importlib
import tkinter as tk
from tkinter import ttk
from PIL import ImageTk, Image

import constants


class SplashScreen(tk.Tk):
    '''
        Window that displays a photo background with the name of the 
        application. The current version and progress of modules being 
        loaded is also displayed.
    '''
    
    
    HEIGHT = 300
    WIDTH = 600

    
    def __init__(self):
        super().__init__()
        
        # hides the outer frame of the window
        self.overrideredirect(1)
        
        self.img_path = constants.MEDIA_PATH.joinpath('loading_background.jpg')
        
        self.img = None

        self.progress_var = tk.IntVar()
        
        self._center_window()
        self._make_widgets()
        self.focus()
        
        
    def _center_window(self):
        x_offset = (self.winfo_screenwidth() - int(self.WIDTH)) // 2
        y_offset = (self.winfo_screenheight() - int(self.HEIGHT)) // 2
        
        self.geometry(f'{self.WIDTH}x{self.HEIGHT}+{x_offset}+{y_offset}')
        

    def _make_widgets(self):
        self.img = ImageTk.PhotoImage(Image.open(self.img_path))
        
        background = ttk.Label(self, image=self.img)
        
        version_frm = ttk.Frame(self)
        progress_frm = ttk.Frame(self)
        
        version_lbl = tk.Label(
            version_frm, anchor='w', text=constants.APP_VERSION, 
            font='Arial 12 bold', bg=constants.BLUE_THEME_COLOR,
            fg='white'
            )
        
        self.loading_lbl = tk.Label(
            progress_frm, anchor='w', text='Loading...', fg='white', 
            bg=constants.BLUE_THEME_COLOR
            )

        progress_bar = ttk.Progressbar(
            progress_frm, length=self.WIDTH - 3, maximum=len(constants.MODULES), 
            variable=self.progress_var
            )
        
        background.grid(row=0, column=0)
        
        version_frm.grid(
            row=0, column=0, sticky='e', padx=(0, 8), pady=(20, 0)
            )
        
        progress_frm.grid(row=0, column=0, sticky='s')
        
        version_lbl.pack(fill='x')
        self.loading_lbl.pack(fill='x')
        progress_bar.pack(fill='x')
        
        
    def import_modules(self):
        '''
            Dynamically loads each module in the constant list of modules.
            Updates a label in self with the name of the module and a
            progress bar that indicates the progress of the modules.
        '''
        self.update()
        
        for i, module in enumerate(constants.MODULES, start=1):
            self.loading_lbl.configure(text=f'Loading {module}')
            
            self.update()
             
            importlib.import_module(module)
     
            self.progress_var.set(i)
            self.update()
     
        self.destroy()


if __name__ == '__main__':
    splash_screen = SplashScreen()
    splash_screen.import_modules()
    
    import starsapp
    
    app = starsapp.Controller()
    app.start()
    
    
