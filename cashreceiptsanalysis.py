'''
Created on Apr 2, 2019

@author: vahidrogo
'''
'''
    REQUIREMENTS:
        1. Report title should say "City of ", "Town of " or 
            "County of ". County names can be left alone, for the city and 
            the town I can use the jurisdiction sub types table.
            
        2. Need 8 quarters
            - 6 quarters of quarter over quarter percentages
            - 2 periods of FYTD with amount and percent change
            2 periods of BMY with amount and percent change
            
        3. Need data for:
            - All cities in the county for the county the city is in
                - Also all the addons in the county
            - All counties for the region the county for the jurisdiction is 
            in
            - All smaller regions and the outer regions
                - the smaller regions have to be above the outer region
                they are in
                - Above Northern California is 
                    - Central Valley
                    - Central Coast
                    - North Coast
                    - Other Northern
                    - S.F. Bay Area
                    - Sacramento Valley
                    
                - Above Southern California
                    - Inland Empire
                    - Other Southern
                    - South Coast
                    
            - State total
            
        4. The following are highlighted:
            - The jurisdiction for which the report is for
            - The county the jurisdiction is in
            - The region the jurisdiction is in
            - Both of the outer regions
            - State total
            
        5. The following have asterisks:
            - The jurisdiction for which the report is for
            - The county the jurisdiction is in
            - The region the jurisdiction is in
            
        6. Pull data from table:
            - PROD_DW.stars.CountyCashFullwCnt_PY_R
        
'''

import xlsxwriter


DESCRIPTION = 'Sales Tax Net Cash Receipts: Three Advances Plus Clean-Up Payment'


class CashReceiptsAnalysis:
    '''
    '''
    
    
    def __init__(self, controller, selections):
        self.controller = controller
        self.selections = selections
        
        
    def main(self, jurisdiction):
        self.jurisdiction = jurisdiction
        print('Running CRA for', self.jurisdiction.name)