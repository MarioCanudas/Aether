from pydantic import BaseModel, field_validator
from datetime import date
from decimal import Decimal
from typing import Optional
from .amounts import TransactionType

class TransactionTemplate(BaseModel):
    user_id: Optional[int]
    template_name: str
    template_description: Optional[str]
    transaction_date: Optional[date]
    transaction_type: TransactionType
    transaction_amount: Optional[Decimal]
    transaction_category_id: Optional[int]
    transaction_description: Optional[str]
    
    @field_validator('template_name')
    @classmethod
    def validate_template_name_length(cls, v: str) -> str:
        if len(v) > 50:
            raise ValueError('Template name must be less than 100 characters')
        else:
            return v
    
    @field_validator('template_description')
    @classmethod
    def validate_template_description_length(cls, v: str) -> str:
        if len(v) > 200:
            raise ValueError('Template description must be less than 200 characters')
        else:
            return v
        
    @field_validator('transaction_description')
    @classmethod
    def validate_transaction_description_length(cls, v: str) -> str:
        if len(v) > 200:
            raise ValueError('Transaction description must be less than 200 characters')
        else:
            return v
        