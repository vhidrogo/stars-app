'''
Created on Apr 23, 2019

@author: vahidrogo
'''

import numpy as np
import pandas as pd
import sqlite3 as sql
import threading
from tkinter import messagebox as msg
import traceback

import constants
from progress import LoadingCircle
import utilities


PERIOD_COUNT = 8

JURI_TYPE_COL = 'jurisdiction_type'

GROUP_NAME_COL = 'group_name'
GROUP_TYPE_COL = 'group_type'

JURISDICTION_COL = 'jurisdiction_name'

QTR_AMT_CHG_COL = 'qoq_amt_chg'
QTR_PCNT_CHG_COL = 'qoq_%_chg'
YR_AMT_CHG_COL = 'yoy_amt_chg'
YR_PCNT_CHG_COL = 'yoy_%_chg'

RANK_COL = constants.YEAR_COLUMN_PREFIX + 'rank'
GAIN_RANK_COL = constants.QUARTER_COLUMN_PREFIX + 'gain_rank'
DECLINE_RANK_COL = constants.QUARTER_COLUMN_PREFIX + 'decline_rank'

RANK_COL = constants.YEAR_COLUMN_PREFIX + 'rank'

PCNT_OF_TOT_COL = constants.YEAR_COLUMN_PREFIX + '%_of_tot'

CAT_TYPE = 'cat'
SEG_TYPE = 'seg'
TOT_TYPE = 'tot'

JURI_TYPE = 'city/town/county'
REGION_TYPE = 'region'
OUTER_REGION_TYPE = 'outer_region'
STATE_TYPE = 'state'

OTHER_TYPE = 'other'

OTHER_GROUP = 'MISC/OTHER'

TOT_GROUP = 'TOTAL'

NORCAL_NAME = 'NORTHERN CALIFORNIA'
SOCAL_NAME = 'SOUTHERN CALIFORNIA'
STATE_NAME = 'CALIFORNIA STATEWIDE'

IS_SOUTHERN_COL = 'is_southern'

OTHER_CATEGORIES = ('TRANSPORTATION', 'MISCELLANEOUS')

RANK_GROUP_COLS = [GROUP_TYPE_COL, JURISDICTION_COL]

TITLE = f'{constants.APP_NAME} - Econ Totals'


