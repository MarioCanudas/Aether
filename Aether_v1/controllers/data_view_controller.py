import pandas as pd
from typing import Optional, Literal, List, Dict
import logging
from services import TransactionsDBService, CategoryDBService
from models.amounts import TransactionType
from models.bank_properties import StatementType, BankName
from models.dates import Period
from models.records import TransactionRecord
from .base_controller import BaseController

logger = logging.getLogger(__name__)

class DataViewController(BaseController):
    def get_transactions_date_range(self) -> Period:
        user_id = self.user_session_service.current_user_id
        
        with self.quick_read_conn() as conn:
            transactions_db = TransactionsDBService(conn)
            
            period = transactions_db.get_transactions_period(user_id)
            
            return period
        
    def get_banks_in_transactions(self) -> List[str]:
        user_id = self.user_session_service.current_user_id
        
        with self.quick_read_conn() as conn:
            transactions_db = TransactionsDBService(conn)
            
            return transactions_db.get_unique_values(column= 'bank', user_id= user_id)
        
    def get_filtered_transactions(
            self, 
            period: Period, 
            banks: Optional[list[BankName]],
            statement_type: Optional[StatementType],
            amount_types: Optional[List[TransactionType]]
        ) -> pd.DataFrame:
        user_id = self.user_session_service.current_user_id
        
        with self.quick_read_conn() as conn:
            transactions_db = TransactionsDBService(conn)
            
            transactions = transactions_db.get_transactions(
                user_id= user_id,
                columns= ['transaction_id', 'date', 'description', 'amount', 'type', 'bank', 'statement_type', 'filename'],
                period= period,
                banks= banks,
                statement_type= statement_type,
                amount_types= amount_types,
                show_categories_names= True
            )
            
            return pd.DataFrame(transactions).sort_values(by= 'date', ascending= False)
        
    def get_categories(self, mapped: bool = False) -> List[str] | Dict[str, int]:        
        with self.quick_read_conn() as conn:
            categories_db = CategoryDBService(conn)
            
            if mapped:
                return categories_db.get_categories_by_user_mapped(self.user_id)
            else:
                return categories_db.get_categories_by_user(self.user_id)
                
    @staticmethod
    def _extract_modified_transactions(
            original_transactions: pd.DataFrame, 
            edited_transactions: pd.DataFrame
        ) -> Dict[str, List[TransactionRecord]]:
        """
        Extract modified, new, and deleted transactions.
        Returns a dictionary with 'new', 'modified', and 'deleted' keys.
        """
        df_og = original_transactions.copy()
        df_ed = edited_transactions.copy()
        
        # Get transaction IDs for comparison
        original_ids = set(df_og['transaction_id'].tolist())
        edited_ids = set(df_ed['transaction_id'].tolist())
        
        # Find deleted transactions (in original but not in edited)
        deleted_ids = original_ids - edited_ids
        deleted_transactions = df_og[df_og['transaction_id'].isin(deleted_ids)].to_dict(orient='records')
        
        # Find new transactions (in edited but not in original)
        new_ids = edited_ids - original_ids
        new_transactions = df_ed[df_ed['transaction_id'].isin(new_ids)].to_dict(orient='records')
        
        # Find modified transactions (in both but with different content)
        common_ids = original_ids & edited_ids
        modified_transactions = []
        
        for transaction_id in common_ids:
            original_row = df_og[df_og['transaction_id'] == transaction_id].iloc[0]
            edited_row = df_ed[df_ed['transaction_id'] == transaction_id].iloc[0]
            
            # Compare all columns except transaction_id
            comparison_cols = [col for col in original_row.index if col != 'transaction_id']
            if not original_row[comparison_cols].equals(edited_row[comparison_cols]):
                modified_transactions.append(edited_row.to_dict())
        
        return {
            'new': new_transactions,
            'modified': modified_transactions,
            'deleted': deleted_transactions
        }
        
    def modify_transactions(self, original_transactions: pd.DataFrame, edited_transactions: pd.DataFrame) -> None:
        modified_transactions = self._extract_modified_transactions(original_transactions, edited_transactions)
        
        if not modified_transactions:
            return
        
        # Chanche the categorie (str) to category_id (int)
        categories = self.get_categories(mapped= True)
        
        for transactions in modified_transactions.values():
            for transaction in transactions:
                transaction['category_id'] = categories[transaction['category']] if transaction['category'] else None
                transaction['user_id'] = self.user_id
                
                del transaction['category']
                
                if transaction['transaction_id'] is None or pd.isna(transaction['transaction_id']):
                    del transaction['transaction_id']
        
        with self.batch_conn() as conn:
            transactions_db = TransactionsDBService(conn)
            
            if modified_transactions['new']:
                transactions_db.add_records(modified_transactions['new'])
                
            if modified_transactions['modified']:
                transactions_db.update_transactions(modified_transactions['modified'])
                
            if modified_transactions['deleted']:
                transactions_db.delete_records(modified_transactions['deleted'])
