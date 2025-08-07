import pandas as pd
from typing import Optional
from .base_controller import BaseController

class UserConfigurationController(BaseController):
    def get_users_table(self) -> pd.DataFrame:
        with self.quick_read_scope() as db:
            return db.get_records(
                'users', 
                columns= ['id', 'username', 'created_at', 'last_login', 'updated_at'],
                value_format= 'dataframe'
            )
            
    def modify_user(self, current_username: str, new_username: str, new_password: Optional[str] = None) -> None:
        user_id = self.get_user_id(current_username)
        
        if new_username not in self.get_users():
            with self.batch_scope() as db:
                if new_password is not None:
                    db.update_record('users', {'username': new_username, 'password': new_password}, {'id': user_id})
                else:
                    db.update_record('users', {'username': new_username}, {'id': user_id})
        else:
            raise ValueError(f'User {new_username} already exists')
            
    def add_user(self, username: str) -> None:
        self.user_session_service.add_user(username)
        
    def delete_user(self, user_id: int) -> None:
        with self.batch_scope() as db:
            db.delete_record('users', {'id': user_id})