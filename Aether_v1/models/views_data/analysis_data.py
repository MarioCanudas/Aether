from pydantic import BaseModel, ConfigDict, field_validator
from decimal import Decimal
import altair as alt
from typing import Optional, List
from .all_views import PeriodsOptions
from ..dates import Period

class AnalysisAmountsPerPeriod(BaseModel):
    current_month: Decimal
    last_month: Decimal
    avarage: Decimal
    all_time: Decimal
    
    def __getitem__(self, key: PeriodsOptions) -> Optional[Decimal]:
        match key:
            case PeriodsOptions.ALL_TIME:
                return self.all_time
            case PeriodsOptions.CURRENT_MONTH:
                return self.current_month
            case PeriodsOptions.LAST_MONTH:
                return self.last_month
            case PeriodsOptions.AVARAGE:
                return self.avarage
            case _:
                raise ValueError(f'Invalid period option: {key}')
            
class AnalysisAmounts(BaseModel):
    accumulated_amount : Decimal | AnalysisAmountsPerPeriod
    max_amount : Decimal | AnalysisAmountsPerPeriod
    frecuency : int | AnalysisAmountsPerPeriod
    
    @property
    def values(self) -> List[Decimal | AnalysisAmountsPerPeriod]:
        return [self.accumulated_amount, self.max_amount, self.frecuency]
    
    def _validate_amounts_per_period(self) -> bool:
        for value in self.values:
            if isinstance(value, Decimal):
                return False
        else:
            return True  
    
    def __getitem__(self, key: PeriodsOptions) -> 'AnalysisAmounts':
        if not self._validate_amounts_per_period():
            raise ValueError('Accumulated amount, max amount and frecuency must be AnalysisAmountsPerPeriod')
        
        match key:
            case PeriodsOptions.ALL_TIME:
                return AnalysisAmounts(
                    accumulated_amount= self.accumulated_amount.all_time,
                    max_amount= self.max_amount.all_time,
                    frecuency= self.frecuency.all_time,
                )
            case PeriodsOptions.CURRENT_MONTH:
                return AnalysisAmounts(
                    accumulated_amount= self.accumulated_amount.current_month,
                    max_amount= self.max_amount.current_month,
                    frecuency= self.frecuency.current_month,
                )
            case PeriodsOptions.LAST_MONTH:
                return AnalysisAmounts(
                    accumulated_amount= self.accumulated_amount.last_month,
                    max_amount= self.max_amount.last_month,
                    frecuency= self.frecuency.last_month,
                )
            case PeriodsOptions.AVARAGE:
                return AnalysisAmounts(
                    accumulated_amount= self.accumulated_amount.avarage,
                    max_amount= self.max_amount.avarage,
                    frecuency= self.frecuency.avarage,
                )
            case _:
                raise ValueError(f'Invalid period option: {key}')

class AnalysisViewData(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    period: Period
    amount_per_category_chart: Optional[alt.Chart | alt.LayerChart]
    avg_monthly_bar_chart: Optional[alt.Chart]
    avg_daily_bar_chart: Optional[alt.Chart]
    analysis_amounts: AnalysisAmounts
    
    @field_validator('amount_per_category_chart')
    @classmethod
    def validate_amount_per_category_chart(cls, amount_per_category_chart: Optional[alt.Chart | alt.LayerChart]) -> Optional[alt.Chart | alt.LayerChart]:
        if (amount_per_category_chart is not None) and not isinstance(amount_per_category_chart, (alt.Chart, alt.LayerChart)):
            raise ValueError('Amount per category chart must be a Altair Chart object')
        
        return amount_per_category_chart
    
    @field_validator('avg_monthly_bar_chart')
    @classmethod
    def validate_avg_monthly_bar_chart(cls, avg_monthly_bar_chart: Optional[alt.Chart]) -> Optional[alt.Chart]:
        if (avg_monthly_bar_chart is not None) and not isinstance(avg_monthly_bar_chart, alt.Chart):
            raise ValueError('Average monthly bar chart must be a Altair Chart object')
        
        return avg_monthly_bar_chart
    
    @field_validator('avg_daily_bar_chart')
    @classmethod
    def validate_avg_daily_bar_chart(cls, avg_daily_bar_chart: Optional[alt.Chart]) -> Optional[alt.Chart]:
        if (avg_daily_bar_chart is not None) and not isinstance(avg_daily_bar_chart, alt.Chart):
            raise ValueError('Average daily bar chart must be a Altair Chart object')
        
        return avg_daily_bar_chart