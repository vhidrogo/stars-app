'''
Created on Jun 13, 2018

@author: vahidrogo
'''

import pythoncom
from tkinter import messagebox as msg
from win32com import client


class PdfConverter:
    '''
    '''
    
    
    def __init__(self):
        pythoncom.CoInitialize()
        self.word_app = client.DispatchEx('Word.Application')
        self.excel_app = client.DispatchEx('Excel.Application')
        self.powerpoint_app = client.DispatchEx('Powerpoint.Application')
        
        self.excel_app.DisplayAlerts = False
        self.excel_app.visible = False 
        
    
    def convert(self, input_file, output_file):
        file_type = input_file.rsplit('.', 1)[1].lower()
        if file_type in ['doc', 'docx', 'rtf']:
            self.from_word(input_file, output_file)
        elif file_type in ['xls', 'xlsx']:
            self.from_excel(input_file, output_file) 
        elif file_type in ['ppt', 'pptx']:
            self.from_powerpoint(input_file, output_file)
        else:
            msg.showwarning('Conversion Not Available', 
                            '{} cannot be converted to .pdf because {} '
                            'conversion is not currently supported.'
                            .format(input_file, file_type))
    
    def from_word(self, input_file, output_file):
        doc = self.word_app.Documents.Open(input_file)
        doc.SaveAs(output_file, FileFormat=17)
        doc.Close()
    
    def from_excel(self, input_file, output_file):
        wb = self.excel_app.workbooks.open(input_file)
        wb.ExportAsFixedFormat(0, output_file, 1, 0)
        wb.Close()
    
    def from_powerpoint(self, input_file, output_file):
        presentation = self.powerpoint_app.Presentations.Open(input_file)
        presentation.SaveAs(output_file, FileFormat=32)
        presentation.Close()
        
    def close(self):
        self.excel_app.Quit()
        self.word_app.Quit()
        self.powerpoint_app.Quit()