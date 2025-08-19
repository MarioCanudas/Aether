from pydantic import BaseModel, field_validator, model_validator
from enum import Enum
from decimal import Decimal
from datetime import date
from typing import Optional, Dict, Any  
from .amounts import TransactionType
from .dates import Period

class GoalType(str, Enum):
    """
    Represents the type of a goal.
    >>> Values:
        BUDGET
        SAVINGS
        DEBT
        INCOME
        INVESTMENT
    """
    BUDGET = 'Presupuesto'
    SAVINGS = 'Ahorro'
    DEBT = 'Deuda'
    INCOME = 'Ingreso'
    INVESTMENT = 'Inversión'
    
    @property
    def transaction_type(self) -> TransactionType:
        match self:
            case GoalType.BUDGET:
                return TransactionType.EXPENSE
            case GoalType.SAVINGS:
                return TransactionType.INCOME
            case GoalType.DEBT:
                return TransactionType.EXPENSE
            case GoalType.INCOME:
                return TransactionType.INCOME
            case GoalType.INVESTMENT:
                return TransactionType.INCOME
    
    
class GoalStatus(str, Enum):
    """
    Represents the status of a goal.
    >>> Values:
        ACTIVE
        INACTIVE
        ACHIEVED
        FAILED
    """
    ACTIVE = 'Activo'
    INACTIVE = 'Inactivo'
    ACHIEVED = 'Cumplido'
    FAILED = 'Fallido'
    
    @property
    def icon(self) -> str:
        match self:
            case GoalStatus.ACHIEVED:
                return ':material/check_circle:'
            case GoalStatus.FAILED:
                return ':material/cancel:'
            case GoalStatus.ACTIVE:
                return ':material/hourglass_bottom:'
            case GoalStatus.INACTIVE:
                return ':material/hourglass_pause:'
            
    @property
    def color(self) -> str:
        match self:
            case GoalStatus.ACHIEVED:
                return 'green'
            case GoalStatus.FAILED:
                return 'red'
            case GoalStatus.ACTIVE:
                return 'orange'
            case GoalStatus.INACTIVE:
                return 'gray'


class Goal(BaseModel):
    user_id: int
    type: GoalType
    category_id: int
    amount: Decimal
    added_amount: Optional[Decimal] = None
    name: str
    period: Period
    status: GoalStatus = GoalStatus.ACTIVE
    related_transaction_type: Optional[TransactionType] = None
    
    @field_validator('amount')
    @classmethod
    def validate_amount(cls, amount: Decimal) -> Decimal:
        if amount <= 0:
            raise ValueError('Amount must be greater than 0')
        else:
            return amount.quantize(Decimal('0.01'))
        
    @model_validator(mode= 'after')
    def validate_related_transaction_type(self) -> 'Goal':
        if self.related_transaction_type is None:
            self.related_transaction_type = self.type.transaction_type
        
        return self
    
    def to_record(self) -> Dict[str, Any]:
        record = self.model_dump()
        
        record['type'] = self.type.value
        
        record['start_date'] = self.period.start_date
        record['end_date'] = self.period.end_date
        
        del record['period']
        
        if not self.added_amount:
            del record['added_amount']
        
        return record
    
    
class GoalInfo(BaseModel):
    goal_id: int
    name: str
    type: GoalType
    category: str
    amount: float
    added_amount: float
    start_date: date
    end_date: date
    status: GoalStatus
    current_amount: float
    remaining: float
    progress_porcentage: float
    
    @field_validator('progress_porcentage')
    @classmethod
    def validate_progress_porcentage(cls, progress_porcentage: float) -> float:
        if progress_porcentage < 0:
            raise ValueError('Progress porcentage must be greater than 0')
        else:
            return progress_porcentage
    
    @property
    def custom_current_amount_name(self) -> str:
        match self.type:
            case GoalType.BUDGET:
                return 'Spent'
            case GoalType.SAVINGS:
                return 'Savings'
            case GoalType.DEBT:
                return 'Debt payments'
            case GoalType.INCOME:
                return 'Income'
            case GoalType.INVESTMENT:
                return 'Invested'