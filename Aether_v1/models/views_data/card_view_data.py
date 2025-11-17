from pydantic import BaseModel, ConfigDict, field_validator
import pandas as pd
from typing import List, Optional
from altair import Chart
from ..cards import CardMetrics
from ..records import TransactionRecord

class CardViewData(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    metrics: CardMetrics
    transactions: List[TransactionRecord]
    income_vs_expenses_chart: Optional[Chart] = None
    
    @field_validator('income_vs_expenses_chart')
    @classmethod
    def validate_income_vs_expenses_chart(cls, income_vs_expenses_chart: Optional[Chart]) -> Optional[Chart]:
        if (income_vs_expenses_chart is not None) and not isinstance(income_vs_expenses_chart, Chart):
            raise ValueError('Income vs expenses chart must be a Altair Chart object')
        
        return income_vs_expenses_chart
    
    def get_last_transactions(self, in_df: bool = False) -> List[TransactionRecord] | pd.DataFrame:
        if in_df:
            return pd.DataFrame(self.transactions[:5])
        else:
            return self.transactions[:5]
