from pydantic import BaseModel
from typing import Optional
from .bank_properties import BankName, StatementType

class Card(BaseModel):
    card_id: Optional[int] = None
    user_id: int
    name: str
    bank: BankName
    statement_type: StatementType