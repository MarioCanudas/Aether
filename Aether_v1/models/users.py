from datetime import datetime
from typing import Any

from pydantic import BaseModel


class NewUser(BaseModel):
    username: str
    password_hash: str | None = (
        None  # Optional because it's not required when adding a user for now
    )


class UserProfile(BaseModel):
    user_id: int
    username: str
    password_hash: str | None = None
    created_at: datetime
    last_login: datetime
    updated_at: datetime | None = None

    @classmethod
    def from_dict(cls, dict_data: dict[str, Any]) -> "UserProfile":
        return cls(**dict_data)

    @property
    def created_at_formatted(self) -> str:
        return self.created_at.strftime("%Y-%m-%d %H:%M")

    @property
    def last_login_formatted(self) -> str:
        return self.last_login.strftime("%Y-%m-%d %H:%M")

    @property
    def updated_at_formatted(self) -> str:
        if self.updated_at is None:
            return "Not updated yet"
        else:
            return self.updated_at.strftime("%Y-%m-%d %H:%M")
