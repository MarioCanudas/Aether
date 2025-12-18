from typing import Any

from models.users import NewUser, UserProfile

from .base_db import BaseDBService


class UserDBService(BaseDBService):
    # Table information
    table_name: str = "users"
    allowed_columns: set[str] = {
        "user_id",
        "username",
        "password_hash",
        "created_at",
        "last_login",
        "updated_at",
    }

    # Column names
    id_col: str = "user_id"
    username: str = "username"
    password_hash: str = "password_hash"
    created_at: str = "created_at"
    last_login: str = "last_login"
    updated_at: str = "updated_at"

    def get_user(self, **conditions: Any) -> UserProfile | None:
        query = f"SELECT * FROM {self.table_name}"

        if conditions:
            params = self._validate_conditions(conditions)

            query += " WHERE "
            query += " AND ".join([f"{col} = %({col})s" for col in params.keys()])
        else:
            params = {}

        result = self.execute_query(query, params=params, fetch="one", dict_cursor=True)

        if result and isinstance(result, dict):
            return UserProfile.from_dict(result)
        return None

    def get_users(self, columns: list[str] | None = None) -> list[dict[str, Any]]:
        if columns:
            query = f"SELECT {', '.join(columns)} FROM {self.table_name}"
        else:
            query = f"SELECT * FROM {self.table_name}"

        result = self.execute_query(query, fetch="all", dict_cursor=True)

        if result and isinstance(result, list):
            return [r for r in result if isinstance(r, dict)]
        return []

    def add_user(self, new_user: NewUser) -> None:
        with self.transaction():
            query = f"""
                INSERT INTO {self.table_name} ({self.username}, {self.password_hash}) 
                VALUES (%(username)s, %(password_hash)s)
            """

            self.execute_query(query, params=new_user.model_dump())

    def update_user(self, user_id: int, **updates: Any) -> None:
        params = self._validate_conditions(updates)
        params["user_id"] = user_id

        with self.transaction():
            query = f"""
                UPDATE {self.table_name}
                SET {", ".join([f"{col} = %({col})s" for col in updates])}
                WHERE {self.id_col} = %(user_id)s
            """

            self.execute_query(query, params=params)

    def delete_user(self, user_id: int) -> None:
        with self.transaction():
            query = f"""
                DELETE FROM {self.table_name}
                WHERE {self.id_col} = %(id)s
            """

            self.execute_query(query, params={"id": user_id})
