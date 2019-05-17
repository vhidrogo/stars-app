'''
Created on Dec 18, 2018

@author: vahidrogo
'''

import pandas as pd
import sqlite3 as sql
import threading
from tkinter import messagebox as msg

import constants
from progress import Progress
import utilities


class RollupTotals(threading.Thread):
    '''
        Parent class for SegmentTotals(), SegmentTotalsRegion(), 
        CategoryTotals() and CategoryTotalsRegion().
        
        Creates a new table with the data fetched using the query 
        set in each of the child classes.
    '''
    
    
    FIRST_QUARTER_COLUMN = 3
    

    def __init__(
            self, is_addon=False, is_category=True, is_region=False,
            is_business_code_totals=False
            ):
        super().__init__()
        
        self.is_addon = is_addon
        self.is_category = is_category
        self.is_region = is_region
        self.is_business_code_totals = is_business_code_totals
        
        self.title = constants.APP_NAME
        
        self.input_table_name = constants.BUSINESS_CODE_TOTALS_TABLE
        
        if self.is_addon:
            self.input_table_name += constants.ADDON_SUFFIX
        
        self.df = None
        
        self.query = ''
        self.rollup_id_name = ''
        self.rollup_table_name = ''
        
        
    def run(self):
        if self.is_addon:
            self.rollup_table_name += constants.ADDON_SUFFIX
         
        self.progress = Progress(self, self.title, abort=False)
         
        self.progress.update_progress(0, 'Fetching business code totals.')
         
        self._set_df()
         
        progress = 90 if self.is_region else 70
         
        self.progress.update_progress(progress, 'Preparing data.')
         
        if self.df is not None:
            # drops the old id column
            self.df.drop(constants.ID_COLUMN_NAME, axis=1, inplace=True)
            
            if not self.is_business_code_totals:
                # drops the business code id column
                self.df.drop(
                    constants.BUSINESS_CODE_ID_COLUMN_NAME, axis=1, inplace=True
                    )
              
            self._update_column_names()
              
            self._set_region_id_column()
              
            column_names = list(self.df)
              
            juri_column = (
                constants.REGION_ID_COLUMN_NAME if self.is_region 
                else constants.TAC_COLUMN_NAME
                )
                       
            # sets the columns that will be used in the table in the order 
            # that they will be in
            new_column_names = [
                constants.ID_COLUMN_NAME, juri_column, self.rollup_id_name
                ] + column_names[self.FIRST_QUARTER_COLUMN:]
            
            self.df = self.df[new_column_names]
                
            self._group_by_new_id()
              
            progress = 95 if self.is_region else 85
              
            self.progress.update_progress(progress, 'Creating table.')
                
            self._create_table()
              
            self.progress.update_progress(100, 'Build complete.')
            
        self.progress.destroy()
        
        
    def _set_df(self):
        sql_code = 'ATTACH DATABASE ? AS ?'
        
        args = (str(constants.DB_PATHS[constants.STARS_DB]), constants.STARS_DB)
        
        con = sql.connect(
            constants.DB_PATHS[constants.STATEWIDE_DATASETS_DB], uri=True,
            timeout=constants.DB_TIMEOUT
            )
           
        db_attached = utilities.execute_sql(
            sql_code=sql_code, args=args, open_con=con, dontfetch=True
            )
        
        if db_attached:
            results = utilities.execute_sql(
                sql_code=self.query, open_con=con, getcursor=True
                )
            
            if results:
                column_names = [i[0] for i in results.description]
                
                data = results.fetchall()
                
                self.df = pd.DataFrame(data, columns=column_names)
                
        con.close()
        
        
    def _update_column_names(self):
        column_names = list(self.df)
        
        # changes column to "id" from "new_id"
        column_names[0] = constants.ID_COLUMN_NAME
        
        if self.is_region:
            tac_index = 1 if self.is_business_code_totals else 2
            
            # changes column to "region_id" from "tac"
            column_names[tac_index] = constants.REGION_ID_COLUMN_NAME
        
        # updates the column names in the dataframe
        self.df.columns = column_names
        
        
    def _set_region_id_column(self):
        # gets the regions id's from the id column
        region_id_column = self.df[
            constants.ID_COLUMN_NAME
            ].apply(lambda x: x.split('-')[0])
            
        self.df[constants.REGION_ID_COLUMN_NAME] = region_id_column
        

    def _group_by_new_id(self):
        column_names = list(self.df)
        
        group_columns = column_names[:self.FIRST_QUARTER_COLUMN]
        
        sum_columns = column_names[self.FIRST_QUARTER_COLUMN:]
        
        self.df = self.df.groupby(
            group_columns, as_index=False, sort=False
            )[sum_columns].sum()
            
            
    def _create_table(self):
        con = sql.connect(
            constants.DB_PATHS[constants.STATEWIDE_DATASETS_DB], 
            timeout=constants.DB_TIMEOUT
            )
        
        try:
            with con:
                self.df.to_sql(
                    self.rollup_table_name, con, if_exists='replace', 
                    index=False
                    )
                
        except sql.OperationalError as e:
            msg.showerror(self.title, e)
            
        con.close()
            
            
