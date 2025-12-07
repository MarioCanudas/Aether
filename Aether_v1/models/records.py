from typing import Optional, TypedDict, List, Tuple, Any
from decimal import Decimal
from datetime import date

# TODO: Remove this typed dict and use the Transaction model
class TransactionRecord(TypedDict):
    """
    Represents a transaction record in the database.
    
    >>> user_id: Optional[int]
    >>> date: str
    >>> description: Optional[str]
    >>> category_id: Optional[int]
    >>> category: Optional[str]
    >>> amount: float
    >>> type: str
    >>> bank: str
    >>> statement_type: str
    >>> filename: Optional[str]
    """
    user_id: Optional[int] = None
    date: str
    description: Optional[str] = None
    category_id: Optional[int] = None
    category: Optional[str] = None
    amount: Decimal | float
    type: str
    bank: str
    card_id: Optional[int] = None
    statement_type: str
    filename: Optional[str] = None
    
class MonthlyResultRecord(TypedDict):
    """
    Represents a monthly result record in the database.
    
    >>> user_id: Optional[int]
    >>> year_month: str
    >>> initial_balance: float
    >>> total_income: float
    >>> total_withdrawal: float
    >>> savings: float
    """
    user_id: Optional[int]
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