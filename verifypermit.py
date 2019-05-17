'''
Created on Jul 17, 2018

@author: vahidrogo
'''

from selenium import webdriver
from selenium.common.exceptions import *
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC   
from selenium.webdriver.support.ui import Select, WebDriverWait
import time
import tkinter as tk
from tkinter import messagebox as msg
from tkinter import ttk

from comboboxautocomplete import ComboboxAutoComplete
import constants
from tooltip import ToolTip
import utilities


class Controller():
    '''
    '''
    
    
    title = f'{constants.APP_NAME} - Verify Permit'
    default_business_code = '19 : SPECIALTY STORES'
    
    
    def __init__(self):
        self.page_loaded = False
        
        self.base_url = 'http://cdtfa.ca.gov'
        
        self.chrome_path = str(constants.APPS_PATH.joinpath('chromedriver.exe'))
       
        self.timeout = 5
         
        self.baseurl = 'http://cdtfa.ca.gov'
        
        self.xpaths = {
            'first_link' : '//span[@class="ca-gov-icon-check-list"]',
            'id_input' : '//input[@id="d-4"]',
            'type_select' : '//select[@id="d-3"]',
            'search_button' : '//button[@id="d-5"]'
            }
        
        # xpaths for each of the elements of the data to extract
        self.data_xpaths = {
            'DBA Name' : '//input[@id="f-6"]',
            'End Date' : '//input[@id="f-4"]',
            'Owner Name' : '//input[@id="f-5"]',
            'Start Date' : '//input[@id="f-3"]',
            }
        
        self._set_business_codes()
        
        self.gui = View(self, self.title)
        
        self._set_default_business_code()
        
        self._set_driver()
        
        
    def _set_driver(self):
        self.gui.results_message.set('Loading chromedriver')
        self.gui.update()
        
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--disable-gpu')
        
        self.driver = webdriver.Chrome(
            executable_path=self.chrome_path, chrome_options=chrome_options
            )
        
        self.gui.results_message.set('')
        self.gui.update()
        
        
    def _set_business_codes(self):
        self.business_codes = []
        
        query = f'''
            SELECT id, name
            FROM {constants.BUSINESS_CODES_TABLE}
            '''
        
        results = utilities.execute_sql(
            sql_code=query, db_name=constants.STARS_DB, fetchall=True
            )
        
        if results:
            self.business_codes = [f'{i[0]} : {i[1]}' for i in results]
            
            
    def _set_default_business_code(self):
        self.gui.business_code_id.set(self.default_business_code)
        
        
    def on_clean_names_click(self):
        self._clean_dba_name()
        self._clean_owner_name()
        
        
    def _clean_dba_name(self):
        name = self.gui.fields['DBA Name'].get().strip()
        
        if name:
            name = utilities.clean_business_name(name)
            
            # populates the gui entry with the cleaned name
            self.gui.fields['DBA Name'].set(name)
    
    
    def _clean_owner_name(self):
        name = self.gui.fields['Owner Name'].get().strip()
        
        if name:
            name = utilities.clean_business_name(name)
            
            # populates the gui entry with the cleaned name
            self.gui.fields['Owner Name'].set(name)
        
        
    def on_search_click(self, event=None):
        self.permit_number = self._get_permit_number()
        
        if self.permit_number:
            # displays formatted the matched permit number in the
            self.gui.permit_number.set(self.permit_number)
            self.gui.update()
              
            if self.page_loaded:
                self._verify_permit()
            else:
                self._load_page()
                self.gui.show_field_frame()
                self.gui.make_db_widgets()
        else:
            self.gui.permit_ent.focus()
            
            
    def _get_permit_number(self):
        '''
            Returns the formatted permit number if the pattern for the 
            permit number is found in the input text.
        '''
        permit_number = ''
        
        permit_input = self.gui.permit_number.get().strip()
        
        if permit_input:
            if utilities.is_valid_permit_number(permit_input):
                permit_number = utilities.format_permit_number(permit_input)
               
            else:
                msg.showerror(
                    self.title, 
                    f'Permit number must be of format: "{constants.PERMIT_FORMAT}".',
                    parent=self.gui
                    )
        
        return permit_number
           
           
    def _load_page(self):
        self.gui.results_message.set(self.base_url)
        self.gui.update()
        
        self.driver.get(self.baseurl)
        
        self.gui.results_message.set(
            'http://cdtfa.ca.gov/services/permits-licenses.htm'
            )
        self.gui.update()
        
        # first link
        self.driver.find_element_by_xpath(self.xpaths['first_link']).click()
        
        self.gui.results_message.set(
            'https://onlineservices.cdtfa.ca.gov/_/')
        self.gui.update()
        
        # link in the next page
        self.driver.find_element_by_link_text('verification webpage').click()
        
        element_present = EC.presence_of_element_located(
                (By.XPATH, self.xpaths['type_select']))
        
        # waits for the page to load to get the type select
        WebDriverWait(
            self.driver, self.timeout,
            ignored_exceptions=TimeoutException).until(element_present)
       
        if element_present:  
            self.type_select = Select(
                self.driver.find_element_by_xpath(
                    self.xpaths['type_select']))
             
            self.type_select.select_by_visible_text('Sellers Permit')

            self.page_loaded = True
            
            self._verify_permit()
        
        
    def _verify_permit(self):
        # these have to  be found each time the search button is clicked
        # otherwise they raise a element error
        self.id_input = self.driver.find_element_by_xpath(
            self.xpaths['id_input'])
        
        self.search_button = self.driver.find_element_by_xpath(
            self.xpaths['search_button'])
        
        # enter the permit number
        self.id_input.send_keys(self.permit_number)
        
        self.search_button.click()
        
        self._load_values()
            
            
    def _load_values(self):
        # waits for the values to be displayed
        time.sleep(0.3)
        
        for key, xpath in self.data_xpaths.items():
            value = self.driver.find_element_by_xpath(
                xpath).get_attribute('value')
                
            self.gui.fields[key].set(value)
            
        if self._no_values_found():
            self.gui.results_message.set(
                "This seller's permit does not exist.")
        else:
            if self._permit_is_closed():
                self.gui.results_message.set(
                    "This seller's permit has closed.")
            else:
                self.gui.results_message.set(
                    "This is a valid seller's permit.")
            
        self.gui.update()
        
        
    def _no_values_found(self):
        '''
            Returns TRUE if all the values in the fields are empty.
        '''
        return not any(value.get() for value in self.gui.fields.values())
        
        
    def _permit_is_closed(self):
        '''
            Returns TRUE if a value was found in the end date input.
        '''
        return bool(self.gui.fields['End Date'].get())
    
    
    def on_execute_click(self):
        permit_number = self._get_permit_number()
        
        if permit_number:
            business_code_id = self.gui.business_code_id.get()
            if business_code_id:
                business_code_id  = business_code_id.split(':')[0].strip()
                business_name = self._get_business_name()
                
                values = [business_name, business_code_id]
                
                # 1 for insert and 2 for alter
                execute_type = self.gui.execute_option.get()
                if execute_type == 1:
                    values.insert(0, permit_number) 
                    
                    sql_code = ('INSERT INTO '
                                'permits(id, business, business_code_id) '
                                'VALUES(?, ?, ?)')
                    
                    message = 'inserted'
                else:
                    values.append(permit_number)
                    
                    sql_code = ('UPDATE permits '
                                'SET business=?, business_code_id=? '
                                'WHERE id=?')
                    
                    message = 'altered'
                    
                executed = utilities.execute_sql(
                    sql_code=sql_code, args=values, db_name=constants.STARS_DB, 
                    dml=True, gui=self.gui
                    )
                 
                if executed:
                    self.gui.results_message.set(f'{permit_number} {message}.')
                     
                    self._clear_values()
                    
                    # resets the value of the business code widget to the default
                    self._set_default_business_code()
                    
                    # reset the execute option to "Insert"
                    self.gui.execute_option.set(1)
            else:
                msg.showerror(
                    self.title, 
                    'Please select a value for (business_code_id).',
                    parent=self.gui)
        else:
            self.gui.permit_ent.focus()
        
            
    def _get_business_name(self):
        # use the "DBA Name" as the primary name
        business_name = self.gui.fields['DBA Name'].get()
        
        if not business_name:
            # if the primary name is not found then use the "Owner Name"
            business_name = self.gui.fields['Owner Name'].get()
        
        return business_name
            
            
    def _clear_values(self):
        for value in self.gui.fields.values():
            value.set('')
        
        self.gui.permit_number.set('')
        self.gui.business_code_id.set('')
        self.gui.update()
        
        
    def close(self):
        self.gui.results_message.set('Closing chromedriver')
        self.gui.update()
        
        self.driver.close()
        self.driver.quit() 
        
        self.gui.destroy()
        
        
