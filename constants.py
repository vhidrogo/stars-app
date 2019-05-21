'''
Created on Jun 25, 2018

@author: vahidrogo
'''

from pathlib import Path
import re
import sys


APP_VERSION = '1.6.8'

APP_NAME = f'StarsApp{APP_VERSION}'

MODULES = [
    'collections',
    'contextlib', 
    'copy',
    'datetime',
    'operator',
    'os',
    'math',
    'ntpath',
    'numpy',
    'pathlib',
    'pandas',
    'pandas.errors',
    'pathvalidate',
    'pdfrw',
    'pdfrw.buildxobj',
    'pdfrw.toreportlab',
    'pyexcelerate',
    'PyPDF2',
    'pyodbc',
    'pythoncom',
    'recordclass',
    'reportlab',
    'reportlab.lib.pagesizes',
    'reportlab.pdfbase',
    'reportlab.pdfbase.ttfonts',
    'reportlab.pdfgen.canvas',
    'requests',
    'selenium',
    'selenium.common.exceptions',
    'selenium.webdriver.common.by',
    'selenium.webdriver.support',
    'selenium.webdriver.support.ui',
    #'shutil',
    'sqlite3',
    'statistics',
    'subprocess',
    'sys',
    'time',
    'threading',
    'TkinterDnD2',
    'traceback', 
    'win32com',
    'xlsxwriter',
    'starsapp'
    ]

DB_FOLDER = Path('N:/stars_app/database')

BACKUP_DB_FOLDER = DB_FOLDER.joinpath('backup')
if not BACKUP_DB_FOLDER.exists():
    Path.mkdir(BACKUP_DB_FOLDER)

# database names
BUSINESSES_DB = 'businesses'
CONFIGURATION_DB = 'configuration.db'
QUARTERLY_CASH_DB = 'quarterly_cash'
QUARTERLY_ECONOMIC_DB = 'quarterly_economic'
STARS_DB = 'starsdb'
STATEWIDE_DATASETS_DB = 'statewide_datasets'

DB_NAMES = [
    BUSINESSES_DB, QUARTERLY_CASH_DB, QUARTERLY_ECONOMIC_DB, STARS_DB,
    STATEWIDE_DATASETS_DB
    ]

DB_PATHS = {
    name : DB_FOLDER.joinpath(f'{name}.db') for name in DB_NAMES
    }

# table names in starsdb
ACCURALS_TABLE = 'accurals'
ADDONS_TABLE = 'Addons'
BUSINESS_CODES_TABLE = 'business_codes'
CATEGORIES_TABLE = 'categories'
COUNTIES_TABLE = 'counties'
JURISDICTIONS_SUB_TYPES_TABLE = 'JurisdictionSubTypes'
JURISDICTION_TYPES_TABLE = 'JurisdictionTypes'
JURISDICTIONS_TABLE = 'Jurisdictions'
NAICS_TABLE = 'naics'
NAICS_TO_BUSINESS_CODE_TABLE = 'naics_to_business_code'
NAME_DICTIONARY_TABLE = 'name_dictionary'
PACKET_REPORTS_TABLE = 'PacketReports'
PACKET_REPORT_SELECTIONS_TABLE = 'PacketReportSelections'
PACKET_TYPES_TABLE = 'PacketTypes'
PERMITS_TABLE = 'permits'
PROCESSES_TABLE = 'processes'
REGIONS_TABLE = 'regions'
REPS_TABLE = 'reps'
SEGMENTS_TABLE = 'segments'
SUMMARY_VERBIAGE = 'summary_verbiage'
TRANSITS_TABLE = 'Transits'

# table names in statewide_databasets
BUSINESS_CODE_TOTALS_TABLE = 'business_code_totals'
CATEGORY_TOTALS_TABLE = 'category_totals'
CDTFA_ALLOCATION_TABLE = 'cdtfa_allocations'
QUARTERLY_COUNTY_POOL_TOTALS_TABLE = 'quarterly_county_pool_totals'
GEO_NAMES_TABLE = 'geo_names'
GEO_RANGES_TABLE = 'geo_ranges'
SEGMENT_TOTALS_TABLE = 'segment_totals'

# common column names
BUSINESS_COLUMN_NAME = 'BUSINESS'
BUSINESS_CODE_ID_COLUMN_NAME = 'business_code_id'
CATEGORY_ID_COLUMN_NAME = 'category_id'
COUNTY_ID_COLUMN_NAME = 'CountyId'
ESTIMATE_COLUMN_NAME = 'EST'
ID_COLUMN_NAME = 'id'
JURISDICTION_ID_COLUMN = 'JurisdictionId'
PERMIT_COLUMN_NAME = 'PERMIT'
REGION_ID_COLUMN_NAME = 'region_id'
SEGMENT_COLUMN_NAME = 'segment'
SEGMENT_ID_COLUMN_NAME = 'segment_id'
TAC_COLUMN_NAME = 'tac'

ADDRESS_COLUMNS = ['NBR', 'DIR', 'STREET', 'TYPE', 'PDIR', 'UNIT']

