from pydantic import BaseModel, field_validator
from enum import Enum
import json
from datetime import date
from decimal import Decimal
from typing import Optional, Dict, Any, TypedDict
from .amounts import TransactionType
from .goals import GoalType

class TemplateType(str, Enum):
    TRANSACTION = 'Transaction'
    GOAL = 'Goal'

    
class TransactionDefaultValues(BaseModel):
    date: Optional[date]
    type: TransactionType
    amount: Optional[Decimal]
    category_id: Optional[int]
    description: Optional[str]
    
    @field_validator('description')
    @classmethod
    def validate_description_length(cls, v: str) -> str:
        if len(v) > 200:
            raise ValueError('Description must be less than 200 characters')
        else:
            return v
    
    def to_json(self) -> str:
        model_dump = self.model_dump()
        
        return json.dumps({k:v for k, v in model_dump.items() if v is not None})
    
    
class GoalDefaultValues(BaseModel):
    name: str
    type: GoalType
    category_id: Optional[int]
    amount: Optional[Decimal]
    start_date: Optional[date]
    end_date: Optional[date]

    @field_validator('start_date', 'end_date', mode='after')
    @classmethod
    def validate_dates_structure(cls, values: dict[str, Any]) -> Dict[str, Any]:
        """
        Validates that if either start_date or end_date is provided, both must be present,
        and start_date must be less than end_date.
        """
        start_date = values.get('start_date')
        end_date = values.get('end_date')

        if (start_date and not end_date) or (not start_date and end_date):
            raise ValueError("Both start_date and end_date must be provided together.")
        else:
            if start_date >= end_date:
                raise ValueError("Start date must be less than end date.")

        return values
    
    def to_json(self) -> str:
        model_dump = self.model_dump()
        
        return json.dumps({k:v for k, v in model_dump.items() if v is not None})
    
    
class TemplateRecord(TypedDict):
    """
    Represents a template record in the database.
    
    >>> Values:
    user_id: Optional[int]
    template_name: str
    template_description: Optional[str]
    template_type: TemplateType
    default_values: str
    """
    user_id: Optional[int]
    template_name: str
    template_description: Optional[str]
    template_type: TemplateType
    default_values: str
    
    
class Template(BaseModel):
    user_id: Optional[int]
    template_name: str
    template_description: Optional[str]
    template_type: TemplateType
    default_values: TransactionDefaultValues | GoalDefaultValues
    
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
    
    def to_record(self) -> TemplateRecord:
        record : TemplateRecord = {
            'user_id': self.user_id,
            'template_name': self.template_name,
            'template_description': self.template_description,
            'template_type': self.template_type,
            'default_values': self.default_values.to_json()
        }
        return record

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
        