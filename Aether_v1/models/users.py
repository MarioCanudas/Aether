from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, Any 

class NewUser(BaseModel):
    username: str
    password_hash: Optional[str] = None # Optional because it's not required when adding a user for now
    
class UserUpdate(BaseModel):
    user_id: int
    username: Optional[str] = None
    password_hash: Optional[str] = None
    updated_at: datetime


class UserProfile(BaseModel):
    user_id: int
    username: str
    password_hash: Optional[str] = None
    created_at: datetime
    last_login: datetime
    updated_at: Optional[datetime] = None
    
    @classmethod
    def from_dict(cls, dict_data: Dict[str, Any]) -> 'UserProfile':
        return cls(**dict_data)
    
    @property
    def created_at_formatted(self) -> str:
        return self.created_at.strftime('%Y-%m-%d %H:%M')
    
    @property
    def last_login_formatted(self) -> str:
        return self.last_login.strftime('%Y-%m-%d %H:%M')
    
    @property
    def updated_at_formatted(self) -> str:
        if self.updated_at is None:
            return 'Not updated yet'
        else:
            return self.updated_at.strftime('%Y-%m-%d %H:%M')
    
