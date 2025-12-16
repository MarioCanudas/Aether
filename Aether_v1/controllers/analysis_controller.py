import pandas as pd
import asyncio
import altair as alt
from datetime import date
from typing import Literal, List, Optional
import logging
from utils import modify_period
from services import PlottingService, DataProcessingService, TransactionsDBService
from constants.dates import MonthLabels
from models.dates import Period
from models.tables import AllTransactionsTable, MonthlyResultsTable
from models.views_data import AnalysisViewData, PeriodsOptions, AnalysisAmountsPerPeriod, AnalysisAmounts
from models.amounts import TransactionType
from .base_controller import BaseController

logger = logging.getLogger(__name__)

class AnalysisController(BaseController):
    def __init__(self):
        super().__init__()
        self.data_processing_service = DataProcessingService()
        self.plotting_service = PlottingService()
        
    def get_years(self) -> List[int]:
        with self.quick_read_conn() as conn:
            transactions_db = TransactionsDBService(conn)
            
            period = transactions_db.get_transactions_period(self.user_id)
            
            return sorted(period.get_available_years(), reverse= True)
    
    async def get_category_amount_bar_chart(self, transactions_db: TransactionsDBService, category: Literal['Abono', 'Cargo']) -> alt.Chart:
        transactions = transactions_db.get_transactions(
            self.user_id,
            columns=['amount'],
            show_categories_names=True,
            amount_types=[TransactionType(category)],
            transaction_model= False,
        )

        if not transactions:
            return None
        
        transactions = pd.DataFrame(transactions)

        transactions['category'] = transactions['category'].fillna('Sin categoría')
        transactions['amount'] = transactions['amount'].abs()

        amount_per_category = transactions.groupby('category').agg({'amount': 'sum'}).reset_index()
        amount_per_category['amount'] = amount_per_category['amount'].astype('float64')

        if len(amount_per_category) > 5:
            # Sort by amount descending and take top 5
            top_five = amount_per_category.sort_values('amount', ascending=False).head(5)
            # Collect "other" as sum of rest
            others = amount_per_category.sort_values('amount', ascending=False).iloc[5:]
            otras_sum = others['amount'].sum()
            # Only include "Otras" if there's anything left
            if otras_sum > 0:
                otras_row = pd.DataFrame({'category': ['Otras'], 'amount': [otras_sum]})
                amount_per_category = pd.concat([top_five, otras_row], ignore_index=True)
            else:
                amount_per_category = top_five.reset_index(drop=True)

        return self.plotting_service.category_amount_bar_chart(amount_per_category, category)
    
    async def get_monthly_bar_chart_avg_amount(self, transactions_db: TransactionsDBService, category: Literal['Abono', 'Cargo']) -> alt.Chart:        
        transactions = transactions_db.get_transactions(self.user_id)
        
        all_transactions = AllTransactionsTable(df = pd.DataFrame([t.model_dump() for t in transactions]))
        monthly_results: MonthlyResultsTable = self.data_processing_service.get_monthly_results(all_transactions)
        
        df = monthly_results.df.copy()
        
        df['month_label'] = df['year_month'].dt.strftime('%b')
        df['year_month'] = df['year_month'].astype(str)
        df['total_withdrawal'] = df['total_withdrawal'].astype('float64').apply(lambda x: abs(x))
        df['total_income'] = df['total_income'].astype('float64').apply(lambda x: abs(x))
        
        return self.plotting_service.monthly_bar_chart(df, category).properties(title='Per Month')

    async def get_daily_bar_chart_avg_amount(self, transactions_db: TransactionsDBService, category: Literal['Abono', 'Cargo']) -> Optional[alt.Chart]:
        transactions = transactions_db.get_transactions(self.user_id)
            
        if not transactions:
            return None
            
        transactions = pd.DataFrame([t.model_dump() for t in transactions])
        transactions['date'] = pd.to_datetime(transactions['date'])
        
        avg_per_day = self.data_processing_service.process_avg_daily_data_by_category(transactions, category)
        avg_per_day = avg_per_day.reset_index(drop= True).reset_index()
        avg_per_day.columns = ['day', 'amount']
        
        avg_per_day['amount'] = avg_per_day['amount'].astype('float64').apply(lambda x: abs(x))
        avg_per_day['day'] = avg_per_day['day'].astype('int64').apply(lambda x: x + 1)
        
        return self.plotting_service.daily_bar_chart(avg_per_day, category).properties(title='Per Day')
        
    def get_daily_bar_chart(self, category: Literal['Abono', 'Cargo'], year: int) -> Optional[alt.Chart]:
        with self.quick_read_conn() as conn:
            transactions_db = TransactionsDBService(conn)
            
            period = Period(
                start_date= date(year, 1, 1),
                end_date= date(year, 12, 31)
            )
            
            transactions = transactions_db.get_transactions(
                self.user_id, 
                period= period,
                amount_types= [TransactionType(category)]
            )
            
            if not transactions:
                return None
            
            print(transactions)
            
            transactions = pd.DataFrame([t.model_dump() for t in transactions])
            
            transactions['date'] = pd.to_datetime(transactions['date'])
            
            month_transactions = pd.DataFrame(columns= ['day', 'amount'])
            
            month_transactions['day'] = transactions['date'].dt.day
            month_transactions['amount'] = transactions['amount'].astype('float64').apply(lambda x: abs(x))
            
            month_transactions = month_transactions.groupby('day').agg({'amount': 'sum'}).reset_index()
            
        return self.plotting_service.daily_bar_chart(month_transactions, category)
    
    @staticmethod
    def _get_year_period(year: int) -> Period:
        return Period(
            start_date= date(year, 1, 1),
            end_date= date(year, 12, 31)
        )
        
    def get_monthly_bar_chart(self, category: Literal['Abono', 'Cargo'], year: int) -> Optional[alt.Chart]:
        with self.quick_read_conn() as conn:
            transactions_db = TransactionsDBService(conn)
            
            transactions = transactions_db.get_transactions(
                self.user_id,
                period= self._get_year_period(year),
                type= category
            )
            
            if not transactions:
                return None
            
            transactions = pd.DataFrame([t.model_dump() for t in transactions])
            transactions['date'] = pd.to_datetime(transactions['date'])
                        
            monthly_results = self.data_processing_service.get_monthly_results(AllTransactionsTable(df= transactions))
            
            df = monthly_results.df.copy()
        
            df['month_label'] = df['year_month'].dt.strftime('%b')
            df['year_month'] = df['year_month'].astype(str)
            df['total_withdrawal'] = df['total_withdrawal'].astype('float64').apply(lambda x: abs(x))
            df['total_income'] = df['total_income'].astype('float64').apply(lambda x: abs(x))
            
            return self.plotting_service.monthly_bar_chart(df, category)
        
    async def _get_acumulated_amounts(
            self, 
            category: Literal['Abono', 'Cargo'],
            transactions_db: TransactionsDBService,
            period: Period,
        ) -> AnalysisAmountsPerPeriod:
        first_initial_balance = transactions_db.get_first_initial_balance(self.user_id)
        
        async with asyncio.TaskGroup() as tg:
            all_time_sums = tg.create_task(transactions_db.get_specific_period_sums(self.user_id, period))
            current_month_sums = tg.create_task(
                transactions_db.get_specific_period_sums(
                    self.user_id, 
                    modify_period(period, PeriodsOptions.CURRENT_MONTH)
                )
            )
            last_month_sums = tg.create_task(
                transactions_db.get_specific_period_sums(
                    self.user_id, 
                    modify_period(period, PeriodsOptions.LAST_MONTH)
                )
            )
            avarage_sums = tg.create_task(transactions_db.get_avg_all_time_sums(self.user_id))
            
        if category == 'Abono':
            all_time_income = all_time_sums.result().income + first_initial_balance['amount'] if first_initial_balance else all_time_sums.result().income
            return AnalysisAmountsPerPeriod(
                all_time= all_time_income,
                current_month= current_month_sums.result().income,
                last_month= last_month_sums.result().income,
                avarage= avarage_sums.result().income
            )
        elif category == 'Cargo':
            return AnalysisAmountsPerPeriod(
                all_time= all_time_sums.result().withdrawal,
                current_month= current_month_sums.result().withdrawal,
                last_month= last_month_sums.result().withdrawal,
                avarage= avarage_sums.result().withdrawal
            )
        
    async def _get_max_amount(
            self, 
            category: Literal['Abono', 'Cargo'],
            transactions_db: TransactionsDBService,
        ) -> AnalysisAmountsPerPeriod:
        max_amounts = await transactions_db.get_max_amounts(self.user_id)
        
        if category == 'Abono':
            return max_amounts['Abono']
        elif category == 'Cargo':
            return max_amounts['Cargo']
        else:
            raise ValueError(f'Invalid category: {category}')
        
    async def _get_frecuency(
            self, 
            category: Literal['Abono', 'Cargo'],
            transactions_db: TransactionsDBService,
        ) -> AnalysisAmountsPerPeriod:
        frecuencys = await transactions_db.get_frecuencys(self.user_id) 
        
        if category == 'Abono':
            return frecuencys['Abono']
        elif category == 'Cargo':
            return frecuencys['Cargo']
        else:
            raise ValueError(f'Invalid category: {category}')
        
    async def get_analysis_view_data(self, category: Literal['Abono', 'Cargo']) -> AnalysisViewData:
        with self.quick_read_conn() as conn:
            transactions_db = TransactionsDBService(conn)
            period = transactions_db.get_transactions_period(self.user_id)
            
            async with asyncio.TaskGroup() as tg:
                amount_per_category_chart = tg.create_task(self.get_category_amount_bar_chart(transactions_db, category))
                avg_monthly_bar_chart = tg.create_task(self.get_monthly_bar_chart_avg_amount(transactions_db, category))
                avg_daily_bar_chart = tg.create_task(self.get_daily_bar_chart_avg_amount(transactions_db, category))
                acumulated_amounts = tg.create_task(self._get_acumulated_amounts(category, transactions_db, period))
                max_amount = tg.create_task(self._get_max_amount(category, transactions_db))
                frecuency = tg.create_task(self._get_frecuency(category, transactions_db))

            return AnalysisViewData(
                period= period,
                amount_per_category_chart= amount_per_category_chart.result(),
                avg_monthly_bar_chart= avg_monthly_bar_chart.result(),
                avg_daily_bar_chart= avg_daily_bar_chart.result(),
                analysis_amounts= AnalysisAmounts(
                    accumulated_amount= acumulated_amounts.result(),
                    max_amount= max_amount.result(),
                    frecuency= frecuency.result(),
                ),
            )
                
    async def get_amounts_in_specific_period(self, category: Literal['Abono', 'Cargo'], period: Period) -> AnalysisAmounts:
        with self.quick_read_conn() as conn:
            transactions_db = TransactionsDBService(conn)
            
            async with asyncio.TaskGroup() as tg:
                acumulated_amounts = tg.create_task(transactions_db.get_specific_period_sums(self.user_id, period))
                max_amount = tg.create_task(transactions_db.get_max_amount_in_specific_period(self.user_id, period))
                frecuency = tg.create_task(transactions_db.get_frecuency_in_specific_period(self.user_id, period))
           
        if category in ['Abono', 'Cargo']:
            return AnalysisAmounts(
                accumulated_amount= acumulated_amounts.result().income if category == 'Abono' else acumulated_amounts.result().withdrawal,
                max_amount= max_amount.result()[category],
                frecuency= frecuency.result()[category],
            )
        else:
            raise ValueError(f'Invalid category: {category}')