class SegmentTotals(RollupTotals):
    '''
        Creates the "segment_totals" table in the "statewide_datasets"
        database. The table contains the amounts from the 
        "business_code_totals" table also in "statewide_datasets" rolled
        up by "segment_id". The "segment_id" comes from the "segments" 
        table in "starsdb" based on the "business_code_id" from the 
        "business_code_totals" table.
    '''
    

    def __init__(self, is_addon=False):
        super().__init__(is_addon)
         
        self.title += ' - Segment Totals'
         
        self.query = f'''
            SELECT d.{constants.TAC_COLUMN_NAME} || '-' || 
                    s.{constants.ID_COLUMN_NAME} new_id, 
                s.{constants.ID_COLUMN_NAME} {constants.SEGMENT_ID_COLUMN_NAME}, 
                d.* 
            
            FROM {self.input_table_name} d, 
                {constants.STARS_DB}.{constants.BUSINESS_CODES_TABLE} b, 
                {constants.STARS_DB}.{constants.SEGMENTS_TABLE} s
            
            WHERE d.{constants.BUSINESS_CODE_ID_COLUMN_NAME}
                    =b.{constants.ID_COLUMN_NAME}  
                AND b.{constants.SEGMENT_ID_COLUMN_NAME}
                    =s.{constants.ID_COLUMN_NAME} 
            '''
        
        self.rollup_id_name = constants.SEGMENT_ID_COLUMN_NAME
        
        self.rollup_table_name = 'segment_totals'
        
        self.start()
        
        
class SegmentTotalsRegion(RollupTotals):
    '''
        Creates the "segment_totals_region" table in the "statewide_datasets"
        database. The table contains the amounts from the 
        "business_code_totals" table also in "statewide_datasets" rolled up by
        "segment_id" and "region_id". The "segment_id" comes from the 
        "segments" table in "starsdb" based on the "business_code_id" from the 
        "business_code_otals" table. The "region_id" comes from the 
        "jurisdictions" table also in "starsdb".
    '''
    

    def __init__(self):
        super().__init__(is_region=True)
         
        self.title += ' - Segment Totals Region'
        
        self.query = f'''
            SELECT c.region_id || '-' || 
                    s.{constants.ID_COLUMN_NAME} new_id, 
                s.{constants.ID_COLUMN_NAME} {constants.SEGMENT_ID_COLUMN_NAME}, 
                d.*
                 
            FROM {self.input_table_name} as d, 
                {constants.STARS_DB}.{constants.BUSINESS_CODES_TABLE} b, 
                {constants.STARS_DB}.{constants.COUNTIES_TABLE} c,
                {constants.STARS_DB}.{constants.SEGMENTS_TABLE} s,
                {constants.STARS_DB}.{constants.JURISDICTIONS_TABLE} j
                
            WHERE d.{constants.BUSINESS_CODE_ID_COLUMN_NAME}
                    =b.{constants.ID_COLUMN_NAME}
                AND b.{constants.SEGMENT_ID_COLUMN_NAME}
                    =s.{constants.ID_COLUMN_NAME}
                AND d.{constants.TAC_COLUMN_NAME}
                    =j.{constants.TAC_COLUMN_NAME}
                AND j.{constants.COUNTY_ID_COLUMN_NAME}
                    =c.{constants.ID_COLUMN_NAME}
            '''
        
        self.rollup_id_name = constants.SEGMENT_ID_COLUMN_NAME
          
        self.rollup_table_name = 'segment_totals_region'
          
        self.start()
        
        
