from typing import Optional, TypedDict
from decimal import Decimal
from datetime import date

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
    
class BudgetRecord(TypedDict):
    """
    Represents a budget record in the database.
    
    >>> user_id: int
     category_id: int
     amount: Decimal
     name: str
     start_date: date
     end_date: date
    """
    user_id: int
    category_id: int
    amount: Decimal
    name: str
    start_date: date
    end_date: date