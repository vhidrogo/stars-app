'''
Created on May 21, 2019

@author: vahidrogo
'''

import xlsxwriter

import utilities

OUTPUT_NAME = 'Annualized Growth by Economic Category'
OUTPUT_TYPE = 'xlsx'


class AnnualizedGrowthChart:
    '''
        Outputs the "Annualized Growth by Economic Category" Excel chart.
    '''
    
    
    def __init__(self, controller, selections):
        self.controller = controller
        self.selections = selections
        
        self.output_path = ''
        
        self.output_saved = False
        
        
    def main(self, jurisdiction):
        self.jurisdiction = jurisdiction
        
        self._set_output_path()
        self._output()
        
        if self.output_saved and self.selections.open_output:
            utilities.open_file(self.output_path)
        
        
    def _set_output_path(self):
        name = (
            f'{self.jurisdiction.id} {self.selections.period} {OUTPUT_NAME}'
            )
        
        self.output_path = f'{self.jurisdiction.folder}{name}.{OUTPUT_TYPE}'
        
        
    def _output(self):
        pass