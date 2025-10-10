import pandas as pd
import asyncio
from typing import Literal
import logging
from services import PlottingService, DataProcessingService, TransactionsDBService
from models.tables import AllTransactionsTable, MonthlyResultsTable
from models.views_data import AnalysisViewData
from .base_controller import BaseController

logger = logging.getLogger(__name__)

class AnalysisController(BaseController):
    def __init__(self):
        super().__init__()
        self.data_processing_service = DataProcessingService()
        self.plotting_service = PlottingService()
    
    async def get_bar_chart_monthly_total_by_category(self, transactions_db: TransactionsDBService, category: Literal['Abono', 'Cargo']):        
        transactions = transactions_db.get_transactions(self.user_id)
        
        all_transactions = AllTransactionsTable(df = pd.DataFrame(transactions))
        monthly_results: MonthlyResultsTable = self.data_processing_service.get_monthly_results(all_transactions)
        
        df = monthly_results.df.copy()
        
        df['month_label'] = df['year_month'].dt.strftime('%b')
        df['year_month'] = df['year_month'].astype(str)
        df['total_withdrawal'] = df['total_withdrawal'].astype('float64')
        df['total_income'] = df['total_income'].astype('float64')

        if category == 'Abono':
            return self.plotting_service.bar_chart_monthly_total_income(df)
        elif category == 'Cargo':
            return self.plotting_service.bar_chart_monthly_total_expenses(df)

    async def get_bar_chart_daily_total_by_category(self, transactions_db: TransactionsDBService, category: Literal['Abono', 'Cargo']):
        transactions = transactions_db.get_transactions(self.user_id)
            
        transactions = pd.DataFrame(transactions)
        transactions['date'] = pd.to_datetime(transactions['date'])
        
        avg_per_day = self.data_processing_service.process_daily_data_by_category(transactions, category)
        avg_per_day = avg_per_day.reset_index(drop= True).reset_index()
        avg_per_day.columns = ['day', 'amount']
        
        avg_per_day['amount'] = avg_per_day['amount'].astype('float64')
        avg_per_day['day'] = avg_per_day['day'].astype('int64').apply(lambda x: x + 1)
        
        if category == 'Abono':
            return self.plotting_service.bar_chart_daily_total_income(avg_per_day)
        elif category == 'Cargo':
            return self.plotting_service.bar_chart_daily_total_expenses(avg_per_day)
        
    async def get_analysis_view_data(self, category: Literal['Abono', 'Cargo']) -> AnalysisViewData:
        with self.quick_read_conn() as conn:
            transactions_db = TransactionsDBService(conn)
            
            async with asyncio.TaskGroup() as tg:
                monthly_chart = tg.create_task(self.get_bar_chart_monthly_total_by_category(transactions_db, category))
                daily_chart = tg.create_task(self.get_bar_chart_daily_total_by_category(transactions_db, category))
                
            return AnalysisViewData(
                monthly_chart= monthly_chart.result(),
                daily_chart= daily_chart.result()
            )