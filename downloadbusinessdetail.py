'''
Created on Oct 10, 2018

@author: vahidrogo
'''

from pathlib import Path
from selenium import webdriver
from selenium.common.exceptions import *
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC   
from selenium.webdriver.support.ui import WebDriverWait
import time
import tkinter as tk
from tkinter import messagebox as msg
from tkinter import ttk

from clearviewdetail import ClearviewDetail
import constants
from loaddetail import LoadDetail
import utilities


BASE_URL = 'https://reports.muniservices.com/microstrategy/asp/main.aspx'

CHECK_DOWNLOAD_INTERVAL = 1
    
WAIT_FOR_DOWNLOAD = 600
WAIT_FOR_PAGE = 3
WAIT_FOR_TAC = 10

PARTIAL_DOWNLOAD_ID = '.crdownload'


class DownloadBusinessDetail:
    '''
    '''
    
    
    #javascript_click = 'document.querySelectorAll("{}")[0].click()'
    javascript_click = "document.querySelector('{}').click()"
    
    xpath_format = '//a[contains(text(),"{}")]'
    
    other_xpaths  = {
        'tac_search' : '//input[@id="id_mstr56_txt"]',
        'tac_selected' : '//*[@id="id_mstr58ListContainer"]/div/div',
        'export' : '//*[@id="tbExport"]'
        }
    
    # text of the elements in the html
    texts = {
        '@CRProduction' : '@CRProduction',
        'Workables' : 'Workables',
        'QE' : 'QE_stars',
        'QC' : 'QC_stars',
        'QE_AO' : 'QE_AO_stars',
        'QC_AO' : 'QC_AO_stars',
        }
    
    selectors = {
        '@CRProduction' : 'a[title="@CRProduction"]',
        'export' : '#tbExport',
        'QE' : 'a[title="QE_stars"]',
        'QC' : 'a[title="QC_stars"]',
        'QE_AO' : 'a[title=QE_AO_stars]',
        'QC_AO' : 'a[title=QC_AO_stars]',
        'Shared_Reports' : 'span:nth-child(3) > a',
        'tac_search' : '.mstrBGIcon_tbSearch',
        'Workables' : 'a[title="Workables"]',
        }
   
    
    def __init__(self, controller, selections):
        self.controller = controller
        self.selections = selections
        
        self.user_set = False
        
        self._set_user()
        
        if self.user_set:
            self.report_type = ''
            
            self.chrome_path = str(constants.APPS_PATH.joinpath('chromedriver.exe'))
            
            self._set_driver()
             
            self.clearview_detail = ClearviewDetail()
        
        
    def _set_user(self):
        login_gui = LoginGui()
        
        gui_closed = False
        
        while not gui_closed:
            time.sleep(1)
            
            gui_closed = login_gui.is_closed()
            
        self.username = login_gui.get_username()
        self.password = login_gui.get_password()
        
        if self.username and self.password:
            self.user_set = True
    
    
    def _set_driver(self):
        chrome_options = webdriver.ChromeOptions()
        #chrome_options.add_argument('--headless')
        chrome_options.add_argument('--disable-gpu')
        
        self.driver = webdriver.Chrome(
            executable_path=self.chrome_path, chrome_options=chrome_options
            )
    
    
    def main(self, jurisdiction):
        if self.user_set:
            self.jurisdiction = jurisdiction
            
            self.is_addon = utilities.is_addon(self.jurisdiction)
            
            self._set_report_type()
            
            self.output_folder = utilities.get_downloads_folder()
            self.output_file_name = self._get_output_file_name()
            
            self.output_path = str(
                Path(self.output_folder).joinpath(
                    f'{self.texts[self.report_type]}{self.output_file_name}.csv'
                    )
                )
            
            try:
                self.controller.update_progress(
                    0, f'{self.jurisdiction.id}: Loading {BASE_URL}'
                    )
                
                self.driver.get(BASE_URL)
               
                self.controller.update_progress(
                    5, f'{self.jurisdiction.id}: Logging in.'
                    )
                
                logged_in = False
                
                self._log_in()
                
                self.controller.update_progress(
                    10, f'{self.jurisdiction.id}: Loading STARS_Analytics'
                    )
                
                try:
                    self._load_project_page()
                    
                    logged_in = True
                    
                except Exception:
                    msg.showerror(
                        self.selections.title, 'Login failed.'
                        )
                    
                if logged_in:
                    element_name = 'Shared_Reports'
                     
                    self.controller.update_progress(
                        15, f'{self.jurisdiction.id}: Loading {element_name}'
                        )
                     
                    # clicks on "Shared Reports" at the top
                    self._execute_javascript(element_name)
                     
                    element_name = '@CRProduction'
                     
                    self.controller.update_progress(
                        20, f'{self.jurisdiction.id}: Loading {element_name}'
                        )
                     
                    # if the page has loaded
                    if self._element_is_present(element_name):
                        # clicks on "@CRProduction" folder
                        self._execute_javascript(element_name)
                         
                        element_name = 'Workables'
                          
                        self.controller.update_progress(
                            25, f'{self.jurisdiction.id}: Loading {element_name}'
                            )
                          
                        if self._element_is_present(element_name):
                            # clicks on "workables" folder
                            self._execute_javascript(element_name)
                             
                            self.controller.update_progress(
                                30, f'{self.jurisdiction.id}: Loading {self.report_type}'
                                )
                               
                            if self._element_is_present(self.report_type):
                                self._run_report()
                                 
                                element_name = 'export'
                                    
                                self.controller.update_progress(
                                    50, f'{self.jurisdiction.id}: Loading {element_name}')
                                    
                                if self._element_is_present(
                                    element_name, xpath=self.other_xpaths[element_name],
                                    wait=WAIT_FOR_DOWNLOAD):
                                        
                                    # clicks the export button to download the report
                                    self._execute_javascript(element_name)
                                        
                                    self.controller.update_progress(
                                        50, f'{self.jurisdiction.id}: Downloading.')
                                        
                                    self._wait_for_download()
                          
                    # closes Chrome
                    self._close()
                    
                    if Path(self.output_path).is_file():
                        # gets the data from the file that was just 
                        # downloaded into a pandas dataframe
                        df = self.clearview_detail.get_dataframe(self.output_path)
                        
                        if df is not None:
                            output_path = self._get_output_path()
                            
                            load_detail = LoadDetail(self.controller, df, output_path)
                            load_detail.load(self.jurisdiction)
                
            except Exception as e:
                # Will use with headless mode
                #self._close()
                
                msg.showerror(
                    self.selections.title, 
                    f'Unhandled exception: {e} occurred during the automation '
                    'process, please continue where the program left off.'
                    )
                
    

    def _set_report_type(self):
        if self.selections.basis == 'Cash':
            report = 'QC_AO' if self.is_addon else 'QC'
        else:
            report = 'QE_AO' if self.is_addon else 'QE'
            
        self.report_type = report
        
        
    def _get_output_file_name(self):
        name = f'_{self.jurisdiction.id}_{time.strftime("%Y%m%d_%H%M%S")}'
        
        return name
    
    
    def _log_in(self):
        user_entry = self.driver.find_element_by_id('Uid')
        password_entry = self.driver.find_element_by_id('Pwd')
        login_button = self.driver.find_element_by_id('3054')
        
        user_entry.send_keys(self.username)
        password_entry.send_keys(self.password)
        login_button.click()
        
        
    def _load_project_page(self):
        # clicks the "STARS_Analytics" icon
        self.driver.find_element_by_class_name('mstrLargeIconViewItemLink').click()
        
        
    def _execute_javascript(self, element):
        selector = self.selectors[element]
        
        command = self._get_javascript(selector)
        
        self.driver.execute_script(command)
        
        
    def _get_javascript(self, css_selector):
        return self.javascript_click.format(css_selector)
         

    def _get_xpath(self, element):
        '''
        '''
        element_text = self.texts[element]
        
        xpath = self.xpath_format.format((element_text))
        
        return xpath
    
    
    def _element_is_present(
            self, element=None, xpath=None, wait=WAIT_FOR_PAGE):
        '''
            Returns whether an element is present on the current page, a 
            set time of seconds will be waited for to try and locate the 
            element. The xpath of element will be used to try to locate it.
        
            Args:
                element: String the dictionary key assigned to the element 
        '''
        is_present = False
        
        if xpath is None:
            xpath = self._get_xpath(element)
        
        try:
            WebDriverWait(
                self.driver, wait
                ).until(EC.presence_of_element_located((By.XPATH, xpath))
                        )
            
            is_present = True
            
        except TimeoutException:
            is_present = False
            
            msg.showerror(
                self.selections.title, f'Timed out trying to load {element}.'
                )
            
        finally:
            return is_present
           
    
    def _run_report(self):
        # clicks on the report
        self._execute_javascript(self.report_type)
        
        if self._element_is_present(xpath=self.other_xpaths['tac_search']):
            # inputs the tac
            search_entry = self.driver.find_element_by_id('id_mstr56_txt')
            search_entry.send_keys(f'"{self.jurisdiction.tac}"')
            
            self._execute_javascript('tac_search')
            
            if self._tac_found():
                # clicks the ">" to select the tac
                add_button = self.driver.find_element_by_id('id_mstr60')
                add_button.click()
                    
                #===============================================================
                # # clicks the ">>" to select all the quarters
                # add_all_button = self.driver.find_element_by_id('id_mstr90')
                # add_all_button.click()
                #===============================================================
                   
                # inputs the city name to be added at the end of the report name
                name_entry = self.driver.find_element_by_id('id_mstr96_txt')
                name_entry.send_keys(self.output_file_name)
                   
                # clicks on "Run Report"
                run_button = self.driver.find_element_by_id('id_mstr97')
                run_button.click()
            
            else:
                msg.showerror(
                    self.selections.title, 
                    f'Failed to load tac: {self.jurisdiction.tac}.')
            
        
    def _tac_found(self):
        if self._element_is_present(
            xpath=self.other_xpaths['tac_selected'], wait=WAIT_FOR_TAC):
            
            try:
                tac_selected = self.driver.find_element_by_xpath(
                    self.other_xpaths['tac_selected'])
                
                if self.jurisdiction.tac in tac_selected.text:
                    tac_found = True
                    
                else:
                    tac_found = False
                    
            except NoSuchElementException:
                tac_found = False
            
        return tac_found
    
    
    def _wait_for_download(self):
        download_complete = False
        
        seconds_waited = 0
        
        while not download_complete and seconds_waited < WAIT_FOR_DOWNLOAD:
            time.sleep(CHECK_DOWNLOAD_INTERVAL)
            
            download_complete = self._download_complete()
            
            seconds_waited += CHECK_DOWNLOAD_INTERVAL
        
    
    def _download_complete(self):
        return any(
            self.output_file_name in str(path) and
            PARTIAL_DOWNLOAD_ID not in str(path)
            for path in Path(self.output_folder).iterdir())
        
        
    def _get_output_path(self):
        path = ''
        
        for file in Path(self.output_folder).iterdir():
            file = str(file)
            
            if self.output_file_name in file:
                path = file
        
        return path
        
       
    def _close(self):
        self.driver.close()
        self.driver.quit()
        
        
