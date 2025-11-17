import asyncio
from typing import List
import pandas as pd
from altair import Chart
from datetime import date
from dateutil.relativedelta import relativedelta
from utils import months_map
from services import CardsDBService, TransactionsDBService, PlottingService
from models.bank_properties import BankName, StatementType
from models.cards import Card, CardMetrics
from models.amounts import TransactionType
from models.records import TransactionRecord
from models.views_data import CardViewData
from .base_controller import BaseController

class CardsViewController(BaseController):
    def add_card(self, name: str, bank: BankName, statement_type: StatementType, expiration_date: date) -> None:
        card = Card(user_id= self.user_id, name= name, bank= bank, statement_type= statement_type, expiration_date= expiration_date)
        
        with self.session_conn() as conn:
            cards_db = CardsDBService(conn)
            
            cards_db.add_card(card)
    
    def get_cards(self, only_name: bool = False) -> List[Card] | List[str]:
        with self.quick_read_conn() as conn:
            cards_db = CardsDBService(conn)
            
            cards = cards_db.get_cards(self.user_id)
        
        if only_name:
            return [card.name for card in cards]
        else:
            return cards
        
    def get_card_by_name(self, name: str) -> Card:
        with self.quick_read_conn() as conn:
            cards_db = CardsDBService(conn)
            
            card_id = cards_db.find_id(name= name, user_id= self.user_id)
            
            return cards_db.get_card_by_id(self.user_id, card_id)
        
    async def get_income_vs_expenses_chart(self, transactions: List[TransactionRecord]) -> Chart | None:
        df = pd.DataFrame(transactions)
        
        if df.empty:
            return None
        
        df['date'] = pd.to_datetime(df['date'])
        
        today = date.today()
        start_date = today - relativedelta(months= 6)
        end_date = today
        
        df = df[df['date'].between(pd.to_datetime(start_date), pd.to_datetime(end_date))]
        df['month'] = df['date'].dt.month
        df['month-year'] = df['date'].dt.strftime('%Y-%m')
        df['month_label'] = df['month'].apply(lambda x: months_map(x))
        
        grouped = df.groupby(['month-year', 'type'], as_index=False).agg(
            amount= ('amount', 'sum'),  
            month_label= ('month_label', 'first'),
            month= ('month', 'first'),
        )
        
        grouped['amount'] = grouped['amount'].apply(lambda x: abs(x))
        grouped['amount'] = grouped['amount'].astype('float64')
        
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
            
            transactions = transactions_db.get_transactions(user_id= self.user_id, show_categories_names= True, card_id= card_id)
            
            return CardViewData(
                metrics= metrics, 
                transactions= transactions, 
                income_vs_expenses_chart= await self.get_income_vs_expenses_chart(transactions)
            )