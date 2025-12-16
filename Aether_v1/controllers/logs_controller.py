from typing import List
from functools import cached_property
from passlib.context import CryptContext
from datetime import datetime
from services import UserDBService
from models.users import NewUser
from .base_controller import BaseController

class LogsController(BaseController):
    @cached_property
    def password_context(self) -> CryptContext:
        return CryptContext(schemes= ['argon2'], deprecated= 'auto')
    
    def hash_password(self, password: str) -> str:
        return self.password_context.hash(password)
    
    def _verify_password(self, password: str, hashed_password: str) -> bool:
        return self.password_context.verify(password, hashed_password)
    
    def verify_login(self, username: str, password: str) -> bool:
        with self.quick_read_conn() as conn:
            users_db = UserDBService(conn)
            
            user = users_db.get_user(username= username)
            
            if user is None:
                return False
            
            if user.password_hash is None:
                raise ValueError('Password hash is not set for user')
            
            return self._verify_password(password, user.password_hash)
        
    def update_last_login(self, user_id: int) -> None:
        with self.session_conn() as conn:
            users_db = UserDBService(conn)
            
            users_db.update_user(user_id, last_login= datetime.now())
    
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
        
    def add_user(self, new_user: NewUser) -> None:
        with self.session_conn() as conn:
            users_db = UserDBService(conn)
            
            users_db.add_user(new_user)
            