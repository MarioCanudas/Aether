from typing import Any
from models.users import UserInfo, NewUser
from .base_db import BaseDBService

class UserDBService(BaseDBService):
    # Table information
    table_name = 'users'
    allowed_columns = {'user_id', 'username', 'password_hash', 'created_at', 'last_login', 'updated_at'}
    
    # Column names
    id_col = 'user_id'
    username = 'username'
    password_hash = 'password_hash'
    created_at = 'created_at'
    last_login = 'last_login'
    updated_at = 'updated_at'
    
    def get_user(self, **conditions: Any) -> UserInfo | None:
        query = f"SELECT * FROM {self.table_name}"
        
        if conditions:
            params = self._validate_conditions(conditions)
            
            query += " WHERE "
            query += " AND ".join([f"{col} = %({col})s" for col in params.keys()])
            
        result = self.execute_query(query, params= params, fetch='one', dict_cursor=True)
        
        return UserInfo.from_dict(result) if result else None
    
    def add_user(self, user: NewUser) -> None:
        with self.transaction():
            query = f"""
                INSERT INTO {self.table_name} ({self.username}, {self.password_hash}) 
                VALUES (%(username)s, %(password_hash)s)
            """
            print(user.model_dump())

            self.execute_query(query, params= user.model_dump())
        