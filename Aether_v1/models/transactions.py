from pydantic import BaseModel
from typing import Optional, List, Any, Tuple, Dict
from datetime import date
from decimal import Decimal
from .amounts import TransactionType
from .bank_properties import BankName, StatementType

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
    
    @property
    def default_values(self) -> List[str]:
        return [
            'user_id',
            'category_id',
            'date',
            'description',
            'amount',
            'type',
            'bank',
        ]
        
    @property
    def optional_values(self) -> List[str]:
        return [
            'transaction_id',
            'category_id',
            'card_id',
            'description',
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
        
    def to_tuple(self) -> Tuple[Any, ...]:
        try:
            return Tuple(getattr(self, key) for key in self.default_values + self.optional_values)
        except Exception as e:
            raise ValueError(f"Error converting Transaction model to tuple: {e}")
        
    def dump_to_add(self) -> Dict[str, Any]:
        record = self.model_dump()
        
        del record['transaction_id']
        
        return record