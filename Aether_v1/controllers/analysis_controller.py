from streamlit import session_state
import pandas as pd
from typing import Literal
import logging
from services import PlottingService, DataProcessingService
from .base_controller import BaseController

logger = logging.getLogger(__name__)

class AnalysisController(BaseController):
    def __init__(self):
        super().__init__()
        self.data_processing_service = DataProcessingService()
        self.plotting_service = PlottingService()
        
    def user_have_transactions(self) -> bool:
        user_id = self.user_session_service.current_user_id
        
        if user_id is None:
            logger.warning("No user is logged in")
            return False
        
        with self.quick_read_scope() as db:
            transactions = db.get_records(
                table_name='transactions',
                where_conditions={'user_id': user_id},
                value_format='tuple',
                limit=1
            )
            return len(transactions) > 0
        
    def user_have_monthly_results(self) -> bool:
        user_id = self.user_session_service.current_user_id
        
        with self.quick_read_scope() as db:
            monthly_results = db.get_records(
                table_name='monthly_results',
                where_conditions={'user_id': user_id},
                value_format='tuple',
                limit=1
            )
            return len(monthly_results) > 0
        
    def get_transactions(self) -> pd.DataFrame:
        user_id = self.user_session_service.current_user_id
        
        with self.quick_read_scope() as db:
            transactions = db.get_records(
                table_name='transactions',
                where_conditions={'user_id': user_id},
                value_format='dataframe'
            )
            return transactions
        
    def get_monthly_results(self) -> pd.DataFrame:
        user_id = self.user_session_service.current_user_id
        
        with self.quick_read_scope() as db:
            monthly_results = db.get_records(
                table_name='monthly_results',
                where_conditions={'user_id': user_id},
                value_format='dataframe'
            )
            return monthly_results
    
    def get_bar_chart_monthly_total_by_category(self, category: Literal['Abono', 'Cargo']):
        monthly_results = self.get_monthly_results()
        monthly_results['year_month'] = monthly_results['year_month'].astype(str)

        if category == 'Abono':
            return self.plotting_service.bar_chart_monthly_total_income(monthly_results)
        elif category == 'Cargo':
            return self.plotting_service.bar_chart_monthly_total_expenses(monthly_results)

    def get_bar_chart_daily_total_by_category(self, category: Literal['Abono', 'Cargo']):
        transactions = self.get_transactions()
        transactions['date'] = pd.to_datetime(transactions['date'])
        
        avg_per_day = self.data_processing_service.process_daily_data_by_category(transactions, category)
        
        if category == 'Abono':
            return self.plotting_service.bar_chart_daily_total_income(avg_per_day)
        elif category == 'Cargo':
            return self.plotting_service.bar_chart_daily_total_expenses(avg_per_day)
