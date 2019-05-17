'''
Created on Aug 6, 2018

@author: vahidrogo
'''

import constants
from estimates import Estimates
from internaldata import InternalData
import utilities


class ExportBusinessDetail:
    '''
    '''
    
    
    even_side = 'E'
    odd_side = 'O'
    
    business_code_query = f'''
        SELECT b.{constants.ID_COLUMN_NAME}, b.name, c.name, s.name
        
        FROM {constants.BUSINESS_CODES_TABLE} as b, 
            {constants.CATEGORIES_TABLE} as c, {constants.SEGMENTS_TABLE} as s
            
        WHERE b.segment_id=s.{constants.ID_COLUMN_NAME} 
            AND s.category_id=c.{constants.ID_COLUMN_NAME}
        '''
    
    output_names = {
        'QuarterCash': 'QC',
        'QuarterEcon': 'QE',
        'YearCash': 'YC',
        'YearEcon': 'YE'
        }
    
    
    def __init__(self, controller):
        self.controller = controller
        self.selections = self.controller.selections
        
        self.report_name = self.output_names[
            f'{self.selections.interval}{self.selections.basis}'
            ]
        
        self.is_cash = self.selections.basis == 'Cash'
        self.is_year = self.selections.interval == 'Year'

        self.output_saved = False
        
        self.jurisdiction = None
        
        self.column_names = []
        self.sheet_rows = []
        
        self.geo_ranges = {}
        
        self._set_business_codes()
        
        self.estimates = Estimates()
        
        
    def _set_business_codes(self):
        '''
            Populates a dictionary with the business code, segment and 
            category names for each of the business code ids. 
        '''
        self.business_codes = {}
        
        results = utilities.execute_sql(
            sql_code=self.business_code_query, 
            db_name=constants.STARS_DB, fetchall=True
            )
        
        if results:
            for business_code_id, business_code, category, segment in results:
                self.business_codes[business_code_id] = {
                    'business_code': business_code, 'segment': segment, 
                    'category': category
                    }
        
    def main(self, jurisdiction):
        self.jurisdiction = jurisdiction
        
        self.controller.update_progress(
            0, f'{self.jurisdiction.id}: Fetching data.'
            )
         
        output = True
        
        if self.selections.include_geos:
            self._set_geo_ranges()
            
            if not self.geo_ranges:
                output = False
                
        if output:
            self.internal_data = InternalData(
                self.is_cash, self.jurisdiction.id
                )
               
            results = self.internal_data.get_data()
               
            if results:
                self._set_column_names(results['column_names'])
                     
                data = results['data']
                  
                if data:
                    progress = 10
                         
                    if self.selections.include_estimates:
                        self.estimates.set_dictionaries(data)
                             
                    self.row_count = len(data)
                         
                    self.controller.update_progress(
                        progress, f'{self.jurisdiction.id}: Processing businesses.'
                        )
                           
                    # the progress after the businesses are done processing
                    business_end_progress = (
                        90 if self.selections.output_type == 'CSV' else 40
                        )
                            
                    progress_increment = self._get_progress_increment(
                        progress, business_end_progress)
                            
                    self._process_businesses(data, progress, progress_increment)
                        
                    progress = business_end_progress
                          
                    self.controller.update_progress(
                        progress, 
                        f'{self.jurisdiction.id}: Writing {self.report_name} '
                        f'{self.selections.output_type} output.'
                        )
                              
                    self._set_output_path()
 
                    self.output_saved = utilities.Output.output(
                        self.sheet_rows, self.output_path, self.column_names
                        )
     
                    if self.output_saved:
                        self.controller.update_progress(
                            100, f'{self.jurisdiction.id}: Finished.'
                            )
                        
                        if self.selections.open_output:
                            utilities.open_file(self.output_path)
        
        
    def _set_geo_ranges(self):
        geos = self._get_geos()
        
        if geos:
            for range_ids, name in geos.items():
                range_ids = range_ids.split('-')
                
                from_range_id = int(range_ids[0])
                to_range_id = int(range_ids[1])
                
                range_ids = self._range_ids(from_range_id, to_range_id)
      
                geo_ranges = self._get_geo_ranges(range_ids)
                
                if geo_ranges:
                    self.geo_ranges[name] = {}
                     
                    self.geo_ranges[name][self.even_side] = {}
                    self.geo_ranges[name][self.odd_side] = {}
                     
                    for st, st_type, st_dir, pdir, side, low, high in geo_ranges:
                        key = self._get_range_key([st, st_type, st_dir, pdir])
                         
                        if key not in self.geo_ranges[name][side]:
                            self.geo_ranges[name][side][key] = []
                             
                        street_ranges = (low, high)
                             
                        self.geo_ranges[name][side][key].append(street_ranges)
                        
            
    def _get_geos(self):
        query = '''
            SELECT from_range_id, to_range_id, name
            FROM geo_names
            WHERE jurisdiction_id=?
            '''
        
        results = utilities.execute_sql(
            sql_code=query, args=(self.jurisdiction.id,), 
            db_name=constants.STATEWIDE_DATASETS_DB, fetchall=True
            )
        
        geos = {}
        
        if results:
            results.sort()
            
            # insert a row with the column names
            results.insert(0, ['FROM', 'TO', 'NAME'])
            
            # formated strings with the geo numbers and name to show in text file
            text_lines = [
                '{:>4} - {:>5}   :    {}'.format(from_id, to_id, name)
                for from_id, to_id, name in results
                ]
            
            text_file = f'Export {self.report_name}'
             
            exclude_geos = utilities.get_excluded_from_text_file(
                text_file, text_lines, self.jurisdiction
                )
             
            if exclude_geos:
                exclude_geos = [
                    line.rsplit(':', 1)[0].split('-') for line in exclude_geos
                    ]
                
                exclude_geos = [
                    (int(x[0].strip()), int(x[1].strip())) for x in exclude_geos
                    ]
            
            # loops through all result rows minus the row for the column 
            # names that that was inserted at the beginning
            for from_id, to_id, name in results[1:]:
                if (from_id, to_id) not in exclude_geos:
                    geos[f'{from_id}-{to_id}'] = name
                  
        return geos
    
    
    def _range_ids(self, from_range_id, to_range_id):
        if from_range_id >= to_range_id:
            range_ids = from_range_id
            
        else:
            range_ids = [i for i in range(from_range_id, to_range_id + 1)]
        
        return range_ids
    
    
    def _get_geo_ranges(self, range_ids):
        args = [self.jurisdiction.id, ]
        
        # if there is more than one range id or a list or range ids
        if isinstance(range_ids, list):
            # the range id will be checked against all range ids
            range_id_condition = f'IN {tuple(range_ids)}'
            
        else:
            # only the one range id has to be checked 
            range_id_condition = '=?'
            
            # adds the range id to the list or arguments that will be passed
            # along with the sql query
            args.append(range_ids)
            
        query = f'''
            SELECT street, street_type, dir, pdir, side, low, high
            FROM geo_ranges
            WHERE jurisdiction_id=? AND range_id {range_id_condition} 
            '''
        
        results = utilities.execute_sql(
            sql_code=query, args=args, fetchall=True, 
            db_name=constants.STATEWIDE_DATASETS_DB 
            )
        
        return results
    
    
    def _get_range_key(self, values):
        key = ''
        
        for i in values:
            if i:
                key += i
            
        return key
        
        
    def _set_column_names(self, column_names):
        self._remove_quarter_prefixes(column_names)
        
        if self.is_year:
            del column_names[-3:]
        
        # skips the id column name and inserts the three names of the 
        # classifications where the name of the business code id column was  
        left = column_names[1: constants.DB_BUSINESS_CODE_ID_COLUMN]
        right = column_names[constants.DB_BUSINESS_CODE_ID_COLUMN + 1:]
        
        middle = ['CATEGORY', 'SEGMENT', 'BUSINESS_CODE']
        
        self.column_names = left + middle + right
        
    
    def _remove_quarter_prefixes(self, columns):
        for i, column in enumerate(columns):
            columns[i] = column.replace(constants.QUARTER_COLUMN_PREFIX, '')
            
            
    def _get_progress_increment(self, start_progress, end_progress):
        return (end_progress - start_progress) / self.row_count
            
    
    def _process_businesses(self, data, progress, progress_increment):
        for i, row in enumerate(data):
            include = True
            # converts tuple to list for assigning
            row = list(row)
            
            if self.selections.include_geos:
                geo_name = self._get_geo_name(row)
                
                if geo_name:
                    row[constants.DB_JURISDICTION_COLUMN] = geo_name
                    
                else:
                    include = False
                    
            if include:
                amounts = row[constants.DB_FIRST_QUARTER_COLUMN:]
                  
                if self.selections.include_estimates:
                    # gets the estimate amount if one is necessary, if one is 
                    # not necessary then 0 will be returned
                    estimate_amount = self.estimates.get_estimate(row)
                           
                    if estimate_amount:
                        # converts amounts tuple to list for easy assigning
                        amounts = list(amounts)
                          
                        # sets the estimate
                        amounts[0] = estimate_amount
                          
                        # sets the estimate flag
                        row[
                            constants.DB_ESTIMATE_COLUMN] = constants.ESTIMATE_COLUMN_NAME
                  
                if self.is_year:
                    amounts = self._get_bmy_amounts(amounts)
                      
                row[constants.DB_FIRST_QUARTER_COLUMN:] = amounts
               
                business_code_id = row[constants.DB_BUSINESS_CODE_ID_COLUMN]
                
                if business_code_id:
                    business_code_info = self.business_codes[business_code_id]
                     
                    category = business_code_info['category']
                    segment = business_code_info['segment']
                    business_code = business_code_info['business_code']
                    
                else:
                    category = ''
                    segment = ''
                    business_code = ''
                 
                # skips the id column, replaces business code id with 
                # the values of the three classifications
                left = row[1: constants.DB_BUSINESS_CODE_ID_COLUMN]
                middle = [category, segment, business_code]
                right = row[constants.DB_BUSINESS_CODE_ID_COLUMN + 1:]
                 
                new_row = left + middle + right
     
                self.sheet_rows.append(new_row)
                  
            progress += progress_increment
            
            self.controller.update_progress(
                progress, 
                f'{self.jurisdiction.id}: Processing businesses '
                f'{i:,} /{self.row_count:,}'
                )
            
            
    def _get_bmy_amounts(self, quarterly_amounts):
        bmy_amounts = [
            sum(quarterly_amounts[i: i + 4]) 
            for i in range(len(quarterly_amounts)-3)]
        
        return bmy_amounts
    
    
    def _get_geo_name(self, row_values):
        geo_name = ''
        geo_names = []
        
        street_number = row_values[constants.DB_ADDRESS_NUMBER_COLUMN]
        
        if street_number:
            street_number = int(street_number)
            
            # if the street number is on the even side
            side = self.even_side if not street_number % 2 else self.odd_side
            
            street = row_values[constants.DB_ADDRESS_STREET_COLUMN]
            street_type = row_values[constants.DB_ADDRESS_TYPE_COLUMN]
            street_dir = row_values[constants.DB_ADDRESS_DIR_COLUMN]
            street_pdir = row_values[constants.DB_ADDRESS_PDIR_COLUMN]
            
            key = self._get_range_key(
                [street, street_type, street_dir, street_pdir]
                )
            
            for name, ranges in self.geo_ranges.items():
                side_ranges = ranges[side]
                
                if key in side_ranges:
                    number_ranges = side_ranges[key]
                    
                    if any(
                        low <= street_number <= high 
                        for low, high in number_ranges
                        ):
                            
                        geo_names.append(name)
                        
        if geo_names:
            geo_name = ', '.join(geo_names)
        
        return geo_name
    
    
    def _set_output_path(self):
        name = (
            f'{self.jurisdiction.id} {self.selections.period} {self.report_name}'
            )
        
        if self.selections.include_geos:
            name += ' Geos'
        
        folder = self.jurisdiction.folder
        
        self.output_path = f'{folder}{name}.{self.selections.output_type}'
        
        
    