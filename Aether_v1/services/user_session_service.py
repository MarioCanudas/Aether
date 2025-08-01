import logging
import pandas as pd
import threading 
from typing import Dict, Any, Optional
from .connection_management_service import ConnectionManagementService

logger = logging.getLogger(__name__)

class UserSessionService:
    """
    Service for managing user sessions.
    """
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """Singleton pattern for application-wide session management."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if getattr(self, '_initialized', False):
            return
            
        self._local = threading.local()  # Thread-local storage for Streamlit sessions
        self.connection_manager = ConnectionManagementService()
        self._initialized = True
        self.current_user_id = None
        logger.info("UserSessionService initialized")
        
    def get_available_df_users(self) -> list:
        """
        Get all available users from the database as a DataFrame.
        
        Returns:
            DataFrame with id, username, and created_at.
        """
        try:
            with self.connection_manager.get_quick_read_service() as db:
                users = db.get_records(
                    table_name='users',
                    columns=['username'],
                    value_format='dict'
                )
                return [user['username'] for user in users]
        except Exception as e:
            logger.error(f"Error fetching available users: {e}")
            return pd.DataFrame()
        
    def set_current_user_by_id(self, user_id: Optional[int]) -> bool:
        """
        Set the current user by their ID.
        
        Args:
            user_id: User ID to set as current, or None to clear.
            
        Returns:
            True if user was set successfully, False otherwise.
        """
        try:
            with self.connection_manager.get_quick_read_service() as db:
                users = db.get_records(
                    table_name='users',
                    where_conditions={'id': int(user_id)},
                    value_format='dict'
                )
                
                if users:
                    user_data = users[0]
                    self.current_user_id = user_data['id']
                    self._local.current_user = user_data
                    logger.info(f"Current user set: {user_data['username']} (ID: {user_id})")
                    return True
                else:
                    logger.warning(f"User with ID {user_id} not found")
                    return False
                    
        except Exception as e:
            logger.error(f"Error setting current user {user_id}: {e}")
            return False
        
    def clear_current_user(self) -> None:
        """
        Clear the current user.
        """
        self.current_user_id = None
        self._local.current_user = None
        
    def get_user_id_by_username(self, username: str) -> Optional[int]:
        """
        Get the user ID by username.
        """
        with self.connection_manager.get_quick_read_service() as db:
            users = db.get_records(
                table_name='users',
                where_conditions={'username': username},
                value_format='dict'
            )
            return users[0]['id'] if users else None
        
    def get_current_user(self) -> Optional[Dict[str, Any]]:
        """
        Get the current user for this session.
        
        Returns:
            Dict with user info or None if no user is set.
        """
        return getattr(self._local, 'current_user', None)
    
    def get_current_user_id(self) -> Optional[int]:
        """
        Get the current user ID.
        
        Returns:
            User ID or None if no user is set.
        """
        user = self.get_current_user()
        return user['id'] if user else None
    
    def get_current_username(self) -> Optional[str]:
        """
        Get the current username.
        
        Returns:
            Username or None if no user is set.
        """
        user = self.get_current_user()
        return user['username'] if user else None
    
    def add_user(self, username: str) -> None:
        try:
            with self.connection_manager.get_session_scoped_service() as db:
                db.insert_record(
                    table_name='users',
                    record={'username': username}
                )
        except Exception as e:
            logger.error(f"Error adding user {username}: {e}")
            raise e