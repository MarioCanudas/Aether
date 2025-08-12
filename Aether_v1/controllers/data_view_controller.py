import pandas as pd
from datetime import date
from typing import Optional, Literal, List, Tuple
import logging
from services import TransactionsDBService, MonthlyResultDBService
from models.dates import Period
from .base_controller import BaseController

logger = logging.getLogger(__name__)

class DataViewController(BaseController):
    def get_transactions_date_range(self) -> Tuple[date, date]:
        user_id = self.user_session_service.current_user_id
        
        with self.quick_read_conn() as conn:
            transactions_db = TransactionsDBService(conn)
            
            return transactions_db.get_transactions_date_range(user_id)
        
    def get_banks_in_transactions(self) -> List[str]:
        user_id = self.user_session_service.current_user_id
        
        with self.quick_read_conn() as conn:
            transactions_db = TransactionsDBService(conn)
            
            return transactions_db.get_unique_values(column= 'bank', user_id= user_id)
        
    def get_filtered_transactions(
            self, 
            date_range: Tuple[date, date], 
            banks: Optional[list[str]],
            statement_type: Optional[Literal['debit', 'credit']],
            amount_type: Optional[List[Literal['Abono', 'Cargo', 'Saldo inicial']]]
        ) -> pd.DataFrame:
        user_id = self.user_session_service.current_user_id
        
        with self.quick_read_conn() as conn:
            transactions_db = TransactionsDBService(conn)
            
            transactions = transactions_db.get_transactions(
                user_id= user_id,
                columns= ['date', 'description', 'amount', 'type', 'bank', 'statement_type', 'filename'],
                period= date_range,
                banks= banks,
                statement_type= statement_type,
                amount_type= amount_type,
                show_categories_names= True
            )
            
            df = pd.DataFrame(transactions)
            
            # Set the order of the columns
            return df[['date', 'category', 'description', 'amount', 'type', 'bank', 'statement_type', 'filename']]
        
    def get_monthly_results(self) -> pd.DataFrame:
        user_id = self.user_session_service.current_user_id
        
        with self.quick_read_conn() as conn:
            monthly_results_db = MonthlyResultDBService(conn)
            
            monthly_results = monthly_results_db.get_monthly_results(
                user_id= user_id,
                columns= ['year_month', 'initial_balance', 'total_income', 'total_withdrawal', 'savings'],
            )
            
            df = pd.DataFrame(monthly_results)
            
            # Set the order of the columns
            return df[['year_month', 'initial_balance', 'total_income', 'total_withdrawal', 'savings']]
        
    