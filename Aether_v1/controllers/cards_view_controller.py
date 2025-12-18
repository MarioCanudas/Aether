import asyncio
from typing import Any, cast
import pandas as pd
from altair import Chart
from datetime import date
from dateutil.relativedelta import relativedelta
from utils import months_map
from services import CardsDBService, TransactionsDBService, PlottingService
from models.bank_properties import BankName, StatementType
from models.cards import Card, CardMetrics
from models.amounts import TransactionType
from models.transactions import Transaction
from models.views_data import CardViewData
from .base_controller import BaseController

class CardsViewController(BaseController):
    def add_card(self, card_name: str, card_bank: BankName, statement_type: StatementType, expiration_date: date) -> None:
        card = Card(user_id= self.user_id, card_name= card_name, card_bank= card_bank, statement_type= statement_type, expiration_date= expiration_date)
        
        with self.session_conn() as conn:
            cards_db = CardsDBService(conn)
            
            cards_db.add_card(card)
    
    def get_cards(self, only_name: bool = False) -> list[Card] | list[str]:
        with self.quick_read_conn() as conn:
            cards_db = CardsDBService(conn)
            
            cards = cards_db.get_cards(self.user_id)
        
        if only_name:
            return [card.card_name for card in cards]
        else:
            return cards
        
    def get_card_by_name(self, card_name: str) -> Card:
        with self.quick_read_conn() as conn:
            cards_db = CardsDBService(conn)
            
            card_id = cards_db.find_id(card_name= card_name, user_id= self.user_id)
            if card_id is None:
                raise ValueError(f"Card {card_name} not found")
            
            card = cards_db.get_card_by_id(self.user_id, card_id)
            if card is None:
                 raise ValueError(f"Card with id {card_id} not found")
            return card
        
    async def get_income_vs_expenses_chart(self, transactions: list[dict[str, Any]] | list[Transaction]) -> Chart | None:
        if not transactions:
            return None
        
        # Ensure we work with dicts
        dicts_list: list[dict[str, Any]] = []
        for t in transactions:
            if isinstance(t, Transaction):
                dicts_list.append(t.model_dump())
            else:
                dicts_list.append(t)
                
        df = pd.DataFrame(dicts_list)
        
        df['date'] = pd.to_datetime(df['date'])
        
        today = date.today()
        start_date = today - relativedelta(months= 6)
        end_date = today
        
        # Casting to Any or specific pandas types to avoid type checker errors with partial pandas stubs
        date_series: Any = df['date']
        df = df[date_series.between(pd.to_datetime(start_date), pd.to_datetime(end_date))]
        
        # Accessors in pandas types often cause issues in strict mode, cast to Any for pragmatism if stubs are missing
        # Accessors in pandas types often cause issues in strict mode, cast to Any for pragmatism if stubs are missing
        date_dt = cast(pd.Series, df['date']).dt
        df['month'] = date_dt.month
        df['month-year'] = date_dt.strftime('%Y-%m')
        
        month_series = cast(pd.Series, df['month'])
        df['month_label'] = month_series.apply(lambda x: months_map(x))
        
        grouped = df.groupby(['month-year', 'type'], as_index=False).agg(
            amount= ('amount', 'sum'),  
            month_label= ('month_label', 'first'),
            month= ('month', 'first'),
        )
        
        grouped = cast(pd.DataFrame, grouped)
        
        # Fix assignment to new column or slice
        amount_series = cast(pd.Series, grouped['amount'])
        grouped['amount'] = amount_series.apply(lambda x: abs(x))
        grouped['amount'] = cast(pd.Series, grouped['amount']).astype('float64')
        
        plotting_service = PlottingService()
        
        async with asyncio.TaskGroup() as tg:
            income_vs_expenses_chart = tg.create_task(plotting_service.get_income_vs_expenses_bar_chart(grouped))
        
        return income_vs_expenses_chart.result()
        
    async def get_card_view_data(self, card_id: int) -> CardViewData:
        with self.quick_read_conn() as conn:
            transactions_db = TransactionsDBService(conn)
            
            income = transactions_db.get_sum(column= 'amount', card_id= card_id, type= TransactionType.INCOME)
            expenses = transactions_db.get_sum(column= 'amount', card_id= card_id, type= TransactionType.EXPENSE)
            balance = income - expenses
            
            metrics = CardMetrics(total_income= income, total_expenses= expenses, total_balance= balance)
            
            transactions = cast(list[dict[str, Any]], transactions_db.get_transactions(
                user_id= self.user_id, 
                show_categories_names= True, 
                card_id= card_id, 
                order_col='date', 
                order='desc',
                limit= 5,
                transaction_model= False,
            ))
            
            return CardViewData(
                metrics= metrics, 
                transactions= transactions, 
                income_vs_expenses_chart= await self.get_income_vs_expenses_chart(transactions)
            )