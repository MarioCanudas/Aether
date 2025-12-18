import asyncio
import pandas as pd
from typing import Any, cast
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from psycopg2.extensions import connection
from utils import months_map
from services import TransactionsDBService, DataProcessingService, FinancialAnalysisService, PlottingService
from models.dates import Period
from models.financial import FinancialAmountsSums
from models.tables import AllTransactionsTable, MonthlyResultsTable
from models.views_data import HomeViewData, PeriodsOptions
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
        
        # Ensure validation if get_transactions returns mix of dict/module
        dicts_list = []
        for t in transactions:
            if isinstance(t, dict):
                dicts_list.append(t)
            else:
                dicts_list.append(t.model_dump())
        all_transactions = AllTransactionsTable(df = pd.DataFrame(dicts_list))
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
        
    async def _get_last_six_months_transactions(self, conn: connection) -> pd.DataFrame:
        transactions_db = TransactionsDBService(conn)
        
        period = transactions_db.get_transactions_period(self.user_id)
        period.start_date = period.end_date - timedelta(days= 180)  
        
        last_six_months = transactions_db.get_transactions(
            self.user_id,
            columns= ['date', 'amount', 'type'],
            period= period,
            order_col= 'date',
            order= 'desc',
            transaction_model= False,
        )
        

        if not last_six_months:
            return pd.DataFrame(
                {
                    'month-year': [],
                    'type': [],
                    'amount': [],
                    'month_label': [],
                    'month': [],
                }
            )
            
        last_six_months = pd.DataFrame(last_six_months)
        last_six_months['date'] = pd.to_datetime(last_six_months['date'])
        
        # Accessors like .dt can be tricky for static analysis in implicit pandas types
        date_series: Any = last_six_months['date']
        date_dt: Any = date_series.dt
        
        last_six_months['month'] = date_dt.month
        last_six_months['month-year'] = date_dt.strftime('%Y-%m')
        
        month_series: Any = last_six_months['month']
        last_six_months['month_label'] = month_series.apply(lambda x: months_map(x))
        
        grouped = last_six_months.groupby(['month-year', 'type'], as_index=False).agg(
            amount= ('amount', 'sum'),  
            month_label= ('month_label', 'first'),
            month= ('month', 'first'),
        )
        
        grouped = cast(pd.DataFrame, grouped)
        grouped['amount'] = grouped['amount'].apply(lambda x: abs(x))
        grouped['amount'] = cast(pd.Series, grouped['amount']).astype('float64')
        
        return grouped
        
    async def _get_last_six_months_balance(self, conn: connection) -> pd.DataFrame:
        transactions_db = TransactionsDBService(conn)
        
        period = transactions_db.get_transactions_period(self.user_id)
        period_start_date = period.end_date - timedelta(days= 180)

        # Fetch all transactions for the user
        all_transactions = transactions_db.get_transactions(
            self.user_id,
            columns=['date', 'amount', 'type'],
            transaction_model= False,
        )

        all_transactions = pd.DataFrame(all_transactions)
        all_transactions['date'] = pd.to_datetime(all_transactions['date'])

        # Create 'month-year' column for grouping
        all_transactions['month-year'] = all_transactions['date'].dt.strftime('%Y-%m')
        all_transactions['month'] = all_transactions['date'].dt.month
        all_transactions['month_label'] = all_transactions['month'].apply(lambda x: months_map(x))

        # Filter for income/expense or the first initial balance
        is_income_or_expense = all_transactions['type'].isin(['Abono', 'Cargo'])
        initial_mask = all_transactions['type'] == 'Saldo inicial'
        if initial_mask.any():
            first_initial_idx = all_transactions.loc[initial_mask, 'date'].idxmin()
            is_first_initial = all_transactions.index == first_initial_idx
        else:
            is_first_initial = pd.Series(False, index=all_transactions.index)

        all_transactions = all_transactions.loc[is_income_or_expense | is_first_initial].copy()

        # Group by month-year and aggregate monthly sum
        all_balances = all_transactions.groupby('month-year', as_index=False).agg(
            date=('date', 'first'),
            balance=('amount', 'sum'),
            month_label=('month_label', 'first'),
            month=('month', 'first'),
        )

        # Sort by month-year ascending and compute cumulative sum of balance
        all_balances = all_balances.sort_values(by='month-year', ascending=True)
        all_balances['balance'] = all_balances['balance'].cumsum()
        all_balances['balance'] = all_balances['balance'].astype('float64')

        all_balances['date'] = pd.to_datetime(all_balances['date'])
        all_balances = all_balances[all_balances['date'] >= pd.to_datetime(period_start_date)]

        return all_balances.reset_index(drop=True)
    
    def _modify_period(self, period: Period, period_options: PeriodsOptions) -> Period:
        today = date.today()
        
        match period_options:
            case PeriodsOptions.ALL_TIME:
                return period
            case PeriodsOptions.CURRENT_MONTH:
                return Period(start_date= today.replace(day= 1), end_date= today)
            case PeriodsOptions.LAST_MONTH:
                return Period(
                    start_date= today.replace(day= 1) - relativedelta(months= 1), 
                    end_date= today.replace(day= 1) - relativedelta(days= 1)
                )
            case PeriodsOptions.AVARAGE:
                return period
            case PeriodsOptions.SPECIFIC_PERIOD:
                return period
    
    async def get_home_view_data(self) -> HomeViewData:        
        with self.quick_read_conn() as conn:
            transactions_db = TransactionsDBService(conn)
            
            period = transactions_db.get_transactions_period(self.user_id)
            first_initial_balance = transactions_db.get_first_initial_balance(self.user_id)
            
            async with asyncio.TaskGroup() as tg:
                avg_financial_sums = tg.create_task(transactions_db.get_avg_all_time_sums(self.user_id))
                last_six_months = tg.create_task(self._get_last_six_months_transactions(conn))
                last_six_months_balance = tg.create_task(self._get_last_six_months_balance(conn))
            
            label = self.financial_analysis_service.get_financial_status_label(avg_financial_sums.result())
            tips = self.financial_analysis_service.get_financial_tips(label)
            donut_config = self.plotting_service.get_savings_donut_chart_config(label)
                
            async with asyncio.TaskGroup() as tg:
                all_time_sums = tg.create_task(
                    transactions_db.get_specific_period_sums(
                        self.user_id, 
                        period
                    )
                )
                current_month_sums = tg.create_task(
                    transactions_db.get_specific_period_sums(
                        self.user_id, 
                        self._modify_period(period, PeriodsOptions.CURRENT_MONTH))
                )
                last_month_sums = tg.create_task(
                    transactions_db.get_specific_period_sums(
                        self.user_id, 
                        self._modify_period(period, PeriodsOptions.LAST_MONTH))
                )
                income_vs_expenses_bar_chart = tg.create_task(self.plotting_service.get_income_vs_expenses_bar_chart(last_six_months.result()))
                balance_line_chart = tg.create_task(self.plotting_service.get_balance_line_chart(last_six_months_balance.result()))
                donut_score_chart = tg.create_task(self.plotting_service.get_plot_savings_donut_chart(donut_config))
                
        last_transactions = transactions_db.get_transactions(
            self.user_id, 
            columns= ['date', 'description', 'amount', 'type', 'bank'],
            limit= 5, 
            order_col= 'date', 
            order= 'desc',
            show_categories_names= True,
            transaction_model= False,
        )
        
        last_transactions = pd.DataFrame(last_transactions).sort_values(
            by= 'date', 
            ascending= False, 
        ).rename(
            columns= {
                'date': 'Date',
                'category': 'Category',
                'description': 'Description',
                'amount': 'Amount',
                'type': 'Type',
                'bank': 'Bank',
            }
        )
        
        last_transactions['Amount'] = last_transactions['Amount'].apply(lambda x: f"${x:,.2f}")
        
        all_time_sums = all_time_sums.result()
        all_time_sums.add_to_income(first_initial_balance['amount']) if first_initial_balance else None
            
        return HomeViewData(
            label= label,
            tips= tips,
            last_transactions= cast(pd.DataFrame, last_transactions[['Date', 'Category', 'Description', 'Amount', 'Type', 'Bank']]),
            donut_score_chart= donut_score_chart.result(),
            income_vs_expenses_bar_chart= income_vs_expenses_bar_chart.result(),
            balance_line_chart= balance_line_chart.result(),
            all_time_sums= all_time_sums,
            current_month_sums= current_month_sums.result(),
            last_month_sums= last_month_sums.result(),
            avarage_sums= avg_financial_sums.result()
        )
        
    def get_specific_period_sums(self, specific_period: Period) -> FinancialAmountsSums:
        with self.quick_read_conn() as conn:
            transactions_db = TransactionsDBService(conn)
            
            return asyncio.run(transactions_db.get_specific_period_sums(self.user_id, specific_period))
        