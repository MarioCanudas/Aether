from pydantic import BaseModel, Field, field_validator
from enum import Enum
import json
from datetime import date
from decimal import Decimal
from typing import Optional, Dict, Any, TypedDict
from .amounts import TransactionType
from .dates import PeriodRange
from .goals import GoalType

class TemplateType(str, Enum):
    TRANSACTION = 'transaction'
    GOAL = 'goal'

    
class TransactionDefaultValues(BaseModel):
    transaction_date: Optional[date] = Field(default= None)
    type: TransactionType
    amount: Optional[Decimal] = Field(default= None)
    category_id: Optional[int] = Field(default= None)
    description: Optional[str] = Field(default= None, max_length= 200)
    
    @classmethod
    def from_dict(cls, values: Dict[str, Any]) -> 'TransactionDefaultValues':
        """
        Deserialize a dictionary into a TransactionDefaultValues instance.

        Ensures that the resulting dictionary has the correct types
        for each field as expected by the TransactionDefaultValues model.
        """

        # Explicitly convert fields to the expected types if necessary
        if 'type' in values and not isinstance(values['type'], TransactionType):
            values['type'] = TransactionType(values['type'])
        if 'amount' in values and values['amount'] is not None and not isinstance(values['amount'], Decimal):
            values['amount'] = Decimal(str(values['amount']))
        if 'transaction_date' in values and values['transaction_date'] is not None and not isinstance(values['transaction_date'], date):
            values['transaction_date'] = date.fromisoformat(values['transaction_date'])
        if 'category_id' in values and values['category_id'] is not None and not isinstance(values['category_id'], int):
            values['category_id'] = int(values['category_id'])
        if 'description' in values and values['description'] is not None and not isinstance(values['description'], str):
            values['description'] = str(values['description'])

        return cls(**values)
    
    def to_json(self) -> str:
        model_dump = self.model_dump()
        
        if 'transaction_date' in model_dump and model_dump['transaction_date'] is not None:
            model_dump['transaction_date'] = model_dump['transaction_date'].isoformat()
        if 'amount' in model_dump and model_dump['amount'] is not None:
            model_dump['amount'] = float(model_dump['amount'])
            
        return json.dumps({k:v for k, v in model_dump.items() if v is not None})
    
    
class GoalDefaultValues(BaseModel):
    name: str
    type: GoalType
    category_id: Optional[int] = Field(default= None)
    amount: Optional[Decimal] = Field(default= None)
    period_range: Optional[PeriodRange] = Field(default= None)
    
    @classmethod
    def from_dict(cls, values: Dict[str, Any]) -> 'GoalDefaultValues':
        """
        Deserialize a dictionary into a GoalDefaultValues instance.

        Ensures that the resulting dictionary has the correct types
        for each field as expected by the GoalDefaultValues model.
        """

        # Explicitly convert fields to the expected types if necessary
        if 'type' in values and not isinstance(values['type'], GoalType):
            values['type'] = GoalType(values['type'])
        if 'amount' in values and values['amount'] is not None and not isinstance(values['amount'], Decimal):
            values['amount'] = Decimal(str(values['amount']))
        if 'period_range' in values and values['period_range'] is not None and not isinstance(values['period_range'], PeriodRange):
            values['period_range'] = PeriodRange(values['period_range'])

        return cls(**values)
    
    def to_json(self) -> str:
        model_dump = self.model_dump()
    
        if 'amount' in model_dump and model_dump['amount'] is not None:
            model_dump['amount'] = float(model_dump['amount'])
        if 'period_range' in model_dump and model_dump['period_range'] is not None:
            model_dump['period_range'] = model_dump['period_range'].value
            
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