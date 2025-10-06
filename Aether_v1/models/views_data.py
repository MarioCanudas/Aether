from pydantic import BaseModel, ConfigDict, field_validator
import pandas as pd
from altair import Chart
from matplotlib.figure import Figure
from enum import Enum
from typing import List
from .financial import FinancialStatus, FinancialAmountsSums

class HomeViewData(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    label: FinancialStatus
    tips: List[str]
    last_transactions: pd.DataFrame
    donut_score_chart: Figure
    income_vs_expenses_bar_chart: Chart
    balance_line_chart: Chart
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
    
    @field_validator('income_vs_expenses_bar_chart')
    @classmethod
    def validate_income_vs_expenses_bar_chart(cls, income_vs_expenses_bar_chart: Chart) -> Chart:
        if not isinstance(income_vs_expenses_bar_chart, Chart):
            raise ValueError('Income vs expenses bar chart must be a Chart object')
        
        return income_vs_expenses_bar_chart
    
    @field_validator('balance_line_chart')
    @classmethod
    def validate_balance_line_chart(cls, balance_line_chart: Chart) -> Chart:
        if not isinstance(balance_line_chart, Chart):
            raise ValueError('Balance line chart must be a Chart object')
        
        return balance_line_chart
    
    @field_validator('last_transactions')
    @classmethod
    def validate_last_transactions(cls, last_transactions: pd.DataFrame) -> pd.DataFrame:
        if not isinstance(last_transactions, pd.DataFrame):
            raise ValueError('Last transactions must be a pandas DataFrame')
        
        return last_transactions
    
    
class HomePeriodsOptions(str, Enum):
    CURRENT_MONTH = 'Current Month'
    LAST_MONTH = 'Last Month'
    AVARAGE = 'Avarage'
    SPECIFIC_PERIOD = 'Specific Period'
    ALL_TIME = 'All Time'
    
    @classmethod
    def get_values(self) -> List[str]:
        return [option.value for option in self]
    