class CategoryTotals(RollupTotals):
    '''
        Creates the "category_totals" table in the "statewide_datasets"
        database. The table contains the amounts from the 
        "business_code_totals" table also in "statewide_datasets" rolled up by
        "category_id". The "category_id" comes from the "segments" table in 
        "starsdb" based on the "segment_id" that comes from the "business_codes" 
        table also in "starsdb". The "segment_id" is based on the 
        "business_code_id" in the "business_code_totals" table.
    '''
    
    
    def __init__(self, is_addon=False):
        super().__init__(is_addon, is_category=True)
         
        self.title += ' - Category Totals'
         
        self.query = f'''
            SELECT d.{constants.TAC_COLUMN_NAME} || '-' || 
                    c.{constants.ID_COLUMN_NAME} as new_id, 
                c.{constants.ID_COLUMN_NAME} as 
                    {constants.CATEGORY_ID_COLUMN_NAME}, d.* 
            
            FROM {self.input_table_name} as d, 
                {constants.STARS_DB}.{constants.BUSINESS_CODES_TABLE} as b, 
                {constants.STARS_DB}.{constants.CATEGORIES_TABLE} as c, 
                {constants.STARS_DB}.{constants.SEGMENTS_TABLE} as s 
            
            WHERE d.{constants.BUSINESS_CODE_ID_COLUMN_NAME}
                    =b.{constants.ID_COLUMN_NAME}
                AND b.{constants.SEGMENT_ID_COLUMN_NAME}
                    =s.{constants.ID_COLUMN_NAME} 
                AND s.{constants.CATEGORY_ID_COLUMN_NAME}
                    =c.{constants.ID_COLUMN_NAME}
            '''
         
        self.rollup_id_name = constants.CATEGORY_ID_COLUMN_NAME
        
        self.rollup_table_name = 'category_totals'
         
        self.start()
        
        
class CategoryTotalsRegion(RollupTotals):
    '''
        Creates the "category_totals_region" table in the "statewide_datasets"
        database. The table contains the amounts from the 
        "business_code_totals" table also in "statewide_datasets" rolled up 
        by "category_id" and "region_id". The "category_id" comes from the 
        "segments" table in "starsdb" based on the "segment_id" that comes 
        from the "business_codes" table also in "starsdb". The "segment_id" 
        is based on the "business_code_id" in the "business_code_totals" 
        table. The "region_id" comes from the "jurisdictions" table in 
        "starsdb".  
    '''
    
    
    def __init__(self):
        super().__init__(is_region=True)
         
        self.title += ' - Category Totals Region'
        
        self.query = f'''
            SELECT co.region_id || '-' || 
                    c.{constants.ID_COLUMN_NAME} new_id, 
                c.{constants.ID_COLUMN_NAME} {constants.CATEGORY_ID_COLUMN_NAME}, 
                d.* 
            
            FROM {self.input_table_name} d, 
                {constants.STARS_DB}.{constants.BUSINESS_CODES_TABLE} b, 
                {constants.STARS_DB}.{constants.COUNTIES_TABLE} co,
                {constants.STARS_DB}.{constants.CATEGORIES_TABLE} c, 
                {constants.STARS_DB}.{constants.SEGMENTS_TABLE} s, 
                {constants.STARS_DB}.{constants.JURISDICTIONS_TABLE} j
            
            WHERE d.{constants.BUSINESS_CODE_ID_COLUMN_NAME}
                    =b.{constants.ID_COLUMN_NAME} 
                AND b.{constants.SEGMENT_ID_COLUMN_NAME}
                    =s.{constants.ID_COLUMN_NAME} 
                AND s.{constants.CATEGORY_ID_COLUMN_NAME}
                    =c.{constants.ID_COLUMN_NAME}
                AND d.{constants.TAC_COLUMN_NAME}
                    =j.{constants.TAC_COLUMN_NAME}
                AND j.{constants.COUNTY_ID_COLUMN_NAME}
                    =co.{constants.ID_COLUMN_NAME}
            '''
        
        self.rollup_id_name = constants.CATEGORY_ID_COLUMN_NAME
         
        self.rollup_table_name = 'category_totals_region'
          
        self.start()
        
        
class BusinessCodeTotalsRegion(RollupTotals):
    '''
        Creates the "business_code_totals_region" table in the 
        "statewide_datasets" database. The table contains the amounts from 
        the "business_code_totals" table also in the "statewide_datasets" 
        rolled up by "region_id". The "region_id" comes form the 
        "jurisdictions" table in "starsdb".
    '''
    
    
    def __init__(self):
        super().__init__(is_region=True, is_business_code_totals=True)
        
        self.title += ' - Business Code Totals Region'
        
        self.query = f'''
            SELECT co.region_id || '-' || 
                    d.{constants.BUSINESS_CODE_ID_COLUMN_NAME} new_id, 
                d.* 
            
            FROM {self.input_table_name} d, 
                {constants.STARS_DB}.{constants.COUNTIES_TABLE} co,
                {constants.STARS_DB}.{constants.JURISDICTIONS_TABLE} j
            
            WHERE d.{constants.TAC_COLUMN_NAME}
                    =j.{constants.TAC_COLUMN_NAME}
                AND j.{constants.COUNTY_ID_COLUMN_NAME}
                    =co.{constants.ID_COLUMN_NAME}
            '''
        
        self.rollup_id_name = constants.BUSINESS_CODE_ID_COLUMN_NAME
        
        self.rollup_table_name = 'business_code_totals_region'
        
        self.start()
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
        
