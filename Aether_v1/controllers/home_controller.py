import asyncio
import pandas as pd
import matplotlib.pyplot as plt
from services import TransactionsDBService, DataProcessingService, FinancialAnalysisService, PlottingService
from models.financial import SummaryMetrics, FinancialSummary
from models.tables import AllTransactionsTable, MonthlyResultsTable
from models.dates import Period
from .base_controller import BaseController

class HomeController(BaseController):
    def __init__(self):
        super().__init__()
        self.data_processing_service = DataProcessingService()
        self.financial_analysis_service = FinancialAnalysisService()
        self.plotting_service = PlottingService()
        
    async def get_summary_metrics(self) -> SummaryMetrics:
        with self.quick_read_conn() as conn:
            transactions_db = TransactionsDBService(conn)
            
            transactions = transactions_db.get_transactions(self.user_id)
            
            all_transactions = AllTransactionsTable(df = pd.DataFrame(transactions))
            monthly_results: MonthlyResultsTable = self.data_processing_service.get_monthly_results(all_transactions)
            
            monthly_results.year_months = monthly_results.year_months.astype(str)
            
            async with asyncio.TaskGroup() as tg:
                total_savings = tg.create_task(
                    monthly_results.get_total_savings()
                )
                avg_income_per_month = tg.create_task(
                    monthly_results.get_avg_income_per_month()
                )
                avg_withdrawal_per_month = tg.create_task(
                    monthly_results.get_avg_withdrawal_per_month()
                )
            
            return SummaryMetrics(
                total_savings= total_savings.result(),
                avg_income_per_month= avg_income_per_month.result(),
                avg_withdrawal_per_month= avg_withdrawal_per_month.result()
            )
            
    def get_financial_summary(self) -> FinancialSummary:
        summary_metrics = asyncio.run(self.get_summary_metrics())
        
        label = self.financial_analysis_service.get_financial_status_label(summary_metrics)
        tips = self.financial_analysis_service.get_financial_tips(label)

        return FinancialSummary(
            summary_metrics= summary_metrics,
            label= label.value,
            tips= tips
        )
        
    def get_donut_score_chart(self) -> plt.Figure:
        summary_metrics = asyncio.run(self.get_summary_metrics())
        label = self.financial_analysis_service.get_financial_status_label(summary_metrics)
        donut_config = self.plotting_service.get_savings_donut_chart_config(label)
        
        return self.plotting_service.get_plot_savings_donut_chart(donut_config)
    
    def get_transactions_period(self) -> Period:
        with self.quick_read_conn() as conn:
            transactions_db = TransactionsDBService(conn)
            
            return transactions_db.get_transactions_period(self.user_id)
        
        