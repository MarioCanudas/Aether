from pydantic import BaseModel
from typing import Optional, List
from decimal import Decimal
from datetime import date
from .bank_properties import BankName, StatementType
from .records import TransactionRecord

class Card(BaseModel):
    card_id: Optional[int] = None
    user_id: int
    card_name: str
    bank: BankName
    statement_type: StatementType
    expiration_date: Optional[date] = None
    

class CardMetrics(BaseModel):
    total_income: Decimal
    total_expenses: Decimal
    total_balance: Decimal