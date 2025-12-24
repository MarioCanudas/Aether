from collections.abc import Generator
from contextlib import contextmanager
from typing import Any

import pandas as pd
from models.transactions import Transaction
from models.validators import GenericsValidator
from psycopg2.extensions import connection
from services import (
    CardsDBService,
    CategoryDBService,
    ConnectionManagementService,
    TransactionsDBService,
    UserSessionService,
)
from streamlit import session_state


class BaseController:
    """
    Base controller that provides centralized access to DatabaseService and UserSessionService
    with different scopes depending on the type of operation.

    Provides general methods for user session management and database access, commonly used in
    all the child controllers.
    """

    def __init__(self):
        self.connection_manager = ConnectionManagementService()
        self.user_session_service = UserSessionService()
        self.generics_validator = GenericsValidator()

    @property
    def formated_columns(self) -> dict[str, str]:
        return {
            "date": "Date",
            "description": "Description",
            "amount": "Amount",
            "type": "Type",
            "bank": "Bank",
            "statement_type": "Statement Type",
            "category": "Category",
            "card": "Card",
        }

    @contextmanager
    def session_conn(self) -> Generator[connection, None, None]:
        """
        Context manager for user-interactive operations.
        Use this scope for operations that require a persistent connection
        during a user's session, such as interactive data entry or editing.
        """
        with self.connection_manager.get_session_connection() as conn:
            yield conn

    @contextmanager
    def batch_conn(self) -> Generator[connection, None, None]:
        """
        Context manager for batch processing operations.
        Use this scope for high-volume or intensive tasks such as
        processing PDF files or performing bulk database operations.
        """
        with self.connection_manager.get_batch_connection() as conn:
            yield conn

    @contextmanager
    def quick_read_conn(self) -> Generator[connection, None, None]:
        """
        Context manager for fast, read-only operations.
        Use this scope for quick lookups, validations, or dashboard refreshes
        where minimal overhead and read-only safety are desired.
        """
        with self.connection_manager.get_quick_read_connection() as conn:
            yield conn

    @property
    def user_id(self) -> int:
        if "user_id" not in session_state or not session_state.user_id:
            raise ValueError("User ID is not set in session state")

        return session_state.user_id

    def user_have_transactions(self) -> bool:
        with self.quick_read_conn() as conn:
            transactions_db = TransactionsDBService(conn)

            return transactions_db.exists(user_id=self.user_id)

    def user_have_potential_duplicates(self) -> bool:
        with self.quick_read_conn() as conn:
            transactions_db = TransactionsDBService(conn)

            return transactions_db.exists(user_id=self.user_id, duplicate_potential_state=True)

    def get_categories_names(self, maped: bool = False) -> list[str] | dict[str, int]:
        with self.quick_read_conn() as conn:
            category_db = CategoryDBService(conn)

            if maped:
                return category_db.get_categories_by_user_mapped(self.user_id)
            else:
                return category_db.get_categories_by_user(self.user_id)

    def get_category_name(self, category_id: int) -> str | None:
        if not category_id:
            raise ValueError("Category ID is required")

        with self.quick_read_conn() as conn:
            category_db = CategoryDBService(conn)

            return category_db.get_category_name(category_id)

    def get_card_name(self, card_id: int) -> str | None:
        if not card_id:
            raise ValueError("Card ID is required")

        with self.quick_read_conn() as conn:
            cards_db = CardsDBService(conn)

            return cards_db.get_card_name(card_id)

    def transactions_to_df(
        self, transactions: list[Transaction], to_view: bool = False
    ) -> pd.DataFrame:
        dicts_to_df: list[dict[str, Any]] = []

        for t in transactions:
            dict_to_df = t.model_dump()

            if to_view:
                dict_to_df["category"] = (
                    self.get_category_name(t.category_id) if t.category_id else None
                )
                dict_to_df["card"] = self.get_card_name(t.card_id) if t.card_id else None

                del dict_to_df["category_id"]
                del dict_to_df["card_id"]
                del dict_to_df["duplicate_potential_state"]
                del dict_to_df["user_id"]
                del dict_to_df["transaction_id"]
                del dict_to_df["filename"]

            dicts_to_df.append(dict_to_df)

        return (
            pd.DataFrame(dicts_to_df).rename(columns=self.formated_columns)
            if to_view
            else pd.DataFrame(dicts_to_df)
        )
