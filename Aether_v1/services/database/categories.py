from typing import Any

from models.categories import NewCategory

from .base_db import BaseDBService


class CategoryDBService(BaseDBService):
    # Table information
    table_name: str = "categories"
    allowed_columns: set[str] = {"category_id", "user_id", "group", "name", "description"}

    # Column names
    id_col: str = "category_id"
    user_id: str = "user_id"
    group: str = "group"
    name: str = "name"
    description: str = "description"

    def get_categories_by_user(self, user_id: int) -> list[str]:
        query = """
            SELECT name FROM categories WHERE user_id IS NULL OR user_id = %(user_id)s
        """

        result = self.execute_query(query, params={"user_id": user_id}, fetch="all")

        if result and isinstance(result, list):
            return [r[0] for r in result if isinstance(r, tuple)]
        return []

    def get_categories_by_user_mapped(self, user_id: int) -> dict[str, int]:
        categories = {}
        query = """
            SELECT name, category_id FROM categories WHERE user_id IS NULL OR user_id = %(user_id)s
        """

        result = self.execute_query(
            query, params={"user_id": user_id}, fetch="all", dict_cursor=True
        )

        if result and isinstance(result, list):
            for r in result:
                if isinstance(r, dict):
                    categories[r["name"]] = r["category_id"]

        return categories

    def _validate_new_category(self, user_id: int, new_category: NewCategory) -> bool:
        query = f"""
            SELECT COUNT(*) FROM {self.table_name} WHERE {self.user_id} = %(user_id)s AND {self.name} = %(name)s AND "group" = %(group)s
        """

        result = self.execute_query(
            query,
            params={
                "user_id": user_id,
                "name": new_category.name,
                "group": new_category.group.value,
            },
            fetch="one",
        )

        if result and isinstance(result, tuple) and result[0] > 0:
            return False
        else:
            return True

    def add_category(self, user_id: int, new_category: NewCategory) -> None:
        if not self._validate_new_category(user_id, new_category):
            raise ValueError("Category already exists")
        else:
            with self.transaction():
                query = f"""
                    INSERT INTO {self.table_name} ({self.user_id}, "group", {self.name}, {self.description})
                    VALUES (%(user_id)s, %(group)s, %(name)s, %(description)s)
                """

                params: dict[str, Any] = new_category.model_dump() | {"user_id": user_id}

                self.execute_query(query, params=params)

    def get_category_name(self, category_id: int) -> str | None:
        query = f"""
            SELECT {self.name} FROM {self.table_name} WHERE {self.id_col} = %(category_id)s
        """

        result = self.execute_query(query, params={"category_id": category_id}, fetch="one")

        return result[0] if result and isinstance(result, tuple) else None
