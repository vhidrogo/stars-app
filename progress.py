'''
Created on Apr 6, 2018

@author: vahidrogo
'''

from contextlib import suppress
import math
import threading
import time
from timeit import default_timer as timer
import tkinter as tk
from tkinter import ttk
from _tkinter import TclError

import constants


class Progress(tk.Toplevel):
    '''
        Top level window that will pop up to show the progress of a file or
        group of files being processed.
    '''
    
    
    BAR_LENGTH = 480
    PROGRESS_MAXIMUM = 100
    HEIGHT = 110
    WIDTH = 500
    
    
    def __init__(self, controller, title, abort=True):
        super().__init__()
        
        self.controller = controller
        self.abort = abort
        
        self.remaining_seconds = 0
        
        self.previous_progress = 0
        
        self.timer = None
        
        self.progress_var = tk.DoubleVar()
            
        self.title(title)
        
        self.protocol('WM_DELETE_WINDOW', self._end_process)
        
        # prevents the window from being resized
        self.resizable(width=False, height=False)
        
        self._window_setup()
        self._make_widgets()
        
        
    def _window_setup(self):
        '''
            Sets the dimensions of the window and creates the window in the
            center of the screen it is being displayed on based on the size
            of the screen.
        '''
        x_offset = (self.winfo_screenwidth() - self.WIDTH) // 2
        y_offset = (self.winfo_screenheight() - self.HEIGHT) // 2
        
        self.geometry(f'+{x_offset}+{y_offset}')
        
        
    def _make_widgets(self):
        '''
            Creates objects for the progress window and packs them to
            the window that was created in the center of the screen.
        '''
        main_frm = ttk.Frame(self)
        
        progress_bar = ttk.Progressbar(
            main_frm, length=self.BAR_LENGTH, variable=self.progress_var
            )
        progress_bar.config(maximum=self.PROGRESS_MAXIMUM)
        
        progress_label_frm = ttk.Frame(main_frm)
        
        self.status_label = ttk.Label(progress_label_frm)
        self.percent_label = ttk.Label(progress_label_frm)
        
        self.remaining_seconds_label = ttk.Label(
            main_frm, text='Remaining: calculating...'
            )
        
        if self.abort:
            btn = ttk.Button(
                main_frm, text='Abort', command=self._end_process
                )
        
        main_frm.pack(fill='x', padx=constants.OUT_PAD, pady=constants.OUT_PAD)
        
        progress_bar.pack(fill='x')
        
        progress_label_frm.pack(fill='x')
        
        self.status_label.pack(anchor='w', side='left')
        self.percent_label.pack(anchor='e')
        
        #self.remaining_seconds_label.pack(anchor='e', pady=constants.OUT_PAD)
        
        if self.abort:
            btn.pack(anchor='e')
        
        
    def _end_process(self):
        '''
            Sets the end process flag of the Controller object to True
            and destroys the progress window.
        '''
        self.controller.abort = True
        self.destroy()
        
        
    def update_progress(
            self, progress, message, current_count=1, total_count=1):
        '''
            Updates the progress bar on the progress window gui. The 
            given progress will determine the part of the progress bar 
            that is filled and the message will be displayed in the label
            just under the progress bar.
            
            
        
            Args:
                progress: An integer representing the total progress of 
                    the file or group of files hat are being run.
                
                message: A string representing the message that will 
                    be shown on the progress window, if there is more 
                    than one city running at a time than a message to 
                    show the progress of the total cities being run will 
                    be added to the beginning of the string.
        '''
        if total_count > 1:
            progress = self._calculate_progress(
                current_count, total_count, progress)
            
            message = (
                f'Jurisdiction {current_count} of {total_count}: {message}'
                )
            
        self.previous_progress = self.progress_var.get()
        
        self.progress_var.set(progress)
            
        #=======================================================================
        # if self.timer:
        #     remaining_seconds = self._remaining_seconds(progress)
        #     
        #     if not self.remaining_seconds or remaining_seconds < self.remaining_seconds:
        #         self.remaining_seconds = remaining_seconds
        #         
        #         self.remaining_seconds_label.config(
        #             text=f'Remaining: {datetime.timedelta(seconds=int(remaining_seconds))}'
        #             )
        # 
        # else:
        #     self.timer = timer()
        #=======================================================================
        
        percent_string = f'{int(progress)}%'
        
        self.status_label.config(text=message)
        self.percent_label.config(text=percent_string)
        
        
    def _calculate_progress(self, current_count, total_count, progress):
        '''
            Returns the calculated progress for the progress bar based on 
            the progress of the current report for the current city and 
            on how many cities are running at once. If there is more than
            one city running with the current group than the total progress
            is calculated by dividing the bar into sections based on how 
            many cities are running and the current progress of the current
            city. The total progress is then the portion of the bar of each 
            city times the cities that have already been processed plus the 
            same portion times the progress of the current report.
        
            Args: An integer representing the current progress of the 
                report for the current city.
                
            Returns:
                The calculated progress for the progress bar.
        '''
        interval = 100 / total_count
        
        completed_progress = interval * (current_count - 1)
        
        current_file_progress = interval * (progress/100)
        
        return completed_progress + current_file_progress
    
    
    def _remaining_seconds(self, new_progress):
        progress_increment = new_progress - self.previous_progress
        
        time_elapsed = self._time_elapsed()
        
        remaining_seconds_progress = self.PROGRESS_MAXIMUM - new_progress 
        
        if progress_increment and remaining_seconds_progress > 0:
            # calculates the time remaining_seconds
            remaining_seconds = remaining_seconds_progress / progress_increment * time_elapsed
            
        else:
            remaining_seconds = 0
      
        return remaining_seconds
        
        
    def _time_elapsed(self):
        new_timer = timer()
        
        time_elapsed = new_timer - self.timer
        
        # sets the current timer to the new timer
        self.timer = new_timer
        
        return time_elapsed

  
