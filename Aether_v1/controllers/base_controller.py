from abc import ABC
from services import ConnectionManagementService
from typing import Generator
from contextlib import contextmanager

class BaseController(ABC):
    """
    Base controller that provides centralized access to DatabaseService
    with different scopes depending on the type of operation.
    """
    
    def __init__(self):
        self.connection_manager = ConnectionManagementService()
    
    @contextmanager
    def session_scope(self):
        """
        Context manager for user-interactive operations.
        Use this scope for operations that require a persistent connection
        during a user's session, such as interactive data entry or editing.
        """
        with self.connection_manager.get_session_scoped_service() as db_service:
            yield db_service
    
    @contextmanager 
    def batch_scope(self):
        """
        Context manager for batch processing operations.
        Use this scope for high-volume or intensive tasks such as
        processing PDF files or performing bulk database operations.
        """
        with self.connection_manager.get_batch_processing_service() as db_service:
            yield db_service
    
    @contextmanager
    def quick_read_scope(self):
        """
        Context manager for fast, read-only operations.
        Use this scope for quick lookups, validations, or dashboard refreshes
        where minimal overhead and read-only safety are desired.
        """
        with self.connection_manager.get_quick_read_service() as db_service:
            yield db_service

