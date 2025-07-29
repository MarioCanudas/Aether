from pydantic import BaseModel
from enum import Enum
from typing import Optional, List, Dict
from .amounts import AmountColumns, AmountSigns, Balances
from .dates import DateGroups, Period
from ..services.statement_data_extraction import SpecialDataFiltering

class BankName(str, Enum):
    AMEX = 'amex'
    BANORTE = 'banorte'
    BBVA = 'bbva'
    BANAMEX = 'banamex'
    HSBC = 'hsbc'
    INBURSA = 'inbursa'
    NU = 'nu'
    SANTANDER = 'santander'
    
    
class StatementType(str, Enum):
    CREDIT = 'credit'
    DEBIT = 'debit'
    
    
class Metadata(BaseModel):
    bank: BankName
    statement_type: StatementType
    period: Period
    balances: Balances
    
    def get_years(self) -> List[int]:
        return sorted(list(set([year for year in self.period.years])))
    
    
class BankProperties(BaseModel):
    bank: BankName
    statement_type: StatementType
    new_format: Optional[bool] = None
    
    start_phrase: List[str]
    end_phrase: List[str]
    period_phrase: Optional[List[str]] = None
    initial_balance_phrase: Optional[List[str]] = None
    final_balance_phrase: Optional[List[str]] = None
    initial_balance_description: Optional[str] = None
    generated_amount_phrase: Optional[List[str]] = None
    
    columns: List[str]
    amount_columns: AmountColumns
    
    date_pattern: str
    date_groups: DateGroups
    month_pattern: Dict[str, str]
    
    amount_signs: AmountSigns
    
    period_pattern: Optional[str] = None
    period_month_pattern: Optional[Dict[str, str]] = None
    period_group: Optional[DateGroups] = None
    
    special_data_filtering: Optional[SpecialDataFiltering] = None
