'''
Created on Apr 10, 2018

@author: vahidrogo
'''

import ntpath
from pathlib import Path
import re
from tkinter import messagebox as msg
from tkinter import filedialog

import PyPDF2
from pdfrw import PdfReader
from pdfrw.buildxobj import pagexobj
from pdfrw.toreportlab import makerl

from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas
from win32com import client

import constants
from jurisdiction import Jurisdiction
from pdfconverter import PdfConverter
import utilities


class Report():
    '''
        Data class for report attributes.
    '''
    
    
    def __init__(self, args):
        self.id = args[0]
        self.name = args[1]
        self.path = args[2]
        self.is_duplex = args[3]
        
        self.convert_to_pdf = False
        
        self.pdf_path = ''
        self.print_path = ''
        
        self.pdf_pages = []
 
       
class CompilePacket:
    '''
    '''
    
    
    pdfmetrics.registerFont(
        TTFont('Calibri', constants.FONTS_PATH.joinpath('Calibri.ttf'))
        )
         
    pdfmetrics.registerFont(
        TTFont('CalibriBd', constants.FONTS_PATH.joinpath('CalibriBd.ttf'))
        )
    
    output_type = 'pdf'
    
    print_file_suffix = '_print'
    
    blank_cover_path = constants.APP_FILES_PATH.joinpath('packet_cover.pdf')
    blank_pdf_path = constants.APP_FILES_PATH.joinpath('blank_page.pdf')
    
    check_files_ids = {
        'adjustments' : 15, 'browsed' : 16, 'cover' : 1, 'forecast' : 14
        }
    
    output_names = {
        'Client by Rep' : 'Reports',
        'Client Standard' : 'Reports',
        'Custom Standard' : 'Reports Custom',
        'Custom by Rep' : 'Reports Custom',
        'Liaison Standard' : 'Liaison Reports',
        'Liaison by Rep' : 'Liaison Reports',
        }
    
    # id assigned to "All" in starsdb.reps
    ALL_REPS_ID = 12
    
    # id assigned to "All" in starsdb.JurisdictionTypes
    ALL_JURISDICTION_TYPES_ID = 0
    
    
    def __init__(self, controller):
        self.controller = controller
        self.selections = self.controller.selections
        
        self._set_packet_type_id()
        
        if self.packet_type_id:
            # flags that indicate whether each of the files that need to be checked 
            # are being included in the packet
            self.check_files_included = {i : False for i in self.check_files_ids}
            
            self.addon_ids = []
            self.missing_files = []
            self.selected_reports = []
            self.selected_report_attributes = []
            self.selected_report_ids = []
            
            self.output_path = ''
            self.output_path_print = ''
            self.packet_type = ''
            
            self.output_name = self.output_names[self.selections.type_option]
            
            self.is_liaison = ('Liaison' in self.selections.type_option)
            
            self.create_print_file = False
            
            self.total_pages = 0
            
            self.blank_pdf_page = pagexobj(PdfReader(self.blank_pdf_path).pages[0])
                
            self.pdf_converter = PdfConverter()
                
            self._open_excel()
        
        
    def _set_packet_type_id(self):
        self.packet_type_id = None
        
        query = f'''
            SELECT Id
            FROM {constants.PACKET_TYPES_TABLE}
            WHERE name=?
            '''
        
        args = (self.selections.type_option, )
        
        results = utilities.execute_sql(
            sql_code=query, args=args, db_name=constants.STARS_DB
            )
        
        if results:
            self.packet_type_id = results[0]
            
        else:
            msg.showinfo(
                self.selections.title, 
                f'No record found for {self.selections.type_option} in '
                f'{constants.PACKET_TYPES_TABLE}.'
                )
    
    
    def _open_excel(self):
        self.excel_app = client.DispatchEx('Excel.Application')
        self.excel_app.DisplayAlerts = False
        self.excel_app.visible = False
        
        
    def _cleanup(self):
        self.excel_app.Quit()
        self.pdf_converter.close()
        
        
    def main(self, jurisdiction):
        if self.packet_type_id:
            self.jurisdiction = jurisdiction
            
            if self.is_liaison and self.jurisdiction.type == 'addon':
                msg.showinfo(
                    self.selections.title,
                    'Liaison Packets have not been implemented for addons. '
                    'The Business Level Adjustments for addons are included '
                    'in the jurisdiction liaison packet.'
                    )
            else:
                self._set_selected_report_ids()
                
                if self.selected_report_ids:
                    self._set_selected_report_attributes()
                    
                    self._set_selected_reports()
                    
                    if self.selected_reports:
                        self._set_check_files_included()
                        
                        if self.check_files_included['forecast']:
                            path = self._get_forecast_path()
                            
                            self._set_path(
                                self.check_files_ids['forecast'], path
                                )
                            
                        if (
                            self.check_files_included['adjustments'] and 
                            self.jurisdiction.has_addon
                            ):
                                
                            self._set_addon_ids()
                            
                            self._set_addon_adjustment_reports()
                        
                        self._set_report_paths()
 
                        if self.missing_files:
                            self._write_missing_files_txt()
                                
                        else:
                            if not self.selections.pdf_only:
                                self.create_print_file = any(
                                    i.is_duplex for i in self.selected_reports
                                    )
                                  
                            if self.check_files_included['cover']:    
                                self._make_cover()
                                  
                            self._set_pdf_paths()
                                  
                            if self.check_files_included['adjustments']:
                                self._get_adj_first_page()
                                  
                            self.controller.update_progress(
                                5, f'{self.jurisdiction.id}: Converting reports to PDF.'
                                )
                                     
                            self._convert_to_pdf()
                                  
                            self._set_output_paths()
                                                             
                            if not self.is_liaison:  
                                self.controller.update_progress(
                                    15, f'{self.jurisdiction.id}: Processing PDF reports.'
                                    )
                                       
                                self._set_pdf_pages()
                                       
                                self._set_total_pages()
                                       
                                self.controller.update_progress(
                                    15, f'{self.jurisdiction.id}: Finalizing PDF reports.'
                                    )
                                        
                                self._create_pdfs()
                                       
                                if self.create_print_file:
                                    self.controller.update_progress(
                                    20, f'{self.jurisdiction.id}: Merging print PDF file.'
                                    )
                                           
                                    self._merge_pdf(print_file=True) 
                                           
                                    if self.selections.open_output:
                                        utilities.open_file(self.output_path_print)
                                               
                            progress = 80 if self.create_print_file else 70
                                   
                            self.controller.update_progress(
                                progress, 
                                f'{self.jurisdiction.id}: Merging reports PDF file.'
                                )
                                       
                            self._merge_pdf()
                                 
                            self.controller.update_progress(
                                100, f'{self.jurisdiction.id}: Completed.'
                                )
                                   
                            if self.selections.open_output and not self.create_print_file:
                                utilities.open_file(self.output_path)
                
            self._cleanup()
        

    def _set_selected_report_ids(self):
        # all "Standard" packet report selections have rep_id equal to 
        # that of rep "All" in starsdb.reps
        rep_id = (
            self.ALL_REPS_ID if 'Standard' in self.selections.type_option 
            else self.jurisdiction.rep_id
            )
        
        jurisdiction_type_id = (
            self.ALL_JURISDICTION_TYPES_ID 
            if 'Custom' in self.selections.type_option or
            'Liaison' in self.selections.type_option else
            self.jurisdiction.type_id
            )
        
        # construct the Id value to look in starsdb.PacketSelectedReports
        # it is made up of the PacketTypeId, JurisdictionTypeId and RepId 
        # separated by "-"
        key_value = '-'.join(
            str(i) for i in 
            (self.packet_type_id, jurisdiction_type_id, rep_id)
            )
        
        query = f'''
            SELECT * 
            FROM {constants.PACKET_REPORT_SELECTIONS_TABLE}
            WHERE Id=?
            '''
        
        results = utilities.execute_sql(
            sql_code=query, args=(key_value, ), db_name=constants.STARS_DB
            )
        
        if results:
            # first report id column is at index 4, report id 0 is None
            self.selected_report_ids = tuple(i for i in results[4:] if i) 
            
        else:
            msg.showinfo(
                self.selections.title, 
                f'No record found for Id={key_value} in '
                f'{constants.PACKET_REPORT_SELECTIONS_TABLE}.'
                )
            
            
    def _set_selected_report_attributes(self):
        condition = (
            f'={self.selected_report_ids[0]}' 
            if len(self.selected_report_ids) == 1 
            else f'IN {self.selected_report_ids}'
            )
        
        query = (
            f'SELECT Id, Name, Path, IsDuplex '
            f'FROM {constants.PACKET_REPORTS_TABLE} '
            f'WHERE Id {condition}'
            )
        
        results = utilities.execute_sql(
            sql_code=query, db_name=constants.STARS_DB, fetchall=True
            )
      
        if results:
            # adds the attributes to the list of selected report attributes 
            # according to the order of the selected report ids
            for attributes in results:
                report_id = attributes[0]
                
                if self.selected_report_attributes:
                    index = self._get_selected_report_attributes_index(report_id)
                    
                    if index < len(self.selected_report_attributes):
                        self.selected_report_attributes.insert(index, attributes)
                        
                    else:
                        self.selected_report_attributes.append(attributes)
                
                else:
                    self.selected_report_attributes.append(attributes)
                    
                    
    def _get_selected_report_attributes_index(self, report_id):
        index = self.selected_report_ids.index(report_id)
        
        for i, attributes in reversed(list(enumerate(self.selected_report_attributes))):
            # report_id is the first item in the tuple of attributes
            existing_index = self.selected_report_ids.index(attributes[0])
            
            if index <= existing_index:
                index = i
            else:
                break
            
        return index
        

    def _set_selected_reports(self):
        if self.selections.exclude_files:
            name_position = 1
            
            report_names = [
                i[name_position] for i in self.selected_report_attributes
                ]
            
            txt_file = (f'{self.packet_type.capitalize()} Packet Files')
            
            exclude_files = utilities.get_excluded_from_text_file(
                txt_file, report_names, self.jurisdiction
                )
            
            if exclude_files:
                self.selected_report_attributes = [
                    i for i in self.selected_report_attributes 
                    if i[name_position] not in exclude_files
                    ]
        
        for x in self.selected_report_attributes:
            report = Report(x)
            
            # sets all reports other the cover to double sided for Tracy's packets
            if self.jurisdiction.rep_name == 'Tracy Vesely' and report.name != 'Cover':
                report.is_duplex = 1
            
            self.selected_reports.append(report)
    
    
    def _set_check_files_included(self):
        '''
            Sets the flag to True for each of the files that need to be 
            checked if they are being included in the packet.
        '''
        for i in self.check_files_included:
            self.check_files_included[i] = any(
                self.check_files_ids[i] == r.id for r in self.selected_reports
                )
    
    
    def _get_forecast_path(self):
        '''
            Returns the path of the most current forecast file if one
            exists.
        '''
        forecast_path = ''
        
        pattern = f'{self.selections.period} Forecast v'
         
        forecast_paths = []
        
        for path in Path(self.jurisdiction.folder).iterdir():
            path = str(path)
            
            if re.search(pattern, path) and self.output_type in path:
                forecast_paths.append(path)
              
        if forecast_paths:
            if len(forecast_paths) == 1:
                forecast_path = forecast_paths[0]
            
            else:
                current_path = forecast_paths[0]
                current_version = 1
                
                for i in forecast_paths:
                    version = int(i[i.index(pattern)+len(pattern)])
                    
                    if version >= current_version:
                        current_path = i
                        current_version = version
                        
                forecast_path = current_path
                
        return forecast_path
    
    
    def _set_path(self, report_id, path):
        for i in self.selected_reports:
            if i.id == report_id:
                i.path = path
                break
            
            
    def _set_addon_ids(self):
        query = (
            f'SELECT {constants.ID_COLUMN_NAME} '
            f'FROM {constants.ADDONS_TABLE} '
            f'WHERE JurisdictionId=?'
            )
        
        results = utilities.execute_sql(
            sql_code=query, args=(self.jurisdiction.id, ), 
            db_name=constants.STARS_DB, fetchall=True
            )
        
        if results:
            if len(results) == 1:
                results = results[0]
                
            for i in results:
                self.addon_ids.append(i)
                
                
    def _get_report_specific_path(self, path, jurisdiction):
        '''
            Returns the path after replacing the generic place holders.
        '''
        changes = {
            '{folder}' : jurisdiction.folder,
            '{jurisdiction_id}' : self.jurisdiction.id,
            '{quarter}' : self.selections.quarter,
            '{year}' : self.selections.year
            }
        
        for old, new in changes.items():
            path = path.replace(old, str(new))
            
        return path
            
            
    def _set_addon_adjustment_reports(self):
        if self.addon_ids:
            report_attributes = self._get_adjustments_report_attributes()
            
            path = report_attributes[2]
             
            for i in self.addon_ids:
                addon = Jurisdiction(jurisdiction_id=i)
                
                addon_path = self._get_report_specific_path(path, addon)
                
                report = Report(report_attributes)
                 
                report.path = addon_path
                 
                self.selected_reports.append(report)
                
                
    def _get_adjustments_report_attributes(self):
        report_id = self.check_files_ids['adjustments']
        
        query = f'''
            SELECT Id, Name, Path, IsDuplex
            FROM {constants.PACKET_REPORTS_TABLE}
            WHERE Id=?
            '''
        
        args = (report_id, )
        
        return utilities.execute_sql(
            sql_code=query, args=args, db_name=constants.STARS_DB
            )
                
                
    def _set_report_paths(self):
        for i in self.selected_reports:
            path = i.path
            
            if path not in ['app_files', 'None']:
                if path == 'browsed':
                    i.path = filedialog.askopenfilename(
                        initialdir=self.jurisdiction.folder)
                    
                else:
                    path = self._get_report_specific_path(
                        path, self.jurisdiction
                        )
                    
                    if not path or not Path(path).exists():
                        name = i.name
                        
                        self.missing_files.append(
                            '{:30}- {}'.format(name, path)
                            )
                        
                    else:
                        i.path = path
                        
                        
    def _write_missing_files_txt(self):
        name = f'{self.jurisdiction.id} Missing Files.txt'
        
        path = str(constants.TEMP_FILE_PATH.joinpath(name))
        
        with open(path, 'w+') as file:
            for i in self.missing_files:
                file.write(f'{i}\n')
                
        utilities.open_file(path)
        
        
    def _make_cover(self):
        name = f'{self.jurisdiction.id}_packet_cover.pdf'
        
        path = str(constants.TEMP_FILE_PATH.joinpath(name))
        
        reader = PdfReader(self.blank_cover_path)
        page = pagexobj(reader.pages[0])
        
        canvas = Canvas(path, pagesize=letter)
        canvas.setPageSize((page.BBox[2], page.BBox[3]))
        canvas.doForm(makerl(canvas, page))
        canvas.saveState()
         
        max_title_len = 15
        max_title_font_size = 60
        max_title_pixel = max_title_len * max_title_font_size
        
        x = 15
        
        mid_x = x//2
        
        y1 = 15
        
        fs1 = 16
        y2 = y1 + mid_x + fs1
        
        fs2 = 36
        y3 = y2 + mid_x + fs2
        
        fs3 = max_title_font_size
        
        title = self.jurisdiction.name
        
        rep_info = self._get_rep_info()
        
        # draws the email and phone of the rep   
        canvas.setFontSize(fs1)
        canvas.setFillGray(0.45) 
        canvas.drawString(x=x, y=y1, text=f'{rep_info[0]} | {rep_info[1]}')
           
        canvas.setFont('Calibri', fs2)
        canvas.drawString(
            x=x, y=y2, text=f'Economic Review {self.selections.period}')
           
        canvas.setFillColorRGB(0, .23, .34)
        if len(title) > max_title_len:
            fs3 = max_title_pixel//len(title)
           
        canvas.setFontSize(fs3)
        canvas.drawString(x=x, y=y3, text=title)
           
        canvas.restoreState()
        canvas.showPage()       
        canvas.save()
        
        self._set_path(self.check_files_ids['cover'], path)
        
        
    def _get_rep_info(self):
        query = f'''
            SELECT email, phone 
            FROM {constants.REPS_TABLE} 
            WHERE id=?
            '''
        
        rep_info = utilities.execute_sql(
            sql_code=query, args=(self.jurisdiction.rep_id, ),
            db_name=constants.STARS_DB
            )
        
        return rep_info
    
    
    def _set_pdf_paths(self):
        for i in self.selected_reports:
            path = i.path
            
            name = ntpath.basename(path).rsplit('.', 1)[0]
            
            file_type = path.rsplit('.', 1)[1] 
            
            pdf_path = str(
                constants.TEMP_FILE_PATH.joinpath(
                    f'{name}.{self.output_type}'
                    )
                )
         
            if file_type != self.output_type:
                i.convert_to_pdf = True
            
            i.pdf_path = pdf_path
            
            if self.create_print_file:
                print_path = str(
                    constants.TEMP_FILE_PATH.joinpath(
                        f'{name}{self.print_file_suffix}.{self.output_type}'
                        )
                    )
                
                i.print_path = print_path
                
                
    def _get_adj_first_page(self):
        # Saves the first page of the adjustments as a PDF into the 
        # temporary file folder.
        for i in self.selected_reports:
            if i.id == self.check_files_ids['adjustments']:
                wb = self.excel_app.Workbooks.Open(i.path)
                
                wb.WorkSheets(1).ExportAsFixedFormat(0, i.pdf_path)
                wb.Close()
                
                i.path = i.pdf_path
                
                i.convert_to_pdf = False
                
                
    def _convert_to_pdf(self):
        for i in self.selected_reports:
            if i.convert_to_pdf:
                self.pdf_converter.convert(i.path, i.pdf_path)
                
                i.path = i.pdf_path
                
                
    def _set_output_paths(self):
        name = (
            f'{self.jurisdiction.id} {self.selections.period} '
            f'{self.output_name}'
            )
        
        if self.addon_ids:
            id_string = self._get_jurisdiction_id_string()
            
            name = name.replace(self.jurisdiction.id, id_string)
        
        path = self.jurisdiction.folder + name
        
        if not self.selections.pdf_only:
            path_print = f'{path}{self.print_file_suffix}'
            
            self.output_path_print = f'{path_print}.{self.output_type}'
            
        self.output_path = f'{path}.{self.output_type}'
     
     
    def _get_jurisdiction_id_string(self):
        ids = [self.jurisdiction.id]
        
        ids.extend(self.addon_ids)
        
        return ' '.join(ids)
    
    
    def _set_pdf_pages(self):
        '''
            Stores all the pages of each PDF as page objects.
        '''
        for i in self.selected_reports:
            i.pdf_pages = [
                pagexobj(p) for p in PdfReader(i.path).pages
                ]
                
                
    def _set_total_pages(self):
        self.total_pages = sum([len(i.pdf_pages) for i in self.selected_reports])
    
          
    def _create_pdfs(self):
        total_pg_num = 2
        for report in self.selected_reports:
            canvas = Canvas(report.pdf_path)
            
            if self.create_print_file:
                canvas_print = Canvas(report.print_path)
            
            for pg_num, pg in enumerate(report.pdf_pages, start=1):
                canvas.setPageSize((pg.BBox[2], pg.BBox[3]))
                canvas.doForm(makerl(canvas, pg))
                
                if self.create_print_file:
                    canvas_print.setPageSize((pg.BBox[2], pg.BBox[3]))
                    canvas_print.doForm(makerl(canvas_print, pg))
                    
                if report.id != self.check_files_ids['cover']:
                    footer = f'Page {total_pg_num} of {self.total_pages}'
                    
                    canvas.saveState()
                    canvas.setFont('Calibri', 12)
                    canvas.drawCentredString(pg.BBox[2]//2, 15, footer)
                    canvas.restoreState()
                    
                    if self.create_print_file:
                        canvas_print.saveState()
                        canvas_print.setFont('Calibri', 12)
                        canvas_print.drawCentredString(pg.BBox[2]//2, 15, footer)
                        canvas_print.restoreState()
                        
                    total_pg_num += 1
                    
                canvas.showPage()
                
                if self.create_print_file:
                    canvas_print.showPage()
                
                # if the print file is being created and the report is 
                # doubled sided and it's not the last page or its the last 
                # page of the report and the report is double sided and 
                # that report has an odd number of pages then a blank page 
                # is inserted after this page to allow for mixed single and 
                # double sided printing when printing the document in double sided mode
                if self.create_print_file: 
                    if (
                        (not report.is_duplex and total_pg_num <= self.total_pages)
                        or
                        (
                        pg_num == len(report.pdf_pages) and 
                        report.is_duplex and len(report.pdf_pages) % 2 != 0
                        )
                        ):
                        
                        # inserts the blank page
                        canvas_print.setPageSize((pg.BBox[2], pg.BBox[3]))
                        canvas_print.doForm(
                            makerl(canvas_print, self.blank_pdf_page))
                        canvas_print.showPage()
                
            canvas.save()
            
            if self.create_print_file:
                canvas_print.save()
                
            
    def _merge_pdf(self, print_file=False):
        merger = PyPDF2.PdfFileMerger()
        
        for i in self.selected_reports:
            path = i.print_path if print_file else i.path
            
            merger.append(PyPDF2.PdfFileReader(path, 'rb'), i.name)
            
        output_path = (
            self.output_path_print if print_file else self.output_path
            )
            
        try_to_save = True
        while try_to_save:
            try:
                merger.write(output_path)
                try_to_save = False
                
            except PermissionError:
                retry = msg.askretrycancel(
                    self.selections.title, 
                    f'Could not save file to ({output_path}) because there is '
                    'a file with that name currently open. To continue, '
                    'close the file and retry.')
                
                if not retry:
                    try_to_save = False
                    
                    
    
        
        
    
