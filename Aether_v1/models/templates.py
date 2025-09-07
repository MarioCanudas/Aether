from pydantic import BaseModel, Field, field_validator
from enum import Enum
import json
from datetime import date
from decimal import Decimal
from typing import Optional, Dict, Any, TypedDict
from .amounts import TransactionType
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
    start_date: Optional[date] = Field(default= None)
    end_date: Optional[date] = Field(default= None)

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
        if 'start_date' in values and values['start_date'] is not None and not isinstance(values['start_date'], date):
            values['start_date'] = date.fromisoformat(values['start_date'])
        if 'end_date' in values and values['end_date'] is not None and not isinstance(values['end_date'], date):
            values['end_date'] = date.fromisoformat(values['end_date'])

        return cls(**values)
    
    def to_json(self) -> str:
        model_dump = self.model_dump()
        
        if 'start_date' in model_dump and model_dump['start_date'] is not None:
            model_dump['start_date'] = model_dump['start_date'].isoformat()
        if 'end_date' in model_dump and model_dump['end_date'] is not None:
            model_dump['end_date'] = model_dump['end_date'].isoformat()
        if 'amount' in model_dump and model_dump['amount'] is not None:
            model_dump['amount'] = float(model_dump['amount'])
            
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