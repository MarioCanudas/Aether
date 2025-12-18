from datetime import date
from decimal import Decimal

from pydantic import BaseModel

from .bank_properties import BankName, StatementType


class Card(BaseModel):
    card_id: int | None = None
    user_id: int
    card_name: str
    card_bank: BankName
    statement_type: StatementType
    expiration_date: date | None = None


class CardMetrics(BaseModel):
    total_income: Decimal
    total_expenses: Decimal
    total_balance: Decimal
