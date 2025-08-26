import pandas as pd
from typing import Literal
import logging
from services import PlottingService, DataProcessingService, TransactionsDBService, MonthlyResultDBService
from .base_controller import BaseController

logger = logging.getLogger(__name__)

class AnalysisController(BaseController):
    def __init__(self):
        super().__init__()
        self.data_processing_service = DataProcessingService()
        self.plotting_service = PlottingService()
        
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
        with self.quick_read_conn() as conn:
            monthly_results_db = MonthlyResultDBService(conn)
            
            monthly_results = monthly_results_db.get_monthly_results(self.user_id)
        
        monthly_results = pd.DataFrame(monthly_results)
        monthly_results['year_month'] = monthly_results['year_month'].astype(str)

        if category == 'Abono':
            return self.plotting_service.bar_chart_monthly_total_income(monthly_results)
        elif category == 'Cargo':
            return self.plotting_service.bar_chart_monthly_total_expenses(monthly_results)

    def get_bar_chart_daily_total_by_category(self, category: Literal['Abono', 'Cargo']):
        with self.quick_read_conn() as conn:
            transactions_db = TransactionsDBService(conn)
            
            transactions = transactions_db.get_transactions(self.user_id)
            
        transactions = pd.DataFrame(transactions)
        transactions['date'] = pd.to_datetime(transactions['date'])
        
        avg_per_day = self.data_processing_service.process_daily_data_by_category(transactions, category)
        
        if category == 'Abono':
            return self.plotting_service.bar_chart_daily_total_income(avg_per_day)
        elif category == 'Cargo':
            return self.plotting_service.bar_chart_daily_total_expenses(avg_per_day)
