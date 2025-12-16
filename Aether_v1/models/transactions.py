from pydantic import BaseModel
from typing import Optional, List, Any, Dict
from datetime import date
from dateutil.relativedelta import relativedelta
from decimal import Decimal
from .amounts import TransactionType
from .bank_properties import BankName, StatementType

class TransactionKey(BaseModel):
    date: date
    amount: Decimal
    type: TransactionType
    bank: BankName
    statement_type: StatementType
    
    def __eq__(self, other: 'TransactionKey') -> bool:
        if not isinstance(other, TransactionKey):
            return False
        else:
            return self.model_dump() == other.model_dump()
        
    def __ne__(self, other: 'TransactionKey') -> bool:
        if not isinstance(other, TransactionKey):
            return True
        else:
            return self.model_dump() != other.model_dump()
    

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
    
    def __eq__(self, other: 'Transaction') -> bool:
        if not isinstance(other, Transaction):
            return False
        else:
            return self.model_dump() == other.model_dump()
        
    def __ne__(self, other: 'Transaction') -> bool:
        if not isinstance(other, Transaction):
            return True
        else:
            return self.model_dump() != other.model_dump()
    
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
        
    @property
    def key(self) -> TransactionKey:
        return TransactionKey(**{k: getattr(self, k) for k in self.key_values})
        
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
        

class DuplicateResult(BaseModel):
    transaction: Transaction
    exact_duplicates: List[Transaction] = []
    potential_duplicates: List[Transaction] = []
    
    @property
    def has_exact_duplicates(self) -> bool:
        return len(self.exact_duplicates) > 0
    
    @property
    def has_potential_duplicates(self) -> bool:
        return len(self.potential_duplicates) > 0