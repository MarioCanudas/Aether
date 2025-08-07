from abc import ABC
from streamlit import session_state
from typing import Any, Generator, List, Dict
from contextlib import contextmanager
from services import ConnectionManagementService, DatabaseService, UserSessionService

class BaseController(ABC):
    """
    Base controller that provides centralized access to DatabaseService and UserSessionService
    with different scopes depending on the type of operation.
    
    Provides general methods for user session management and database access, commonly used in 
    all the child controllers.
    """
    
    def __init__(self):
        self.connection_manager = ConnectionManagementService()
        self.user_session_service = UserSessionService()
    
    @contextmanager
    def session_scope(self) -> Generator[DatabaseService, None, None]:
        """
        Context manager for user-interactive operations.
        Use this scope for operations that require a persistent connection
        during a user's session, such as interactive data entry or editing.
        """
        with self.connection_manager.get_session_scoped_service() as db_service:
            yield db_service
    
    @contextmanager 
    def batch_scope(self) -> Generator[DatabaseService, None, None]:
        """
        Context manager for batch processing operations.
        Use this scope for high-volume or intensive tasks such as
        processing PDF files or performing bulk database operations.
        """
        with self.connection_manager.get_batch_processing_service() as db_service:
            yield db_service
    
    @contextmanager
    def quick_read_scope(self) -> Generator[DatabaseService, None, None]:
        """
        Context manager for fast, read-only operations.
        Use this scope for quick lookups, validations, or dashboard refreshes
        where minimal overhead and read-only safety are desired.
        """
        with self.connection_manager.get_quick_read_service() as db_service:
            yield db_service

    def get_user_id(self, username: str) -> int | None:
        return self.user_session_service.get_user_id_by_username(username)
    
    def get_users(self) -> List[str]:
        return sorted(self.user_session_service.get_available_df_users())
    
    @property
    def user_id(self) -> int | None:
        return self.user_session_service.get_current_user_id()
            