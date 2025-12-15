from pydantic import BaseModel
from enum import Enum
from typing import Optional, List, Any, Tuple, Dict
from datetime import date
from dateutil.relativedelta import relativedelta
from decimal import Decimal
from .amounts import TransactionType
from .bank_properties import BankName, StatementType

class DuplicateTransactionType(str, Enum):
    """
    >>> Values:
        EXACT: The transaction is an exact duplicate of another transaction.
        POTENTIAL: The transaction is a potential duplicate of another transaction.
        NULL: The transaction is not a duplicate.
    """
    
    EXACT = 'exact'
    POTENTIAL = 'potential'
    NULL = 'null'

class Transaction(BaseModel):
    transaction_id: Optional[int] = None
    user_id: int
    category_id: Optional[int] = None
    date: date
    description: Optional[str] = None
    amount: Decimal
    type: TransactionType
    bank: BankName
    card_id: Optional[int] = None
    statement_type: StatementType
    filename: Optional[str] = None
    duplicate_potential_state: bool = False
    
    @property
    def key_values(self) -> List[str]:
        return [
            'date',
            'amount',
            'type',
            'bank',
            'statement_type',
        ]
    
    @property
    def default_values(self) -> List[str]:
        return [
            'user_id',
            'date',
            'amount',
            'type',
            'bank',
            'statement_type',
            'duplicate_potential_state',
        ]
        
    @property
    def optional_values(self) -> List[str]:
        return [
            'transaction_id',
            'category_id',
            'description',
            'card_id',
            'filename',
        ]
    
    def __getitem__(self, key: str) -> Any:
        if key in self.default_values + self.optional_values:
            return getattr(self, key)
        else:
            raise KeyError(f"Key {key} not found in Transaction model")
        
    def __setitem__(self, key: str, value: Any) -> None:
        if key in self.default_values + self.optional_values:
            setattr(self, key, value)
        else:
            raise KeyError(f"Key {key} not found in Transaction model")
        
    def __delitem__(self, key: str) -> None:
        if key in self.default_values + self.optional_values:
            delattr(self, key)
        else:
            raise KeyError(f"Key {key} not found in Transaction model")
        
    def to_tuple(self, key: Optional[bool] = False) -> Tuple[Any, ...]:
        """
        Convert the Transaction model to a tuple.
        
        - key values: date, amount, type, bank, statement_type
        - default values: user_id, date, amount, type, bank, statement_type
        - optional values: transaction_id, category_id, description, card_id, filename
        
        Args:
            key (Optional[bool]): If True, return the tuple of key values. If False, return the tuple of default values and optional values.
            
        Returns:
            Tuple[Any, ...]: The tuple of values.
        """
        try:
            if key:
                return tuple(getattr(self, k) for k in self.key_values)
            else:
                return tuple(getattr(self, k) for k in self.default_values + self.optional_values)
        except Exception as e:
            raise ValueError(f"Error converting Transaction model to tuple: {e}")
        
    def dump_to_add(self) -> Dict[str, Any]:
        record = self.model_dump()
        
        del record['transaction_id']
        
        return record
    
    async def exact_duplicate(self, other: 'Transaction') -> bool:
        return all(getattr(self, k) == getattr(other, k) for k in self.key_values)
    
    async def potencial_duplicate(self, other: 'Transaction') -> bool:
        # If the transactions are exact duplicates, they are also potential duplicates.
        is_exact_duplicate = await self.exact_duplicate(other)
        
        if is_exact_duplicate:
            return True
        
        # First case: Gap between the dates is less than 3 days.
        if relativedelta(self.date, other.date).days <= 3:
            self_key = (self.amount, self.type, self.bank, self.statement_type)
            other_key = (other.amount, other.type, other.bank, other.statement_type)
            
            if self_key == other_key:
                return True
            else:
                return False
        # Second case: Amount difference is less than $25.00
        elif abs(self.amount - other.amount) <= Decimal('25.00'):
            self_key = (self.date, self.type, self.bank, self.statement_type)
            other_key = (other.date, other.type, other.bank, other.statement_type)
            
            if self_key == other_key:
                return True
            else:
                return False
        # Third case: Banks are different.
        elif self.bank != other.bank:
            self_key = (self.date, self.amount, self.type, self.statement_type)
            other_key = (other.date, other.amount, other.type, other.statement_type)
            
            if self_key == other_key:
                return True
            else:
                return False
        # Fourth case: Card IDs are different.
        elif self.card_id != other.card_id:
            self_key = (self.date, self.amount, self.type, self.bank, self.statement_type)
            other_key = (other.date, other.amount, other.type, other.bank, other.statement_type)
            
            if self_key == other_key:
                return True
            else:
                return False
        # Fifth case: Category IDs are different.
        elif self.category_id != other.category_id:
            self_key = (self.date, self.amount, self.type, self.bank, self.statement_type)
            other_key = (other.date, other.amount, other.type, other.bank, other.statement_type)
            
            if self_key == other_key:
                return True
            else:
                return False
        # Sixth case: Types are different.
        elif self.type != other.type:
            self_key = (self.date, abs(self.amount), self.bank, self.statement_type)
            other_key = (other.date, abs(other.amount), other.bank, other.statement_type)
            
            if self_key == other_key:
                return True
            else:
                return False
        else:
            return False
        