'''
Created on Mar 12, 2018

@author: vahidrogo
'''

import constants
import utilities


class Jurisdiction:
    '''
    '''
    
    
    def __init__(self, jurisdiction_id='', jurisdiction_tac=''):
        if jurisdiction_id:
            self.identifier = jurisdiction_id
            self.where_condition = constants.ID_COLUMN_NAME 
        else:
            self.identifier = jurisdiction_tac
            self.where_condition = constants.TAC_COLUMN_NAME
        
        self.id = ''
        self.tac = ''
        self.name = ''
        self.folder_name = ''
        self.rep_id = 1
        self.rep_name = ''
        self.has_geo = 0
        self.has_addon = 0
        self.accural_id = 1
        self.accural = ''
        self.is_client = 0
        self.county_id = 0
        self.county_name = ''
        self.region_id = ''
        self.region_name = ''
        self.is_southern = ''
        self.percent = 1
        self.type = ''
        self.type_id = 1
        self.exists = False
        
        self._set_attributes()
        
        self.folder = f'N:/{{year}} Q{{quarter}}/{self.rep_name}/{self.folder_name}/'
    
 
    def _set_attributes(self):
        query = f'''
            SELECT sub.Id, Tac, sub.Name, FolderName, RepId, rep.Name, 
                HasGeo, HasAddon, AccuralId, a.Name, IsClient, CountyId, 
                c.Name, r.id, r.Name, r.is_southern, Percent, type, j.id
                
            FROM {constants.ACCURALS_TABLE} a, 
                {constants.JURISDICTION_TYPES_TABLE} j, 
                {constants.REPS_TABLE} rep,
                {constants.COUNTIES_TABLE} c, 
                {constants.REGIONS_TABLE} r,
                (
                    SELECT Id, Tac, Name, FolderName, RepId, HasGeo, HasAddon, 
                        AccuralId, IsClient, CountyId, 1 as Percent, 'jurisdiction' as type
                    FROM {constants.JURISDICTIONS_TABLE}
                
                    UNION
                
                    SELECT id, tac, Name, FolderName, RepId, HasGeo, 
                        0 as HasAddon, 1 as AccuralId, IsClient, 
                        1 as CountyId, Percent, 'transit' as type
                    FROM {constants.TRANSITS_TABLE}
                    
                    UNION
                     
                    SELECT a.id, a.tac, a.Name, a.FolderName, j.RepId, 
                        0 as HasGeo, 0 as HasAddon, j.AccuralId, j.IsClient, 
                        j.CountyId, a.Percent, 'addon' as type
                    FROM {constants.JURISDICTIONS_TABLE} as j, 
                        {constants.ADDONS_TABLE}  a 
                    WHERE a.JurisdictionId=j.id
                ) sub
                
            WHERE rep.Id=sub.RepId 
                AND a.Id=sub.AccuralId 
                AND c.Id=sub.CountyId
                AND r.Id=c.{constants.REGION_ID_COLUMN_NAME}
                AND j.Name=sub.type
                AND sub.{self.where_condition}=?
            '''
        
        results = utilities.execute_sql(
            sql_code=query, args=(self.identifier,), 
            db_name=constants.STARS_DB
            )
        
        if results:
            self.id = results[0]
            self.tac = results[1]
            self.name = results[2]
            self.folder_name = results[3]
            self.rep_id = results[4]
            self.rep_name = results[5]
            self.has_geo = results[6]
            self.has_addon = results[7]
            self.accural_id = results[8]
            self.accural = results[9]
            self.is_client = results[10]
            self.county_id = results[11]
            self.county_name = results[12]
            self.region_id = results[13]
            self.region_name = results[14]
            self.is_southern = results[15]
            self.percent = results[16]
            self.type = results[17]  
            self.type_id = results[18]
            self.exists = True  
                            
                
    def __str__(self):
        return (
                f'id={self.id}, tac={self.tac}, name={self.name}, '
                f'folder_name={self.folder_name}, rep_id={self.rep_id}, '
                f'rep_name={self.rep_name}, has_geo={self.has_geo}, '
                f'has_addon={self.has_addon}, accural_id={self.accural_id}, '
                f'accural={self.accural}, is_client={self.is_client}, '
                f'county_id={self.county_id}, county_name={self.county_name}, '
                f'region_id={self.region_id}, region_name={self.region_name}, '
                f'is_southern={self.is_southern}, percent={self.percent}, '
                f'type={self.type}, type_id={self.type_id}, exists={self.exists}, '
                f'folder={self.folder}'
            )