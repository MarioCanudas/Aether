import pandas as pd
from datetime import datetime, date
import logging
from .base_controller import BaseController

logger = logging.getLogger(__name__)

class DataViewController(BaseController):
    def user_have_transactions(self) -> bool:
        user_id = self.user_session_service.current_user_id
        
        if user_id is None:
            logger.warning("No user is logged in")
            return False
        
        with self.quick_read_scope() as db:
            transactions = db.get_records(
                table_name='transactions',
                where_conditions={'user_id': user_id},
                value_format='tuple',
                limit=1
            )
            return len(transactions) > 0
        
    def user_have_monthly_results(self) -> bool:
        user_id = self.user_session_service.current_user_id
        
        with self.quick_read_scope() as db:
            monthly_results = db.get_records(
                table_name='monthly_results',
                where_conditions={'user_id': user_id},
                value_format='tuple',
                limit=1
            )
            return len(monthly_results) > 0
        
    def get_transactions_date_range(self) -> tuple[date, date]:
        user_id = self.user_session_service.current_user_id
        
        query = """
            SELECT 
                MIN(date) as first_date,
                MAX(date) as last_date
            FROM transactions
            WHERE user_id = :user_id
        """
        
        with self.quick_read_scope() as db:
            result = db.custom_query(
                query= query,
                params= {'user_id': user_id},
                value_format= 'tuple'
            )
            date_range = list(result[0])
            date_range[0] = datetime.strptime(date_range[0], '%Y-%m-%d').date()
            date_range[1] = datetime.strptime(date_range[1], '%Y-%m-%d').date()
            
            return tuple(date_range)
        
    def get_filtered_transactions(self, date_range: tuple[date, date]) -> pd.DataFrame:
        user_id = self.user_session_service.current_user_id
        
        first_date, last_date = date_range
        first_date = first_date.strftime('%Y-%m-%d')
        last_date = last_date.strftime('%Y-%m-%d')
        
        query = """
            SELECT * FROM transactions
            WHERE user_id = :user_id
            AND date BETWEEN :first_date AND :last_date
        """
        
        with self.quick_read_scope() as db:
            transactions = db.custom_query(
                query= query,
                params= {'user_id': user_id, 'first_date': first_date, 'last_date': last_date},
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
        
    