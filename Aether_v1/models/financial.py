from pydantic import BaseModel
from enum import Enum
from typing import Optional
from decimal import Decimal     

class FinancialStatus(str, Enum):
    EXCELLENT = "Excellent!"
    GOOD = "Good"
    REGULAR = "Regular"
    POOR = "Poor"
    
    @property
    def score(self) -> int:
        if self == FinancialStatus.EXCELLENT:
            return 100
        elif self == FinancialStatus.GOOD:
            return 75
        elif self == FinancialStatus.REGULAR:
            return 50
        else:
            return 25
        
    @property
    def icon(self) -> str:
        if self == FinancialStatus.EXCELLENT:
            return '🏆'
        elif self == FinancialStatus.GOOD:
            return '👍'
        elif self == FinancialStatus.REGULAR:
            return '👌'
        else:
            return '👎'
        
    @property
    def color(self) -> str:
        if self == FinancialStatus.EXCELLENT:
            return 'green'
        elif self == FinancialStatus.GOOD:
            return 'yellow'
        elif self == FinancialStatus.REGULAR:
            return 'orange'
        else:
            return 'red'
    
    
class FinancialAmountsSums(BaseModel):
    """
    This model is used to sum the financial amounts of the user, such as income, 
    withdrawal and savings. 
    
    It allows to calculate the balance of the user. 
    
    It not depends on the period of the sums, so can be used for all periods and avarage sums.
    """
    income: Decimal
    withdrawal: Decimal
    savings: Optional[Decimal]
    
    @property
    def balance(self) -> Decimal:
        return self.income + self.withdrawal
    
    def add_to_income(self, amount: Decimal) -> None:
        self.income += amount
    