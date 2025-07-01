from streamlit import session_state
import pandas as pd
from typing import Literal
from services import PlottingService, DataProcessingService
from .base_controller import BaseController

class AnalysisController(BaseController):
    def __init__(self):
        super().__init__()
        self.data_processing_service = DataProcessingService()
        self.plotting_service = PlottingService()
    
    def get_bar_chart_monthly_total_by_category(self, category: Literal['Abono', 'Cargo']):
        monthly_results = session_state.all_monthly_results.copy()
        monthly_results['Month'] = monthly_results['Month'].astype(str)

        if category == 'Abono':
            return self.plotting_service.bar_chart_monthly_total_income(monthly_results)
        elif category == 'Cargo':
            return self.plotting_service.bar_chart_monthly_total_expenses(monthly_results)

    def get_bar_chart_daily_total_by_category(self, category: Literal['Abono', 'Cargo']):
        processed_data = session_state.all_processed_data.copy()
        processed_data['Date'] = pd.to_datetime(processed_data['Date'])
        
        avg_per_day = self.data_processing_service.process_daily_data_by_category(processed_data, category)
        
        if category == 'Abono':
            return self.plotting_service.bar_chart_daily_total_income(avg_per_day)
        elif category == 'Cargo':
            return self.plotting_service.bar_chart_daily_total_expenses(avg_per_day)
