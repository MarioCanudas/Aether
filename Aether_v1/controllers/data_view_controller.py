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
            amount_type: Optional[List[TransactionType]]
        ) -> pd.DataFrame:
        user_id = self.user_session_service.current_user_id
        
        with self.quick_read_conn() as conn:
            transactions_db = TransactionsDBService(conn)
            
            transactions = transactions_db.get_transactions(
                user_id= user_id,
                columns= ['transaction_id', 'date', 'description', 'amount', 'type', 'bank', 'statement_type', 'filename'],
                period= period,
                banks= banks,
                statement_type= statement_type.value,
                amount_type= amount_type.value,
                show_categories_names= True
            )
            
            return pd.DataFrame(transactions)
        
    def get_categories(self, mapped: bool = False) -> List[str] | Dict[str, int]:        
        with self.quick_read_conn() as conn:
            categories_db = CategoryDBService(conn)
            
            if mapped:
                return categories_db.get_categories_by_user_mapped(self.user_id) + {None: None}
            else:
                return categories_db.get_categories_by_user(self.user_id)
                
    @staticmethod
    def _extract_modified_transactions(original_transactions: pd.DataFrame, edited_transactions: pd.DataFrame) -> List[TransactionRecord]:
        if not original_transactions.equals(edited_transactions):
            df_og = original_transactions.copy()
            df_ed = edited_transactions.copy()
            
            df_og_tuples: pd.Series = df_og.apply(tuple, axis= 1)
            df_ed_tuples: pd.Series = df_ed.apply(tuple, axis= 1)
            
            mask = ~df_ed_tuples.isin(df_og_tuples)
            
            return df_ed[mask].to_dict(orient= 'records')
        else:
            return []
        
    @staticmethod
    def _classify_modified_transactions(original_ids: pd.Series, modified_transactions: List[TransactionRecord]) -> Dict[Literal['new', 'modified', 'deleted'], List[TransactionRecord]]:
        new_transactions = []
        modified_transactions_list = []
        deleted_transactions = []
        
        last_original_id = original_ids.max()
        
        for transaction in modified_transactions:
            if transaction['transaction_id'] > last_original_id:
                new_transactions.append(transaction)
            elif transaction['transaction_id'] in original_ids:
                modified_transactions_list.append(transaction)
            
                
        return {'new': new_transactions, 'modified': modified_transactions_list, 'deleted': deleted_transactions}
        
    def modify_transactions(self, original_transactions: pd.DataFrame, edited_transactions: pd.DataFrame) -> None:
        modified_transactions = self._extract_modified_transactions(original_transactions, edited_transactions)
        
        if not modified_transactions:
            return
        
        # Chanche the categorie (str) to category_id (int)
        categories = self.get_categories(mapped= True)
        for transaction in modified_transactions:
            transaction['category_id'] = categories[transaction['category']]
            transaction['user_id'] = self.user_id
            del transaction['category']
            
        classified_transactions = self._classify_modified_transactions(original_transactions['transaction_id'], modified_transactions)
        
        with self.batch_conn() as conn:
            transactions_db = TransactionsDBService(conn)
            
            if classified_transactions['new']:
                transactions_db.add_records(classified_transactions['new'])
                
            if classified_transactions['modified']:
                transactions_db.update_transactions(classified_transactions['modified'])
                
            if classified_transactions['deleted']:
                transactions_db.delete_records(classified_transactions['deleted'])
                
                