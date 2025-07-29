from typing import Optional, TypedDict

class TransactionRecord(TypedDict):
    date: str
    description: Optional[str]
    amount: float
    type: str
    bank: str
    statement_type: str
    filename: str