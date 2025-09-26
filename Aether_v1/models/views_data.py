from pydantic import BaseModel, ConfigDict, field_validator
from matplotlib.figure import Figure
from enum import Enum
from typing import List
from .financial import FinancialStatus, FinancialAmountsSums

class HomeViewData(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    label: FinancialStatus
    tips: List[str]
    donut_score_chart: Figure
    all_time_sums: FinancialAmountsSums
    current_month_sums: FinancialAmountsSums
    last_month_sums: FinancialAmountsSums
    avarage_sums: FinancialAmountsSums
    
    @field_validator('donut_score_chart')
    @classmethod
    def validate_donut_score_chart(cls, donut_score_chart: Figure) -> Figure:
        if not isinstance(donut_score_chart, Figure):
            raise ValueError('Donut score chart must be a Figure object')
        
        return donut_score_chart
    
    
class HomePeriodsOptions(str, Enum):
    CURRENT_MONTH = 'Current Month'
    LAST_MONTH = 'Last Month'
    AVARAGE = 'Avarage'
    SPECIFIC_PERIOD = 'Specific Period'
    ALL_TIME = 'All Time'
    
    @classmethod
    def get_values(self) -> List[str]:
        return [option.value for option in self]
    