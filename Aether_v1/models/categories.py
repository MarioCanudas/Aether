from pydantic import BaseModel, field_validator
from enum import Enum
from typing import List, Optional

class CategoryGroup(str, Enum):
    HOGAR = 'Hogar'
    TRANSPORTE = 'Transporte'
    ALIMENTACION = 'Alimentación'
    OCIO = 'Ocio'
    SALUD = 'Salud'
    FINANZAS = 'Finanzas'
    SERVICIOS = 'Servicios'
    INGRESOS = 'Ingresos'
    OTROS = 'Otros'
    
    @classmethod
    def get_values(cls) -> List[str]:
        return [group.value for group in cls]
    
class NewCategory(BaseModel):
    group: CategoryGroup
    name: str
    description: Optional[str] = None
    
    @field_validator('name')
    @classmethod
    def validate_name_length(cls, v: str) -> str:
        if len(v) > 50:
            raise ValueError('Name must be less than 50 characters')
        else:
            return v
    
    @field_validator('description')
    @classmethod
    def validate_description_length(cls, v: str) -> str:
        if len(v) > 200:
            raise ValueError('Description must be less than 200 characters')
        else:
            return v