class EconTotals(threading.Thread):
    '''
    '''
    

    def __init__(self, window, period):
        super().__init__()
        
        self.loading_circle = LoadingCircle(window, 'Exporting')
        self.loading_circle.start()
        
        self.period = period
        
        self.con = None
        self.df = None
        self.output_saved = False
        
        self.output_path = constants.TEMP_FILE_PATH.joinpath(
            f'{self.period} Econ Totals.xlsx'
            )
        
        self.period_cols = utilities.get_period_headers(
            count=PERIOD_COUNT, 
            period=self.period,
            prefix=constants.QUARTER_COLUMN_PREFIX,
            descending=True
            )
        
        self.current_period = self.period_cols[0]
        self.prior_period = self.period_cols[4]
        
        self.bmy_col_one = (
            constants.YEAR_COLUMN_PREFIX + self.current_period[-6:]
            )
        
        self.bmy_col_two = (
            constants.YEAR_COLUMN_PREFIX + self.period_cols[4][-6:]
            )
        
        self._set_query()
        

    def _set_query(self):
        cat_region_table = (
            constants.CATEGORY_TOTALS_TABLE + constants.REGION_SUFFIX
            )
        
        seg_region_table = (
            constants.SEGMENT_TOTALS_TABLE + constants.REGION_SUFFIX
            )
        
        period_string = ','.join(self.period_cols)
        
        period_sum_string = (
            ','.join(f'SUM({x})' for x in self.period_cols)
            )
        
        bmy_string_one = f'{"+".join(self.period_cols[:4])} {self.bmy_col_one}'
        bmy_string_two = f'{"+".join(self.period_cols[4:])} {self.bmy_col_two}'
        
        qoq_chg_string = (
            f'{self.current_period}-{self.prior_period} {QTR_AMT_CHG_COL}'
            )
        
        yoy_chg_string = (
            f'{self.bmy_col_one}-{self.bmy_col_two} {YR_AMT_CHG_COL}'
            )
        
        # jurisdiction category totals union jurisdiction segment totals 
        # union jurisdiction totals union region category totals union 
        # region segment totals union region totals union
        # SoCal category totals union SoCal segment totals union
        # SoCal totals union NorCal category totals union 
        # NorCal segment totals union NorCal totals union
        # state category totals union state segment totals
        # union state totals
        self.query = f'''
            SELECT {GROUP_TYPE_COL}, {JURI_TYPE_COL},
                {JURISDICTION_COL}, {GROUP_NAME_COL},
                {yoy_chg_string},{qoq_chg_string},{self.bmy_col_one},
                {self.bmy_col_two},{period_string}
            
            FROM (
                SELECT {GROUP_TYPE_COL},{JURI_TYPE_COL},{JURISDICTION_COL}, {GROUP_NAME_COL},
                    {bmy_string_one},{bmy_string_two},{period_string}
                
                FROM (
                    SELECT '{CAT_TYPE}' {GROUP_TYPE_COL},'{JURI_TYPE}' {JURI_TYPE_COL},j.Name {JURISDICTION_COL},
                        c.Name {GROUP_NAME_COL},{period_string}
                         
                    FROM {constants.CATEGORIES_TABLE} c,
                        {constants.JURISDICTIONS_TABLE} j,
                        {constants.CATEGORY_TOTALS_TABLE} t
                         
                    WHERE c.Id=t.{constants.CATEGORY_ID_COLUMN_NAME}
                        AND j.{constants.TAC_COLUMN_NAME}=t.{constants.TAC_COLUMN_NAME}
                      
                    UNION
                      
                    SELECT '{SEG_TYPE}','{JURI_TYPE}' {JURI_TYPE_COL},j.Name,s.Name,{period_string}
                         
                    FROM {constants.SEGMENTS_TABLE} s,
                        {constants.JURISDICTIONS_TABLE} j,
                        {constants.SEGMENT_TOTALS_TABLE} t
                         
                    WHERE s.Id=t.{constants.SEGMENT_ID_COLUMN_NAME}
                        AND j.{constants.TAC_COLUMN_NAME}=t.{constants.TAC_COLUMN_NAME}
                        
                    UNION
                    
                    SELECT '{OTHER_TYPE}','{JURI_TYPE}' {JURI_TYPE_COL},j.Name,'{OTHER_GROUP}',{period_sum_string}
                         
                    FROM {constants.CATEGORIES_TABLE} c,
                        {constants.JURISDICTIONS_TABLE} j,
                        {constants.CATEGORY_TOTALS_TABLE} t
                         
                    WHERE c.Id=t.{constants.CATEGORY_ID_COLUMN_NAME}
                        AND c.Name IN {OTHER_CATEGORIES}
                        AND j.{constants.TAC_COLUMN_NAME}=t.{constants.TAC_COLUMN_NAME}
                        
                    GROUP BY j.Name
                      
                    UNION
                    
                    SELECT '{TOT_TYPE}','{JURI_TYPE}' {JURI_TYPE_COL},j.Name,'{TOT_GROUP}',{period_sum_string}
                         
                    FROM {constants.CATEGORIES_TABLE} c,
                        {constants.JURISDICTIONS_TABLE} j,
                        {constants.CATEGORY_TOTALS_TABLE} t
                         
                    WHERE c.Id=t.{constants.CATEGORY_ID_COLUMN_NAME}
                        AND j.{constants.TAC_COLUMN_NAME}=t.{constants.TAC_COLUMN_NAME}
                        
                    GROUP BY j.Name
                      
                    UNION
                        
                    SELECT '{CAT_TYPE}','{REGION_TYPE}' {JURI_TYPE_COL},r.Name,c.Name,{period_string}
                         
                    FROM {constants.CATEGORIES_TABLE} c,
                        {constants.REGIONS_TABLE} r,
                        {cat_region_table} t
                         
                    WHERE c.Id=t.{constants.CATEGORY_ID_COLUMN_NAME}
                        AND r.Id=t.{constants.REGION_ID_COLUMN_NAME}
                         
                    UNION
                     
                    SELECT '{SEG_TYPE}','{REGION_TYPE}' {JURI_TYPE_COL},r.Name,s.Name,{period_string}
                         
                    FROM {constants.SEGMENTS_TABLE} s,
                        {constants.REGIONS_TABLE} r,
                        {seg_region_table} t
                         
                    WHERE s.Id=t.{constants.SEGMENT_ID_COLUMN_NAME}
                        AND r.Id=t.{constants.REGION_ID_COLUMN_NAME}
                        
                    UNION
                    
                    SELECT '{OTHER_TYPE}','{REGION_TYPE}' {JURI_TYPE_COL},r.Name,'{OTHER_GROUP}',{period_sum_string}
                         
                    FROM {constants.CATEGORIES_TABLE} c,
                        {constants.REGIONS_TABLE} r,
                        {cat_region_table} t
                         
                    WHERE c.Id=t.{constants.CATEGORY_ID_COLUMN_NAME}
                        AND c.Name IN {OTHER_CATEGORIES}
                        AND r.Id=t.{constants.REGION_ID_COLUMN_NAME}
                        
                    GROUP BY r.Name
                         
                    UNION
                    
                    SELECT '{TOT_TYPE}','{REGION_TYPE}' {JURI_TYPE_COL},r.Name,'{TOT_GROUP}',{period_sum_string}
                         
                    FROM {constants.CATEGORIES_TABLE} c,
                        {constants.REGIONS_TABLE} r,
                        {cat_region_table} t
                         
                    WHERE c.Id=t.{constants.CATEGORY_ID_COLUMN_NAME}
                        AND r.Id=t.{constants.REGION_ID_COLUMN_NAME}
                        
                    GROUP BY r.Name
                         
                    UNION 
                    
                    SELECT '{CAT_TYPE}','{OUTER_REGION_TYPE}' {JURI_TYPE_COL},'{SOCAL_NAME}',c.Name,{period_sum_string}
                         
                    FROM {constants.CATEGORIES_TABLE} c,
                        {constants.REGIONS_TABLE} r,
                        {cat_region_table} t
                         
                    WHERE c.Id=t.{constants.CATEGORY_ID_COLUMN_NAME}
                        AND r.Id=t.{constants.REGION_ID_COLUMN_NAME}
                        AND r.{IS_SOUTHERN_COL}=1   
                        
                    GROUP BY c.Name
                        
                    UNION
                        
                    SELECT '{SEG_TYPE}','{OUTER_REGION_TYPE}' {JURI_TYPE_COL},'{SOCAL_NAME}',s.Name,{period_sum_string}
                         
                    FROM {constants.SEGMENTS_TABLE} s,
                        {constants.REGIONS_TABLE} r,
                        {seg_region_table} t
                         
                    WHERE s.Id=t.{constants.SEGMENT_ID_COLUMN_NAME}
                        AND r.Id=t.{constants.REGION_ID_COLUMN_NAME}
                        AND r.{IS_SOUTHERN_COL}=1
                        
                    GROUP BY s.Name
                    
                    UNION
                    
                    SELECT '{OTHER_TYPE}','{OUTER_REGION_TYPE}' {JURI_TYPE_COL},'{SOCAL_NAME}' {JURISDICTION_COL},
                        '{OTHER_GROUP}',{period_sum_string}
                         
                    FROM {constants.CATEGORIES_TABLE} c,
                        {constants.REGIONS_TABLE} r,
                        {cat_region_table} t
                         
                    WHERE c.Id=t.{constants.CATEGORY_ID_COLUMN_NAME}
                        AND c.Name IN {OTHER_CATEGORIES}
                        AND r.Id=t.{constants.REGION_ID_COLUMN_NAME}
                        AND r.{IS_SOUTHERN_COL}=1
                        
                    GROUP BY {JURISDICTION_COL}
                        
                    UNION
                    
                    SELECT '{TOT_TYPE}','{OUTER_REGION_TYPE}' {JURI_TYPE_COL},'{SOCAL_NAME}','{TOT_GROUP}',{period_sum_string}
                         
                    FROM {constants.CATEGORIES_TABLE} c,
                        {constants.REGIONS_TABLE} r,
                        {cat_region_table} t
                         
                    WHERE c.Id=t.{constants.CATEGORY_ID_COLUMN_NAME}
                        AND r.Id=t.{constants.REGION_ID_COLUMN_NAME}
                        AND r.{IS_SOUTHERN_COL}=1   
                        
                    UNION 
                    
                    SELECT '{CAT_TYPE}','{OUTER_REGION_TYPE}' {JURI_TYPE_COL},'{NORCAL_NAME}',c.Name,{period_sum_string}
                         
                    FROM {constants.CATEGORIES_TABLE} c,
                        {constants.REGIONS_TABLE} r,
                        {cat_region_table} t
                         
                    WHERE c.Id=t.{constants.CATEGORY_ID_COLUMN_NAME}
                        AND r.Id=t.{constants.REGION_ID_COLUMN_NAME}
                        AND r.{IS_SOUTHERN_COL}=0  
                        
                    GROUP BY c.Name
                        
                    UNION
                        
                    SELECT '{SEG_TYPE}','{OUTER_REGION_TYPE}' {JURI_TYPE_COL},'{NORCAL_NAME}',s.Name,{period_sum_string}
                         
                    FROM {constants.SEGMENTS_TABLE} s,
                        {constants.REGIONS_TABLE} r,
                        {seg_region_table} t
                         
                    WHERE s.Id=t.{constants.SEGMENT_ID_COLUMN_NAME}
                        AND r.Id=t.{constants.REGION_ID_COLUMN_NAME}
                        AND r.{IS_SOUTHERN_COL}=0
                        
                    GROUP BY s.Name
                    
                    UNION
                    
                    SELECT '{OTHER_TYPE}','{OUTER_REGION_TYPE}' {JURI_TYPE_COL},'{NORCAL_NAME}' {JURISDICTION_COL},
                        '{OTHER_GROUP}',{period_sum_string}
                         
                    FROM {constants.CATEGORIES_TABLE} c,
                        {constants.REGIONS_TABLE} r,
                        {cat_region_table} t
                         
                    WHERE c.Id=t.{constants.CATEGORY_ID_COLUMN_NAME}
                        AND c.Name IN {OTHER_CATEGORIES}
                        AND r.Id=t.{constants.REGION_ID_COLUMN_NAME}
                        AND r.{IS_SOUTHERN_COL}=0
                        
                    GROUP BY {JURISDICTION_COL}
                    
                    UNION
                    
                    SELECT '{TOT_TYPE}','{OUTER_REGION_TYPE}' {JURI_TYPE_COL},'{NORCAL_NAME}','{TOT_GROUP}',{period_sum_string}
                         
                    FROM {constants.CATEGORIES_TABLE} c,
                        {constants.REGIONS_TABLE} r,
                        {cat_region_table} t
                         
                    WHERE c.Id=t.{constants.CATEGORY_ID_COLUMN_NAME}
                        AND r.Id=t.{constants.REGION_ID_COLUMN_NAME}
                        AND r.{IS_SOUTHERN_COL}=0
                    
                    UNION 
                    
                    SELECT '{CAT_TYPE}','{STATE_TYPE}' {JURI_TYPE_COL},'{STATE_NAME}',c.Name,{period_sum_string}
                         
                    FROM {constants.CATEGORIES_TABLE} c,
                        {constants.REGIONS_TABLE} r,
                        {cat_region_table} t
                         
                    WHERE c.Id=t.{constants.CATEGORY_ID_COLUMN_NAME}
                        AND r.Id=t.{constants.REGION_ID_COLUMN_NAME}  
                        
                    GROUP BY c.Name
                        
                    UNION
                        
                    SELECT '{SEG_TYPE}','{STATE_TYPE}' {JURI_TYPE_COL},'{STATE_NAME}',s.Name,{period_sum_string}
                         
                    FROM {constants.SEGMENTS_TABLE} s,
                        {constants.REGIONS_TABLE} r,
                        {seg_region_table} t
                         
                    WHERE s.Id=t.{constants.SEGMENT_ID_COLUMN_NAME}
                        AND r.Id=t.{constants.REGION_ID_COLUMN_NAME}
                        
                    GROUP BY s.Name
                    
                    UNION
                    
                    SELECT '{OTHER_TYPE}','{STATE_TYPE}' {JURI_TYPE_COL},'{STATE_NAME}' {JURISDICTION_COL},
                        '{OTHER_GROUP}',{period_sum_string}
                         
                    FROM {constants.CATEGORIES_TABLE} c,
                        {constants.REGIONS_TABLE} r,
                        {cat_region_table} t
                         
                    WHERE c.Id=t.{constants.CATEGORY_ID_COLUMN_NAME}
                        AND c.Name IN {OTHER_CATEGORIES}
                        AND r.Id=t.{constants.REGION_ID_COLUMN_NAME}
                        
                    GROUP BY {JURISDICTION_COL}
                    
                    UNION
                        
                    SELECT '{TOT_TYPE}','{STATE_TYPE}' {JURI_TYPE_COL},'{STATE_NAME}','{TOT_GROUP}',{period_sum_string}
                         
                    FROM {constants.CATEGORIES_TABLE} c,
                        {constants.REGIONS_TABLE} r,
                        {cat_region_table} t
                         
                    WHERE c.Id=t.{constants.CATEGORY_ID_COLUMN_NAME}
                        AND r.Id=t.{constants.REGION_ID_COLUMN_NAME}
                    ) 
                )
            '''
        
        
    def run(self):
        try:
            self._set_con()
            self._attach_stars_db()
            self._fetch_totals()
            self._insert_quarter_percent_change()
            self._insert_year_percent_change()
            self._insert_decline_rank()
            self._insert_gain_rank()
            self._insert_rank()
            self._insert_percent_of_total_rank()
            
            if self.df is not None:
                self._output()
                  
                if self.output_saved:
                    utilities.open_file(self.output_path)
                    
        except Exception:
            msg.showerror(
                self.TITLE, 
                'Unhandled exception occurred: \n\n'
                f'{traceback.format_exc()}'
                )
            
        finally:
            self.loading_circle.end()
            
            if self.con is not None:
                self.con.close()
                
            
    def _set_con(self):
        self.con = sql.connect(
            database=constants.DB_PATHS[constants.STATEWIDE_DATASETS_DB],
            timeout=30,
            uri=True
            )
        
    
    def _attach_stars_db(self):
        sql_code = 'ATTACH DATABASE ? AS ?'
        args = (str(constants.DB_PATHS[constants.STARS_DB]), constants.STARS_DB)
        self.con.execute(sql_code, args)
        

    def _fetch_totals(self):
        self.df = pd.read_sql(self.query, self.con)
        
        
    def _insert_quarter_percent_change(self):
        # the percent change column will be inserted before the 
        # quarter amount change 
        index = list(self.df).index(QTR_AMT_CHG_COL)
        
        quarter_change = self.df[QTR_AMT_CHG_COL] / self.df[self.prior_period]
        
        quarter_change.replace([np.inf, -np.inf], np.nan, inplace=True)
        quarter_change.fillna(0, inplace=True)
        
        self.df.insert(index, QTR_PCNT_CHG_COL, quarter_change) 
        
        
    def _insert_year_percent_change(self):
        index = list(self.df).index(YR_AMT_CHG_COL)
        
        year_change = self.df[YR_AMT_CHG_COL] / self.df[self.bmy_col_two]
        
        year_change.replace([np.inf, -np.inf], np.nan, inplace=True)
        year_change.fillna(0, inplace=True)
        
        self.df.insert(index, YR_PCNT_CHG_COL, year_change)
        
        
    def _insert_decline_rank(self):
        index = list(self.df).index(YR_PCNT_CHG_COL)
        
        decline_rank = self.df.groupby(
            RANK_GROUP_COLS
            )[QTR_AMT_CHG_COL].rank()
        
        self.df.insert(index, DECLINE_RANK_COL, decline_rank)
        
        
    def _insert_gain_rank(self):
        index = list(self.df).index(DECLINE_RANK_COL)
        
        gain_rank = self.df.groupby(
            RANK_GROUP_COLS
            )[QTR_AMT_CHG_COL].rank(ascending=False)
            
        self.df.insert(index, GAIN_RANK_COL, gain_rank)
        
        
    def _insert_rank(self):
        index = list(self.df).index(GAIN_RANK_COL)
        
        rank = self.df.groupby(
            RANK_GROUP_COLS
            )[self.bmy_col_one].rank(ascending=False)
            
        self.df.insert(index, RANK_COL, rank)
        
        
    def _insert_percent_of_total_rank(self):
        index = list(self.df).index(YR_PCNT_CHG_COL)
        
        totals = {
            name : total for name, total in 
            self.df[
                self.df[GROUP_TYPE_COL] == TOT_TYPE
                ][[JURISDICTION_COL, self.bmy_col_one]].itertuples(index=False)
            }
        
        percents_of_total = []
        
        for row in self.df.itertuples(index=False):
            juri = getattr(row, JURISDICTION_COL)
            bmy_one = getattr(row, self.bmy_col_one)
            
            total = totals[juri]
            
            percent_of_total = bmy_one / total if total else 0
            
            percents_of_total.append(percent_of_total)
            
        self.df.insert(index, PCNT_OF_TOT_COL, percents_of_total)
           

    def _output(self):
        self.output_saved = utilities.Output.output(
            data=self.df, path=self.output_path, header=list(self.df)
            )
        




    
