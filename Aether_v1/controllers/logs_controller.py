from typing import List
from services import UserDBService
from .base_controller import BaseController

class LogsController(BaseController):
    def update_user_id(self, user_id: int) -> None:
        self.user_session_service.set_current_user_by_id(user_id)
    
    def clear_user_session(self) -> None:
        self.user_session_service.clear_current_user()
        
    def get_users(self) -> List[str]:
        with self.quick_read_conn() as conn:
            users_db = UserDBService(conn)
            
            return users_db.get_unique_values('username')
        
    def get_user_id(self, username: str) -> int:
        with self.quick_read_conn() as conn:
            users_db = UserDBService(conn)
            
            return users_db.find_id(username= username)
        