class View(tk.Toplevel):
    '''
    '''
    
    
    APP_HEIGHT = 300
    APP_WIDTH = 350
    
    
    def __init__(self, controller, title):
        super().__init__()
        
        self.controller = controller
        self.title = title
        
        self.protocol('WM_DELETE_WINDOW', self.controller.close)
        
        # prevents the user form changing the window height
        self.resizable(height=False)
        
        self.pad = 10
        self.ipad = self.pad//2
        self.lbl_w = 16
        self.ent_w = 40
        
        self.permit_number = tk.StringVar()
        self.results_message = tk.StringVar()
        self.business_code_id = tk.StringVar()
        
        self.execute_option = tk.IntVar()
        
        self._set_value_variables()
        
        self._set_style()
        
        self._window_setup()
        
        self._make_widgets()
        
        
    def _window_setup(self):
        self.wm_title(self.title)
        
        x_offset = (self.winfo_screenwidth() - int(self.APP_WIDTH)) // 2
        y_offset = (self.winfo_screenheight() - int(self.APP_HEIGHT)) // 2
        
        self.geometry(f'+{x_offset}+{y_offset}')
        
        
    def _set_style(self):
        bold_style = ttk.Style()
        bold_style.configure('bold.TLabel', font=('Arial', '8', 'bold'))
        
        
    def _set_value_variables(self):
        fields = [
            'Owner Name', 'DBA Name', 'Start Date', 'End Date'
            ]
        
        self.fields = {field : tk.StringVar() for field in fields}
        
        
    def _make_widgets(self):
        self.main_frm = ttk.Frame(self)
        self.main_frm.pack(fill='both', padx=self.pad)
        
        frm = ttk.Frame(self.main_frm)
        frm.pack(fill='x', pady=self.pad)
        
        lbl = ttk.Label(frm, text='Permit Number:', width=self.lbl_w)
        lbl.pack(anchor='w', side='left')
        
        self.permit_ent = ttk.Entry(
            frm, textvariable=self.permit_number, width=self.ent_w)
        
        # tooltip for the permit entry
        ToolTip(
            self.permit_ent, 
            f'Format: {constants.PERMIT_FORMAT}\n"-" is optional.'
            )
        
        self.permit_ent.pack(fill='x')
        
        self.permit_ent.bind('<Return>', self.controller.on_search_click)
        
        self.permit_ent.focus()
        
        self.msg_frm = ttk.Frame(self.main_frm)
        self.msg_frm.pack(fill='x')
        
        self.msg_lbl = ttk.Label(
            self.msg_frm, textvariable=self.results_message, 
            style='bold.TLabel')
        
        self.msg_lbl.pack(anchor='w', fill='x')
    
        self.field_frm = ttk.Frame(self.main_frm)
        self.field_frm.pack(fill='both')
        
        self.hidden_field_frm = ttk.Frame(self.field_frm)
        
        self._make_field_widgets()
        
        business_code_frm = ttk.Frame(self.hidden_field_frm)
        
        lbl = ttk.Label(
            business_code_frm, text='business_code_id:', width=self.lbl_w
            )
        
        business_code_cbo = ComboboxAutoComplete(
            parent=business_code_frm, textvariable=self.business_code_id,
            value_list=self.controller.business_codes
            )
        
        clean_names_btn = ttk.Button(
            self.hidden_field_frm, text='Clean Names', 
            command=self.controller.on_clean_names_click
            )
        
        self.bottom_frm = ttk.Frame(self.main_frm)
        self.db_frm = ttk.Frame(self.bottom_frm)
        
        business_code_frm.pack(fill='x', pady=self.ipad)
        lbl.pack(side='left')
        business_code_cbo.pack(fill='x')
        
        clean_names_btn.pack(anchor='e', pady=constants.IN_PAD)
        
        self.bottom_frm.pack(fill='x', pady=self.pad)
        self.db_frm.pack(side='left')
        
        self._make_button_widgets()
        
        
    def _make_field_widgets(self):
        for k, v in self.fields.items():
            frm = ttk.Frame(self.hidden_field_frm)
            frm.pack(fill='x', pady=self.ipad)
            
            lbl = ttk.Label(frm, text='{}:'.format(k), width=self.lbl_w)
            lbl.pack(anchor='w', side='left')
            
            ent = ttk.Entry(frm, textvariable=v)
            ent.pack(fill='x')
            
            
    def show_field_frame(self):
        '''
            Temporarily shows the frame that holds the fields that are 
            returned if a permit is found, it will be called if information
            for the permit is found.
        '''
        self.hidden_field_frm.pack(fill='both')
    
    
    def _make_button_widgets(self):
        frm = ttk.Frame(self.bottom_frm)
        frm.pack(anchor='e', side='bottom')
        
        btn = ttk.Button(
            frm, text='Search', command=self.controller.on_search_click)
        
        btn.pack(side='left', padx=self.pad)
        
        btn = ttk.Button(
            frm, text='Cancel', command=self.controller.close)
        
        btn.pack()
        
        
    def make_db_widgets(self):
        frm = ttk.Labelframe(self.db_frm, text='Permit Table')
        frm.pack()
        
        radio_btn = ttk.Radiobutton(
            frm, text='Insert', variable=self.execute_option, value=1)
        radio_btn.pack(anchor='w', padx=self.ipad)
        
        radio_btn = ttk.Radiobutton(
            frm, text='Alter', variable=self.execute_option, value=2)
        radio_btn.pack(anchor='w', padx=self.ipad)
        
        self.execute_option.set(1)
        
        btn = ttk.Button(
            frm, text='Execute', command=self.controller.on_execute_click)
        
        btn.pack(padx=self.ipad, pady=self.ipad)
        
        
        
        
        
        
        
