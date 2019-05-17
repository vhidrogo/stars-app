'''
Created on Oct 9, 2018

@author: vahidrogo
'''


class BusinessLevelAdjustments:
    def __init__(self, controller, selections):
        self.controller = controller
        self.selections = selections
        
        self.jurisdiction = None
    
    
    def main(self, jurisdiction):
        self.jurisdiction = jurisdiction
        
        print('Running adjustments for', self.jurisdiction.name)