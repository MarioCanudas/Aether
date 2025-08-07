from enum import Enum
from pydantic import BaseModel, field_validator
from dataclasses import dataclass
from datetime import date
from typing import Optional, Dict, Tuple

class DateGroups(BaseModel):
    """
    Represents a date group with a year, month, and day.
    
    It's principally used to extract the date groups from the statement.
    """
    
    year: Optional[int] = None
    month: int
    day: int
    
    @property
    def has_year(self) -> bool:
        return self.year is not None
    
    @field_validator('year', 'month', 'day')
    @classmethod
    def validate_date_groups_instance(cls, v, info):
        """
        Validate that month and day are integers between 1 and 3,
        and that none of the values (year, month, day) are equal to each other,
        knowing that year can be None.
        """
        # Validate month and day are between 1 and 3
        if info.field_name in ('month', 'day'):
            if not (1 <= v <= 3):
                raise ValueError(f"The {info.field_name} must be between 1 and 3")
        
        # Check that none of the values are equal (ignoring None for year)
        year = v if info.field_name == 'year' else info.data.get('year')
        month = v if info.field_name == 'month' else info.data.get('month')
        day = v if info.field_name == 'day' else info.data.get('day')

        # Only compare if at least two values are not None
        values_to_compare = [x for x in (year, month, day) if x is not None]
        if len(values_to_compare) > 1:
            if len(set(values_to_compare)) != len(values_to_compare):
                raise ValueError("year, month, and day must all be different (year can be None)")

        return v
    
class Period(BaseModel):
    """Represents a period with a start and end date."""
    
    start_date: date
    end_date: date
    
    @field_validator('end_date')
    @classmethod
    def validate_dates_not_equal(cls, v, info):
        """
        Validate that the start and end dates are not equal.
        """
        start_date = info.data.get('start_date')
        end_date = v
        if start_date is not None and end_date is not None:
            if start_date == end_date:
                raise ValueError("Start date and end date cannot be the same")
        return v
    
    def to_tuple(self) -> Tuple[date, date]:
        return (self.start_date, self.end_date)

class PeriodRange(Enum):
    WEEKLY = 'Semanal'
    MONTHLY = 'Mensual'
    FORTNIGHTLY = 'Quincenal'
    BIMONTHLY = 'Bimestral'
    QUARTERLY = 'Trimestral'
    SEMIANNUAL = 'Semestral'
    ANNUAL = 'Anual'
    OTHER = 'Otro'

@dataclass(frozen=True)
class MonthPatterns:
    # Abbreviated month names to numeric month names
    abbr_to_num: Dict[str, str] # e.g. 'ENE' -> '01'
    # Numeric month names to abbreviated month names
    num_to_abbr: Dict[str, str] # e.g. '01' -> 'ENE'
    # Month names to numeric month names
    month_to_num: Dict[str, str] # e.g. 'Enero' -> '01'
    
            