from pydantic import BaseModel
from enum import Enum
from typing import Any
from .amounts import AmountColumns, AmountSigns, Balances
from .dates import DateGroups, Period

class BankName(str, Enum):
    CASH = 'cash'
    AMEX = 'amex'
    BANORTE = 'banorte'
    BBVA = 'bbva'
    BANAMEX = 'banamex'
    HSBC = 'hsbc'
    INBURSA = 'inbursa'
    NU = 'nu'
    SANTANDER = 'santander'
    
    @classmethod
    def get_values(cls) -> list[str]:
        return [bank.value for bank in cls]
    
    
class StatementType(str, Enum):
    CREDIT = 'credit'
    DEBIT = 'debit'
    
    @classmethod
    def get_values(cls) -> list[str]:
        return [statement_type.value for statement_type in cls]
    
    
class Metadata(BaseModel):
    bank: BankName
    statement_type: StatementType
    period: Period
    balances: Balances
    
    
class BankProperties(BaseModel):
    bank: BankName
    statement_type: StatementType
    new_format: bool | None = None
    
    start_phrase: list[str]
    end_phrase: list[str]
    period_phrase: list[str] | None = None
    initial_balance_phrase: list[str] | None = None
    final_balance_phrase: list[str] | None = None
    initial_balance_description: str | None = None
    generated_amount_phrase: list[str] | None = None
    
    columns: list[str]
    amount_columns: AmountColumns
    
    date_pattern: str
    date_groups: DateGroups
    month_pattern: dict[str, str]
    
    amount_signs: AmountSigns
    
    period_pattern: str | None = None
    period_month_pattern: dict[str, str] | None = None
    period_group: DateGroups | None = None
    
    special_data_filtering: Any = None