class LoginGui(tk.Toplevel):
    '''
        Toplevel window used to retrieve a username and password from 
        the user to log into the website where the data will be downloaded 
        from.
    '''
    
    
    WINDOW_WIDTH = 200
    WINDOW_HEIGHT = 120
    
    LBL_WIDTH = 10
    
    
    def __init__(self):
        super().__init__()
        
        self.username = ''
        self.password = ''
        
        self.closed = False
        
        self._center_window()
        self._make_widgets()
        
        self.bind('<Return>', self._on_continue_click)
        
        self.focus()
        self.user_ent.focus()
        
        
    def _center_window(self):
        x_offset = (self.winfo_screenwidth() - self.WINDOW_WIDTH) // 2
        y_offset = (self.winfo_screenheight() - self.WINDOW_HEIGHT) // 2
        
        self.geometry(
            f'{self.WINDOW_WIDTH}x{self.WINDOW_HEIGHT}+{x_offset}+{y_offset}'
            )
    
    
    def _make_widgets(self):
        main_frm = ttk.Frame(self)
        user_frm = ttk.Frame(main_frm)
        pass_frm = ttk.Frame(main_frm)
        button_frm = ttk.Frame(main_frm)
        
        user_lbl = ttk.Label(user_frm, text='Username:', width=self.LBL_WIDTH)
        self.user_ent = ttk.Entry(user_frm)
        
        pass_lbl = ttk.Label(pass_frm, text='Password:', width=self.LBL_WIDTH)
        self.pass_ent = ttk.Entry(pass_frm, show='*')
        
        cancel_btn = ttk.Button(
            button_frm, text='Cancel', command=self._on_cancel_click
            )
        
        continue_btn = ttk.Button(
            button_frm, text='Continue', command=self._on_continue_click
            )
        
        main_frm.pack(padx=constants.OUT_PAD)
        user_frm.pack(pady=constants.OUT_PAD)
        pass_frm.pack()
        button_frm.pack(pady=constants.OUT_PAD)
        
        user_lbl.pack(side='left')
        self.user_ent.pack(fill='x')
        
        pass_lbl.pack(side='left')
        self.pass_ent.pack(fill='x')
        
        cancel_btn.pack(side='left', padx=constants.OUT_PAD)
        continue_btn.pack()
        
        
    def is_closed(self):
        return self.closed
    
    
    def _on_cancel_click(self):
        self.destroy()
        
        self.closed = True
        
        
    def _on_continue_click(self, event=None):
        self.username = self.user_ent.get()
        self.password = self.pass_ent.get()
        
        self.destroy()
        
        self.closed = True
        
        
    def get_username(self):
        return self.username
    
    
    def get_password(self):
        return self.password
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    