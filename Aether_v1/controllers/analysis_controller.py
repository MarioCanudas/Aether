from streamlit import session_state
import pandas as pd
from typing import Literal
from services import PlottingService, DataProcessingService

class AnalysisController:
    def __init__(self):
        self.data_processing_service = DataProcessingService()
        self.plotting_service = PlottingService()
    
    def get_bar_chart_monthly_total_by_category(self, category: Literal['Income', 'Expenses']):
        monthly_results = session_state.all_monthly_results.copy()
        monthly_results['Month'] = monthly_results['Month'].astype(str)

        if category == 'Income':
            return self.plotting_service.bar_chart_monthly_total_income(monthly_results)
        elif category == 'Expenses':
            return self.plotting_service.bar_chart_monthly_total_expenses(monthly_results)

    def get_bar_chart_daily_total_by_category(self, category: Literal['Income', 'Expenses']):
        processed_data = session_state.all_processed_data.copy()
        processed_data['Date'] = pd.to_datetime(processed_data['Date'])
        
        avg_per_day = self.data_processing_service.process_daily_data_by_category(processed_data, category)
        
        if category == 'Income':
            return self.plotting_service.bar_chart_daily_total_income(avg_per_day)
        elif category == 'Expenses':
            return self.plotting_service.bar_chart_daily_total_expenses(avg_per_day)
