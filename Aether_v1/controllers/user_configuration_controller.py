import pandas as pd
from datetime import datetime
from typing import Optional
from services import UserDBService
from models.users import UserUpdate
from .base_controller import BaseController

class UserConfigurationController(BaseController):
    def get_users_table(self) -> pd.DataFrame:
        with self.quick_read_conn() as conn:
            users_db = UserDBService(conn)
            
            users = users_db.get_users(columns= ['id', 'username', 'created_at', 'last_login', 'updated_at'])
            
            return pd.DataFrame(users)
            
    def modify_user(self, current_username: str, new_username: str, new_password: Optional[str] = None) -> None:
        if current_username == new_username:
            raise ValueError('New username cannot be the same as the current username')
        
        with self.session_conn() as conn:
            users_db = UserDBService(conn)
            
            user_id = users_db.find_id(username= current_username)
            
            users_db.update_user(
                UserUpdate(
                    user_id= user_id, 
                    username= new_username, 
                    password_hash= new_password,
                    updated_at= datetime.now()
                )
            )
            
    def add_user(self, username: str) -> None:
        self.user_session_service.add_user(username)
        
    def delete_user(self, user_id: int) -> None:
        with self.session_conn() as conn:
            users_db = UserDBService(conn)
            
            users_db.delete_user(user_id)