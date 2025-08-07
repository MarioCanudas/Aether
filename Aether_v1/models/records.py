from typing import Optional, TypedDict

class TransactionRecord(TypedDict):
    date: str
    description: Optional[str]
    amount: float
    type: str
    bank: str
    statement_type: str
    filename: str
    user_id: Optional[int]
    
class MonthlyResultRecord(TypedDict):
    year_month: str
    initial_balance: float
    total_income: float
    total_withdrawal: float
    savings: float
    user_id: Optional[int]