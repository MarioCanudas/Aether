from pydantic import BaseModel, field_validator
from enum import Enum
from typing import Optional, List
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
    

class FinancialStatus(str, Enum):
    EXCELLENT = "Excellent!"
    GOOD = "Good"
    REGULAR = "Regular"
    POOR = "Poor"