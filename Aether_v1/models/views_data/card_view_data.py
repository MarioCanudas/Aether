from pydantic import BaseModel, ConfigDict, field_validator
import pandas as pd
from typing import Any
from altair import Chart
from ..cards import CardMetrics

class CardViewData(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    metrics: CardMetrics
    transactions: list[dict[str, Any]]
    income_vs_expenses_chart: Chart | None = None
    
    @field_validator('income_vs_expenses_chart')
    @classmethod
    def validate_income_vs_expenses_chart(cls, income_vs_expenses_chart: Chart | None) -> Chart | None:
        if (income_vs_expenses_chart is not None) and not isinstance(income_vs_expenses_chart, Chart):
            raise ValueError('Income vs expenses chart must be a Altair Chart object')
        
        return income_vs_expenses_chart
    
    def get_last_transactions(self, in_df: bool = False) -> list[dict[str, Any]] | pd.DataFrame:
        if in_df:
            return pd.DataFrame(self.transactions[:5])
        else:
            return self.transactions[:5]
