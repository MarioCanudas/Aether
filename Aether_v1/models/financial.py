from pydantic import BaseModel, field_validator
from enum import Enum
from typing import Optional
from datetime import date
from decimal import Decimal
from .amounts import TransactionType
from .bank_properties import BankName, StatementType

# TODO: Implement transaction model
class Transaction(BaseModel):
    date: date
    category: str
    description: Optional[str]
    amount: Decimal
    type: TransactionType
    bank: BankName
    
    @field_validator('amount')
    @classmethod
    def round_amount(cls, amount: Decimal) -> Decimal:
        return amount.quantize(Decimal('0.01'))
    
    
class TransactionRecord(BaseModel):
    user_id: int
    category_id: Optional[int]
    date: date
    description: Optional[str]
    amount: Decimal
    type: TransactionType
    bank: BankName
    statement_type: StatementType
    filename: Optional[str]
    

class FinancialStatus(str, Enum):
    EXCELLENT = "Excellent!"
    GOOD = "Good"
    REGULAR = "Regular"
    POOR = "Poor"
    
    @property
    def score(self) -> int:
        if self == FinancialStatus.EXCELLENT:
            return 100
        elif self == FinancialStatus.GOOD:
            return 75
        elif self == FinancialStatus.REGULAR:
            return 50
        else:
            return 25
        
    @property
    def icon(self) -> str:
        if self == FinancialStatus.EXCELLENT:
            return '🏆'
        elif self == FinancialStatus.GOOD:
            return '👍'
        elif self == FinancialStatus.REGULAR:
            return '👌'
        else:
            return '👎'
        
    @property
    def color(self) -> str:
        if self == FinancialStatus.EXCELLENT:
            return 'green'
        elif self == FinancialStatus.GOOD:
            return 'yellow'
        elif self == FinancialStatus.REGULAR:
            return 'orange'
        else:
            return 'red'
    
    
class FinancialAmountsSums(BaseModel):
    """
    This model is used to sum the financial amounts of the user, such as income, 
    withdrawal and savings. 
    
    It allows to calculate the balance of the user. 
    
    It not depends on the period of the sums, so can be used for all periods and avarage sums.
    """
    income: Decimal
    withdrawal: Decimal
    savings: Optional[Decimal]
    
    @property
    def balance(self) -> Decimal:
        return self.income + self.withdrawal
    