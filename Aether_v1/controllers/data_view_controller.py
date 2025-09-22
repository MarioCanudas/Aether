import pandas as pd
from datetime import date
from typing import Optional, Literal, List, Tuple
import logging
from services import TransactionsDBService
from .base_controller import BaseController

logger = logging.getLogger(__name__)

class DataViewController(BaseController):
    def get_transactions_date_range(self) -> Tuple[date, date]:
        user_id = self.user_session_service.current_user_id
        
        with self.quick_read_conn() as conn:
            transactions_db = TransactionsDBService(conn)
            
            period = transactions_db.get_transactions_period(user_id)
            
            return period.to_tuple()
        
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