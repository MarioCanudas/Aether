from enum import Enum
from typing import List
from models.dates import MonthPatterns

class MonthLabels(str, Enum):
    JAN = 'Jan'
    FEB = 'FEB'
    MAR = 'Mar'
    APR = 'Apr'
    MAY = 'May'
    JUN = 'Jun'
    JUL = 'Jul'
    AUG = 'Aug'
    SEP = 'Sep'
    OCT = 'Oct'
    NOV = 'Nov'
    DEC = 'Dec'
    
    @classmethod
    def get_values(self) -> List[str]:
        return [option.value for option in self]

MONTH_PATTERNS = MonthPatterns(
    num_to_abbr = {
        '01': 'ENE',
        '02': 'FEB',
        '03': 'MAR',
        '04': 'ABR',
        '05': 'MAY',
        '06': 'JUN',
        '07': 'JUL',
        '08': 'AGO',
        '09': 'SEP',
        '10': 'OCT',
        '11': 'NOV',
        '12': 'DIC'
    },
    
    abbr_to_num = {
        'ENE': '01',
        'FEB': '02',
        'MAR': '03',
        'ABR': '04',
        'MAY': '05',
        'JUN': '06',
        'JUL': '07',
        'AGO': '08',
        'SEP': '09',
        'OCT': '10',
        'NOV': '11',
        'DIC': '12'
    },
    
    month_to_num = {
        'Enero': '01',
        'Febrero': '02',
        'Marzo': '03',
        'Abril': '04',
        'Mayo': '05',
        'Junio': '06',
        'Julio': '07',
        'Agosto': '08',
        'Septiembre': '09',
        'Octubre': '10',
        'Noviembre': '11',
        'Diciembre': '12'
    }
)

