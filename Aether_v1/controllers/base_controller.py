from abc import ABC
import pandas as pd
from psycopg2.extensions import connection
from typing import Generator, List
from contextlib import contextmanager
from services import (
    ConnectionManagementService, 
    UserSessionService,
    TransactionsDBService
)
from models.transactions import Transaction, DuplicateTransactionType

class BaseController(ABC):
    """
    Base controller that provides centralized access to DatabaseService and UserSessionService
    Base controller that provides centralized access to DatabaseService and UserSessionService
    with different scopes depending on the type of operation.
    
    Provides general methods for user session management and database access, commonly used in 
    all the child controllers.
    
    Provides general methods for user session management and database access, commonly used in 
    all the child controllers.
    """
    
    def __init__(self):
        self.connection_manager = ConnectionManagementService()
        self.user_session_service = UserSessionService()
    
    @contextmanager
    def session_conn(self) -> Generator[connection, None, None]:
        """
        Context manager for user-interactive operations.
        Use this scope for operations that require a persistent connection
        during a user's session, such as interactive data entry or editing.
        """
        with self.connection_manager.get_session_connection() as conn:
            yield conn
    
    @contextmanager 
    def batch_conn(self) -> Generator[connection, None, None]:
        """
        Context manager for batch processing operations.
        Use this scope for high-volume or intensive tasks such as
        processing PDF files or performing bulk database operations.
        """
        with self.connection_manager.get_batch_connection() as conn:
            yield conn

    @contextmanager
    def quick_read_conn(self) -> Generator[connection, None, None]:
        """
        Context manager for fast, read-only operations.
        Use this scope for quick lookups, validations, or dashboard refreshes
        where minimal overhead and read-only safety are desired.
        """
        with self.connection_manager.get_quick_read_connection() as conn:
            yield conn
            
    @property
    def user_id(self) -> int:
        return self.user_session_service.current_user_id
            
    def user_have_transactions(self) -> bool:
        with self.quick_read_conn() as conn:
            transactions_db = TransactionsDBService(conn)
            
            return transactions_db.exists(user_id= self.user_id)
        
    def user_have_potential_duplicates(self) -> bool:
        with self.quick_read_conn() as conn:
            transactions_db = TransactionsDBService(conn)
            
            return transactions_db.exists(user_id= self.user_id, duplicate_potential_state= False)
    @staticmethod
    def transactions_to_df(transactions: List[Transaction]) -> pd.DataFrame:
        return pd.DataFrame([transaction.model_dump() for transaction in transactions])