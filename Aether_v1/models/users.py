from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, Any 

class NewUser(BaseModel):
    username: str
    password_hash: Optional[str] = None # Optional because it's not required when adding a user for now
    

class UserInfo(BaseModel):
    user_id: int
    username: str
    password_hash: Optional[str] = None
    created_at: datetime
    last_login: datetime
    updated_at: Optional[datetime] = None
    
    @classmethod
    def from_dict(cls, dict_data: Dict[str, Any]) -> 'UserInfo':
        return cls(**dict_data)
    
