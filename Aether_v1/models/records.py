from typing import TypedDict
from decimal import Decimal
from datetime import date
    
class MonthlyResultRecord(TypedDict):
    """
    Represents a monthly result record in the database.
    
    >>> user_id: int | None
    >>> year_month: str
    >>> initial_balance: float
    >>> total_income: float
    >>> total_withdrawal: float
    >>> savings: float
    """
    user_id: int | None
    year_month: str
    initial_balance: float
    total_income: float
    total_withdrawal: float
    savings: float
    
class BudgetRecord(TypedDict):
    """
    Represents a budget record in the database.
    
    >>> user_id: int
    >>> category_id: int
    >>> amount: Decimal
    >>> name: str
    >>> start_date: date
    >>> end_date: date
    """
    user_id: int
    category_id: int
    amount: Decimal
    name: str
    start_date: date
    end_date: date
