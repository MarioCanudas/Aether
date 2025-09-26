import asyncio
import pandas as pd
from psycopg2.extensions import connection
from services import TransactionsDBService, DataProcessingService, FinancialAnalysisService, PlottingService
from models.dates import Period
from models.financial import FinancialAmountsSums
from models.tables import AllTransactionsTable, MonthlyResultsTable
from models.views_data import HomeViewData
from .base_controller import BaseController

class HomeController(BaseController):
    def __init__(self):
        super().__init__()
        self.data_processing_service = DataProcessingService()
        self.financial_analysis_service = FinancialAnalysisService()
        self.plotting_service = PlottingService()
        
    async def _get_avg_financial_sums(self, conn: connection) -> FinancialAmountsSums:
        transactions_db = TransactionsDBService(conn)
        
        transactions = transactions_db.get_transactions(self.user_id)
        
        all_transactions = AllTransactionsTable(df = pd.DataFrame(transactions))
        monthly_results: MonthlyResultsTable = self.data_processing_service.get_monthly_results(all_transactions)
        
        monthly_results.year_months = monthly_results.year_months.astype(str)
        
        async with asyncio.TaskGroup() as tg:
            avg_savings_per_month = tg.create_task(
                monthly_results.get_avg_savings_per_month()
            )
            avg_income_per_month = tg.create_task(
                monthly_results.get_avg_income_per_month()
            )
            avg_withdrawal_per_month = tg.create_task(
                monthly_results.get_avg_withdrawal_per_month()
            )
        
        return FinancialAmountsSums(
                income= avg_income_per_month.result(),
                withdrawal= avg_withdrawal_per_month.result(),
                savings= avg_savings_per_month.result(),
            )
    
    async def get_home_view_data(self) -> HomeViewData:        
        with self.quick_read_conn() as conn:
            avg_financial_sums = await self._get_avg_financial_sums(conn)
            
            label = self.financial_analysis_service.get_financial_status_label(avg_financial_sums)
            tips = self.financial_analysis_service.get_financial_tips(label)
            donut_config = self.plotting_service.get_savings_donut_chart_config(label)
            
            transactions_db = TransactionsDBService(conn)
                
            async with asyncio.TaskGroup() as tg:
                all_time_sums = tg.create_task(transactions_db.get_all_time_sums(self.user_id))
                current_month_sums = tg.create_task(transactions_db.get_current_month_sums(self.user_id))
                last_month_sums = tg.create_task(transactions_db.get_last_month_sums(self.user_id))
                donut_score_chart = tg.create_task(self.plotting_service.get_plot_savings_donut_chart(donut_config))
            
        return HomeViewData(
            label= label,
            tips= tips,
            donut_score_chart= donut_score_chart.result(),
            all_time_sums= all_time_sums.result(),
            current_month_sums= current_month_sums.result(),
            last_month_sums= last_month_sums.result(),
            avarage_sums= avg_financial_sums
        )
        
    def get_specific_period_sums(self, specific_period: Period) -> FinancialAmountsSums:
        with self.quick_read_conn() as conn:
            transactions_db = TransactionsDBService(conn)
            
            return transactions_db.get_specific_period_sums(self.user_id, specific_period)
        