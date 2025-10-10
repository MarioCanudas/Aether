from pydantic import BaseModel, ConfigDict, field_validator
import altair as alt

class AnalysisViewData(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    monthly_chart: alt.Chart
    daily_chart: alt.Chart
    
    @field_validator('monthly_chart')
    @classmethod
    def validate_monthly_chart(cls, monthly_chart: alt.Chart) -> alt.Chart:
        if not isinstance(monthly_chart, alt.Chart):
            raise ValueError('Monthly chart must be a altair Chart object')
        
        return monthly_chart
    
    @field_validator('daily_chart')
    @classmethod
    def validate_daily_chart(cls, daily_chart: alt.Chart) -> alt.Chart:
        if not isinstance(daily_chart, alt.Chart):
            raise ValueError('Daily chart must be a altair Chart object')
        
        return daily_chart
    
    