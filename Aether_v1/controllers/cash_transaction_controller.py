from typing import List, Optional
from datetime import date
from services import CategoryDBService, TransactionsDBService
from models.financial import TransactionRecord
from .base_controller import BaseController

class CashTransactionController(BaseController):
    def get_categories(self) -> List[str]:
        with self.quick_read_conn() as conn:
            category_db = CategoryDBService(conn)
            
            return category_db.get_categories_by_user(self.user_id)
        
    def get_category_id(self, category: str) -> Optional[int]:
        with self.quick_read_conn() as conn:
            category_db = CategoryDBService(conn)
            
            return category_db.find_id(name= category)
        
    def add_transaction(self, transaction: TransactionRecord) -> None:
        with self.session_conn() as conn:
            transactions_db = TransactionsDBService(conn)
            
            transactions_db.add_records([transaction.model_dump()])
    