BUSINESS_TABLE_COLUMNS = [
    ID_COLUMN_NAME, 'JURISDICTION', TAC_COLUMN_NAME, BUSINESS_COLUMN_NAME,  
    PERMIT_COLUMN_NAME, 'SUB', BUSINESS_CODE_ID_COLUMN_NAME
    ]

BUSINESS_TABLE_COLUMNS.extend(ADDRESS_COLUMNS)
BUSINESS_TABLE_COLUMNS.extend([
    'ZIP_CODE', 'OPEN_DATE', 'CLOSED_DATE', 'EST'
    ])

DB_TIMEOUT = 15

DATA_TYPES = ['integer', 'real', 'text']
CONSTRAINTS = ['none', 'primary key', 'unique']

FOREIGN_KEY_SEPARATOR = ':'

'''
    These are the tables that are used by the application and/or
    it's processes. For that reason the user will not be able to
    rename or delete these tables. The same applies for select 
    columns within the tables. They are stored in a dictionary 
    with the table name as the key and a list of the protected
    columns as the value.
'''
PROTECTED_TABLES = {
    BUSINESSES_DB : {BUSINESS_CODES_TABLE : [ID_COLUMN_NAME, 'name']}, 
    
    QUARTERLY_CASH_DB : {}, 
    
    QUARTERLY_ECONOMIC_DB : {}, 
    
    STARS_DB : {
        ACCURALS_TABLE : [ID_COLUMN_NAME, 'name'],
        
        ADDONS_TABLE : [
            'folder_name', ID_COLUMN_NAME, 'jurisdiction_id', 
            'name', 'percent', TAC_COLUMN_NAME
            ], 
        
        BUSINESS_CODES_TABLE : [ID_COLUMN_NAME, 'name', 'segment_id'],
        
        CATEGORIES_TABLE : [ID_COLUMN_NAME, 'name'],
        
        'industries' : [ID_COLUMN_NAME, 'name', 'industry_group_id'],
        
        'industry_groups' : [ID_COLUMN_NAME, 'name', 'subsector_id'],
        
        JURISDICTIONS_SUB_TYPES_TABLE : ['Id', 'Name'],
        
        JURISDICTIONS_TABLE : [
            'accural', 'folder_name', 'has_addon', 'has_geo', ID_COLUMN_NAME, 
            'is_client', 'name', 'region_id', 'rep_id', TAC_COLUMN_NAME
            ],
        
        NAICS_TABLE : [
            ID_COLUMN_NAME, 'name', 'industry_id', 'business_code_id'
            ],
        
        NAICS_TO_BUSINESS_CODE_TABLE : ['naics', 'business_code_id'],
        
        NAME_DICTIONARY_TABLE : ['bad_name', 'good_name', 'segment_code'],
        
        PACKET_REPORTS_TABLE : [ID_COLUMN_NAME, 'name', 'path', 'is_duplex'],
        
        PACKET_REPORT_SELECTIONS_TABLE : ['packet_type', 'report_id_1'],
        
        PERMITS_TABLE : ['permit', 'business', 'segment_id'],
        
        PROCESSES_TABLE : [ID_COLUMN_NAME, 'desc', 'output_name', 'opens_output'],
        
        REGIONS_TABLE : [ID_COLUMN_NAME, 'name'],
        
        REPS_TABLE : [ID_COLUMN_NAME, 'name', 'email', 'phone'],
        
        'sectors' : [ID_COLUMN_NAME, 'name'],
        
        SEGMENTS_TABLE : [ID_COLUMN_NAME, 'name', 'sector_id', 'full_name'],
        
        'sub_sectors' : [ID_COLUMN_NAME, 'name', 'sector_id'],
        
        SUMMARY_VERBIAGE : [ID_COLUMN_NAME, 'period', 'position', 'verbiage'],
        
        TRANSITS_TABLE : [
            ID_COLUMN_NAME, TAC_COLUMN_NAME, 'name', 'folder_name', 'rep_id', 
            'has_geo', 'percent', 'is_client']
        },
    
    STATEWIDE_DATASETS_DB : {
        QUARTERLY_COUNTY_POOL_TOTALS_TABLE : [ID_COLUMN_NAME],
        
        GEO_NAMES_TABLE : [ID_COLUMN_NAME, 'jurisdiction_id', 'number', 'name'],
        
        GEO_RANGES_TABLE : [
            ID_COLUMN_NAME, 'jurisdiction_id', 'geo_name_id', 'street', 
            'street_type', 'dir', 'pdir', 'side', 'low', 'high'
            ] 
        }
    }

ID_COLUMN_TOOLTIPS = {
    STATEWIDE_DATASETS_DB : {
        GEO_NAMES_TABLE : 'id="{jurisdiction_id}-{from_range_id}-{to_range_id}"',
        GEO_RANGES_TABLE : 'id=Any unique integer, 1 + current row count will work.'
        },
    
    STARS_DB : {
        ADDONS_TABLE : 'id=three char abbreviation',
        JURISDICTIONS_TABLE : 'id=three char abbreviation',
        PACKET_REPORT_SELECTIONS_TABLE : 'id="{PacketTypeId}-{JurisdictionTypeId}-{RepId}"',
        PERMITS_TABLE : 'id=Formatted permit number "###-######".',
        SUMMARY_VERBIAGE : 'id="{period}-{position}".'
        }
    }

