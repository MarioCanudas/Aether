from pydantic import BaseModel
import pandas as pd
from typing import Optional, List, Any, Dict
from datetime import date
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
        
    def __hash__(self) -> int:
        def _to_hashable(value: Any):
            if isinstance(value, (list, tuple)):
                return tuple(_to_hashable(v) for v in value)
            
            try:
                hash(value)
                return value
            except TypeError:
                return repr(value)
            
        items = tuple(sorted((k, _to_hashable(v)) for k, v in self.model_dump().items()))
        return hash(tuple(items))
    
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
        if 0 < abs((self.date - other.date).days) <= 3:
            self_key = (self.amount, self.type, self.bank, self.card_id, self.statement_type)
            other_key = (other.amount, other.type, other.bank, other.card_id, other.statement_type)
            
            if self_key == other_key:
                return True
            else:
                return False
        # Second case: Amount difference is less than $25.00
        elif 0 < abs(self.amount - other.amount) <= Decimal('25.00'):
            self_key = (self.date, self.type, self.bank, self.card_id, self.statement_type)
            other_key = (other.date, other.type, other.bank, other.card_id, other.statement_type)
            
            if self_key == other_key:
                return True
            else:
                return False
        # Third case: Banks are different.
        elif self.bank != other.bank:
            self_key = (self.date, self.amount, self.type, self.card_id, self.statement_type)
            other_key = (other.date, other.amount, other.type, other.card_id, other.statement_type)
            
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
            self_key = (self.date, self.amount, self.type, self.bank, self.card_id, self.statement_type)
            other_key = (other.date, other.amount, other.type, other.bank, other.card_id, other.statement_type)
            
            if self_key == other_key:
                return True
            else:
                return False
        # Sixth case: Types are different.
        elif self.type != other.type:
            self_key = (self.date, abs(self.amount), self.bank, self.card_id, self.statement_type)
            other_key = (other.date, abs(other.amount), other.bank, other.card_id, other.statement_type)
            
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
    

class FilteredTransactionsResult(BaseModel):
    clean: List[Transaction] = []
    potential_duplicates_to_upload: List[Transaction] = []
    potential_duplicates_to_modify: List[Transaction] = []
    duplicated: List[Transaction] = []
    
    @property
    def potential_duplicates_to_upload_unique(self) -> List[Transaction]:
        return list(set(self.potential_duplicates_to_upload))
    
    @property
    def clean_df(self) -> pd.DataFrame:
        return pd.DataFrame([t.model_dump() for t in self.clean])
    
    @property
    def potential_duplicates_to_upload_df(self) -> pd.DataFrame:
        return pd.DataFrame([t.model_dump() for t in self.potential_duplicates_to_upload])
    
    @property
    def potential_duplicates_to_modify_df(self) -> pd.DataFrame:
        return pd.DataFrame([t.model_dump() for t in self.potential_duplicates_to_modify])
    
    @property
    def duplicated_df(self) -> pd.DataFrame:
        return pd.DataFrame([t.model_dump() for t in self.duplicated])