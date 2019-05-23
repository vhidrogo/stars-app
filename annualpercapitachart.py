'''
Created on May 23, 2019

@author: vahidrogo
'''

import xlsxwriter


class AnnualizedPerCapitaChart:
    '''
        Creates the "Annualized Per Capita by Economic Category" Excel chart.
    '''
    
    
    def __init__(self, controller, selections):
        self.controller = controller
        self.selections = selections
        
        self.output_path = ''
        
        self.jurisdiction = None
        
        
    def main(self, jurisdiction):
        self.jurisdiction = jurisdiction