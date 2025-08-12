from pydantic import BaseModel, field_validator
from typing import Optional, Dict, Any, List
from datetime import date
from decimal import Decimal
from matplotlib.pyplot import Figure
from .amounts import TransactionType
from .bank_properties import BankName, StatementType
from .categories import GoalType
from .dates import Period

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
    

class Goal(BaseModel):
    user_id: int
    type: GoalType
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
        
        record['type'] = self.type.value
        
        record['start_date'] = self.period.start_date
        record['end_date'] = self.period.end_date
        
        del record['period']
        
        return record
    
class GoalInfo(BaseModel):
    name: str
    type: GoalType
    category: str
    amount: float
    added_amount: float
    start_date: date
    end_date: date
    achived: Optional[bool]
    expenses: float
    remaining: float
    
class SummaryMetrics(BaseModel):
    total_savings: Decimal
    avg_income_per_month: Decimal
    avg_withdrawal_per_month: Decimal
    
class FinancialSummary(BaseModel):
    summary_metrics: SummaryMetrics
    label: str
    tips: List[str]
    
    @property
    def total_savings(self) -> Decimal:
        return self.summary_metrics.total_savings
    
    @property
    def avg_income_per_month(self) -> Decimal:
        return self.summary_metrics.avg_income_per_month
    
    @property
    def avg_withdrawal_per_month(self) -> Decimal:
        return self.summary_metrics.avg_withdrawal_per_month