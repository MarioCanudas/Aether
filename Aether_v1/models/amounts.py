from enum import Enum
from pydantic import BaseModel

class TransactionType(str, Enum):
    INCOME = 'Abono'
    EXPENSE = 'Cargo'
    INITIAL_BALANCE = 'Saldo inicial'

class AmountSignType(Enum):
    POSITIVE = '+'
    NEGATIVE = '-'
    NEUTRAL = None
    
class AmountSigns(BaseModel):
    income: AmountSignType
    expense: AmountSignType
    
class Balances(BaseModel):
    """Represents a balance with an initial and final amount."""
    
    initial: float | None
    final: float | None
    
class AmountColumns(BaseModel):
    income: str
    expense: str
    balance: str | None = None
    all_list: list[str]
    
    @property
    def is_mono_column(self) -> bool:
        if len(self.all_list) == 1 and self.income == self.expense:
            return True
        else:
            return False
        
    @property
    def has_balance(self) -> bool:
        if self.balance is not None:
            return True
        else:
            return False
        
    @property
    def column(self) -> str:
        if self.is_mono_column:
            return self.income
        else:
            raise ValueError("AmountColumns is not a mono column")
