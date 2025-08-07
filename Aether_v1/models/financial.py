from pydantic import BaseModel, field_validator
from typing import Optional, Dict, Any
from datetime import date
from decimal import Decimal
from .amounts import AmountType
from .bank_properties import BankName
from .dates import Period

# TODO: Implement transaction model
class Transaction(BaseModel):
    date: date
    category: str
    description: Optional[str]
    amount: Decimal
    type: AmountType
    bank: BankName
    
    @field_validator('amount')
    @classmethod
    def round_amount(cls, amount: Decimal) -> Decimal:
        return amount.quantize(Decimal('0.01'))
    

class Budget(BaseModel):
    user_id: int
    category_id: int
    amount: Decimal
    name: str
    period: Period
    
    @field_validator('amount')
    @classmethod
    def validate_amount(cls, amount: Decimal) -> Decimal:
        if amount <= 0:
            raise ValueError('Amount must be greater than 0')
        else:
            return amount.quantize(Decimal('0.01'))
    
    def to_record(self) -> Dict[str, Any]:
        record = self.model_dump()
        
        record['start_date'] = self.period.start_date
        record['end_date'] = self.period.end_date
        
        del record['period']
        
        return record
    
class BudgetInfo(BaseModel):
    name: str
    category: str
    amount: float
    added_amount: float
    start_date: date
    end_date: date
    achived: Optional[bool]
    expenses: float
    remaining: float