class LoadingCircle(threading.Thread):
    '''
        Animated LoadingCircle loading indicator that runs on separate thread.
        Infinite animation starts by calling start() and ends by calling 
        end().
    '''
    
    
    # dimensions of square window
    WINDOW_DIM = 100
    WINDOW_CENTER = WINDOW_DIM // 2
    
    # radius of outer circle formed by inner circles
    OUTER_RAD = WINDOW_CENTER - constants.OUT_PAD
    
    # circumference of outer circle
    OUTER_CIRC = 2 * math.pi * OUTER_RAD
    
    # scale of inner circles compared to outer circle
    INNER_SCALE = .15
    
    # radius of inner circles
    INNER_RAD = OUTER_RAD * INNER_SCALE
    
    # diameter or inner circles
    INNER_DIA = INNER_RAD * 2
    
    # count of inner circles that will form the outer circle
    INNER_COUNT = int(OUTER_CIRC // (INNER_DIA + INNER_RAD)) 
    
    # interval in seconds for cycling the colors
    CYCLE_INTERVAL = .05
    
    # colors that will be cycled
    colors = [
        '#00fe00','#00e400','#00cb00','#00b100','#009800','#007e00','#006500'
        ]
    

    def __init__(self, parent, text='Loading', bg_color=None):
        super().__init__()
        
        self.daemon = True
        
        self.parent = parent
        self.text = text
        self.bg_color = bg_color
        
        self.center_coordinates = []
        self.circle_ids = []
        
        self._set_center_coordinates()
        
        self._window_setup()
        
        self.canvas = tk.Canvas(self.window)
        self.canvas.pack()
        
        # writes the text in the center of the window
        self.canvas_text = self.canvas.create_text(
            self.WINDOW_CENTER, self.WINDOW_CENTER, text=self.text, 
            width=self.WINDOW_DIM
            )
        
        if not self.bg_color is None:
            self.canvas.config(bg=self.bg_color)
        
        self._draw_circles()
        
        self.running = True
        
        self.config_bind = self.parent.bind('<Configure>', self.on_parent_configure)
        
        
    def _set_center_coordinates(self):
        '''
            Calculates center coordinates for each inner circle along
            the circumference of the outer circle.
        '''
        for i in range(self.INNER_COUNT):
            center_x = int(
                self.WINDOW_CENTER + (
                    math.cos(
                        2 * math.pi / self.INNER_COUNT * i
                        ) * self.OUTER_RAD
                    )
                )
            
            center_y = int(
                self.WINDOW_CENTER + (
                    math.sin(
                        2 * math.pi / self.INNER_COUNT * i
                        ) * self.OUTER_RAD
                    )
                )
            
            coords = (center_x, center_y)
            
            self.center_coordinates.append(coords)
            

    def _draw_circles(self):
        '''
            Draws circles based on each of the center points.
        '''
        for center_x, center_y in self.center_coordinates:
            x0 = center_x - self.INNER_RAD
            y0 = center_y - self.INNER_RAD
            x1 = center_x + self.INNER_RAD
            y1 = center_y + self.INNER_RAD
            
            # draws the circle filled with the lightest color
            circle_id = self.canvas.create_oval(
                x0, y0, x1, y1, fill=self.colors[0], outline=''
                )
            
            self.circle_ids.append(circle_id)
        
        
    def run(self):
        '''
            Begins the animation. Cycles the colors according to the 
            set interval.
        '''
        current_id = 0
        
        while self.running:
            circle_id = current_id
            
            for color in self.colors:
                with suppress(TclError):
                    self.canvas.itemconfig(self.circle_ids[circle_id], fill=color)
                
                circle_id = self._next_circle_index(circle_id)
                
            time.sleep(self.CYCLE_INTERVAL)
                
            current_id += 1
            
            if current_id == self.INNER_COUNT:
                current_id = 0
                
        self.parent.unbind('<Configure>', self.config_bind)
            
            
    def _next_circle_index(self, circle_index):
        '''
            Returns the next id based on the given id. If the next id
            is greater then the last id then it starts again at the first 
            id.
        '''
        next_id = circle_index + 1
        
        if next_id >= self.INNER_COUNT:
            next_id -= self.INNER_COUNT
            
        return next_id


    def _window_setup(self):
        '''
            Sets the dimensions of the window and creates the window in the
            center of the screen it is being displayed on based on the size
            of the screen.
        '''
        self.window = tk.Toplevel(self.parent)
        
        # removes window border and buttons
        self.window.overrideredirect(1)
        
        # grabs the focus from all other windows in the app
        self.window.grab_set()
        
        center_x, center_y = self._center_xy()
        
        self.window.geometry(
            f'{self.WINDOW_DIM}x{self.WINDOW_DIM}+{center_x}+{center_y}'
            )
    
    
    def end(self):
        # stops the animation
        self.running = False
        
        # waits for the current cycle to finish
        time.sleep(self.CYCLE_INTERVAL * len(self.colors))
        
        self.window.destroy()
        
        
    def on_parent_configure(self, event):
        '''
            Moves the window along with the parent window so that it 
            remains in the center of the parent window.
        '''
        center_x, center_y = self._center_xy()
        
        self.window.geometry(f'+{center_x}+{center_y}')
        
        
    def _center_xy(self):
        parent_center_x, parent_center_y = self._parent_center_xy()
        
        return parent_center_x - self.WINDOW_DIM // 2, parent_center_y - self.WINDOW_DIM // 2
        
        
    def _parent_center_xy(self):
        x, y = self.parent.winfo_rootx(), self.parent.winfo_rooty()
        
        width, height = self.parent.winfo_width(), self.parent.winfo_height()
        
        center = (x + width // 2, y + height // 2)
        
        return center
    
    
    def update_text(self, text):
        '''
            Updates the text object in the center of the canvas.
        '''
        self.canvas.itemconfig(self.canvas_text, text=text)
    
    
    
    
    
    
    
    
    
    
    
    