DB_MODES = {0 : 'Alter', 1 : 'Insert'}

BMY_PERIOD_COUNT = 4
MAX_PERIOD_COUNT = 40

ADDON_IDENTIFIER = '77'

UNINCORPORATED_IDENTIFIER = '998'

QUARTER_COLUMN_PREFIX = 'qtr_'
YEAR_COLUMN_PREFIX = 'bmy_'

NUMBER_TABLE_PREFIX = 'table_'

ADDON_SUFFIX = '_ao'
REGION_SUFFIX = '_region'

PERMIT_FORMAT = '###-######'

MAX_EXPORT_RECORDS_EXCEL = 100000

COUNT_FOR_SCROLLBAR = 15

MISSING_SUB_PLACE_HOLDER = 9999

# indexes of columns in business detail csv input data
CITY_COLUMN = 0
TAC_COLUMN = 1
BUSINESS_COLUMN = 2 
PERMIT_COLUMN = 3
SUB_COLUMN = 4
ADDRESS_COLUMN = 5
ZIP_COLUMN = 6
NAICS_COLUMN = 7
OPEN_COLUMN = 8
CLOSE_COLUMN = 9
ESTIMATE_COLUMN = 10
FIRST_QUARTER_COLUMN = 11

# indexes of column in the tables
DB_JURISDICTION_COLUMN = 1
DB_TAC_COLUMN = 2
DB_BUSINESS_COLUMN = 3
DB_PERMIT_COLUMN = 4
DB_BUSINESS_CODE_ID_COLUMN = 6
DB_ADDRESS_NUMBER_COLUMN = 7
DB_ADDRESS_DIR_COLUMN = 8
DB_ADDRESS_STREET_COLUMN = 9
DB_ADDRESS_TYPE_COLUMN = 10
DB_ADDRESS_PDIR_COLUMN = 11
DB_ADDRESS_UNIT_COLUMN = 11
DB_ESTIMATE_COLUMN = 16
DB_FIRST_QUARTER_COLUMN = 17

BLUE_THEME_COLOR = '#013a57'

GENERAL_RETAIL_COLOR = '#692104'
FOOD_PRODUCTS_COLOR = '#FBB425'
TRANSPORTATION_COLOR = BLUE_THEME_COLOR
CONSTRUCTION_COLOR = '#9C6315'
B2B_COLOR = '#506E32'
MISC_COLOR = '#797979'

GRAY_COLOR = '#dbdbdb'

THEME_COLORS = {
    'general_retail' : GENERAL_RETAIL_COLOR, 
    'food_products' : FOOD_PRODUCTS_COLOR, 
    'transportation' : TRANSPORTATION_COLOR,
    'construction' : CONSTRUCTION_COLOR, 
    'business_to_business' : B2B_COLOR, 
    'miscellaneous' : MISC_COLOR
    }

OUT_PAD = 10
IN_PAD = OUT_PAD // 2

DEFAULT_BUSINESS_CODE = 19
BLANK_BUSINESS_CODE = 0

LEFT_CONFIDENTIAL_FOOTER = 'Confidential'
LEFT_NON_CONFIDENTIAL_FOOTER = 'Non-Confidential'
RIGHT_FOOTER = 'MuniServices / Avenu Insights && Analytics'

# if the application is bundled as an executable
if getattr(sys, 'frozen', False):
    APP_PATH = Path(sys._MEIPASS)
else:
    APP_PATH = Path(__file__).resolve().parent

# removes "src" folder from path
APP_PATH = Path(str(APP_PATH).rsplit('\\', 1)[0])

FILES_PATH = APP_PATH.joinpath('files')  

APPS_PATH = FILES_PATH.joinpath('apps')
INTERNAL_DB_FOLDER = FILES_PATH.joinpath('internaldb')
HELP_PATH = FILES_PATH.joinpath('help') 
MEDIA_PATH = FILES_PATH.joinpath('media')
SCRIPTS_PATH = FILES_PATH.joinpath('scripts')
APP_FILES_PATH = FILES_PATH.joinpath('app_files')

FONTS_PATH = MEDIA_PATH.joinpath('fonts')

TEMP_FILE_PATH = APP_PATH.joinpath('temp_files')
if not TEMP_FILE_PATH.exists():
    Path.mkdir(TEMP_FILE_PATH)

PERMIT_PATTERN = re.compile(r'\d{3}-?\d{6}')

BUSINESS_NAME_REMOVE_PATTERNS = [
    re.compile(pattern, re.IGNORECASE)  for pattern in 
    (r"( |, |,|.|')?(CORP|INC|LLC|LTD|ASSN|ASSOC)(\.|')?$",
     r'\(?# ?\d{0,6}-?\d{0,6}\w?\)?'
     )
    ]

SECONDS_PER_ROW_CSV = 0.000210685219236056
SECONDS_PER_ROW_EXCEL = 0.0019460181349047298