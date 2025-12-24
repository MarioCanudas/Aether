import logging
from typing import Any

import pandas as pd
from models.amounts import TransactionType
from models.bank_properties import BankName, StatementType
from models.dates import Period
from models.transactions import Transaction
from models.validators import TransactionValidator
from services import CardsDBService, CategoryDBService, TransactionsDBService

from .base_controller import BaseController

logger = logging.getLogger(__name__)


class DataViewController(BaseController):
    def __init__(self):
        super().__init__()
        self.transaction_validator = TransactionValidator()

    def _to_transactions(self, transactions_dicts: list[dict[str, Any]]) -> list[Transaction]:
        categories = self.get_categories(mapped=True)
        cards = self.get_cards(mapped=True)

        transactions: list[Transaction] = []

        for t in transactions_dicts:
            if "user_id" not in t:
                t["user_id"] = self.user_id

            if "category_id" not in t:
                t["category_id"] = categories[t["category"]] if t["category"] else None

                del t["category"]

            if "card_id" not in t:
                t["card_id"] = cards[t["card_name"]] if t["card_name"] else None

                del t["card_name"]

            if "transaction_id" in t and (
                pd.isna(t["transaction_id"]) or t["transaction_id"] is None
            ):
                del t["transaction_id"]

            transactions.append(Transaction(**t))

        return transactions

    def get_transactions_date_range(self) -> Period:
        user_id = self.user_id

        with self.quick_read_conn() as conn:
            transactions_db = TransactionsDBService(conn)

            period = transactions_db.get_transactions_period(user_id)

            return period

    def get_banks_in_transactions(self) -> list[str]:
        user_id = self.user_id

        with self.quick_read_conn() as conn:
            transactions_db = TransactionsDBService(conn)

            return transactions_db.get_unique_values(column="bank", user_id=user_id)

    def get_cards(self, mapped: bool = False) -> list[str] | dict[str, int]:
        user_id = self.user_id

        with self.quick_read_conn() as conn:
            cards_db = CardsDBService(conn)

            cards = cards_db.get_cards(user_id)

            if mapped:
                return {card.card_name: card.card_id for card in cards if card.card_id is not None}
            else:
                return [card.card_name for card in cards]

    def get_filtered_transactions(
        self,
        period: Period,
        banks: list[BankName] | None,
        statement_type: StatementType | None,
        amount_types: list[TransactionType] | None,
    ) -> pd.DataFrame:
        user_id = self.user_id

        with self.quick_read_conn() as conn:
            transactions_db = TransactionsDBService(conn)

            transactions = transactions_db.get_transactions(
                user_id=user_id,
                columns=[
                    "transaction_id",
                    "date",
                    "description",
                    "amount",
                    "type",
                    "bank",
                    "statement_type",
                    "filename",
                ],
                period=period,
                banks=banks,
                statement_type=statement_type,
                amount_types=amount_types,
                show_categories_names=True,
                show_cards_names=True,
                transaction_model=False,
            )

            return pd.DataFrame(transactions).sort_values(by="date", ascending=False)

    def get_categories(self, mapped: bool = False) -> list[str] | dict[str, int]:
        with self.quick_read_conn() as conn:
            categories_db = CategoryDBService(conn)

            if mapped:
                return categories_db.get_categories_by_user_mapped(self.user_id)
            else:
                return categories_db.get_categories_by_user(self.user_id)

    def _extract_modified_transactions(
        self, original_transactions: pd.DataFrame, edited_transactions: pd.DataFrame
    ) -> dict[str, list[Transaction]]:
        """
        Extract modified, new, and deleted transactions.
        Returns a dictionary with 'new', 'modified', and 'deleted' keys.
        """
        df_og = original_transactions.copy()
        df_ed = edited_transactions.copy()

        # Get transaction IDs for comparison
        original_ids = set(df_og["transaction_id"].tolist())
        edited_ids = set(df_ed["transaction_id"].tolist())

        # Find deleted transactions (in original but not in edited)
        deleted_ids = original_ids - edited_ids
        df_to_delete = df_og[df_og["transaction_id"].isin(list(deleted_ids))]
        df_to_delete = self.generics_validator.validate_dataframe(df_to_delete)

        deleted_transactions = df_to_delete.to_dict(orient="records")

        # Find new transactions (in edited but not in original)
        new_ids = edited_ids - original_ids
        df_new = df_ed[df_ed["transaction_id"].isin(list(new_ids))]
        df_new = self.generics_validator.validate_dataframe(df_new)

        new_transactions = df_new.to_dict(orient="records")

        # Find modified transactions (in both but with different content)
        common_ids = original_ids & edited_ids
        modified_transactions = []

        for transaction_id in common_ids:
            original_row = df_og[df_og["transaction_id"] == transaction_id].iloc[0]
            original_row = self.generics_validator.validate_series(original_row)

            edited_row = df_ed[df_ed["transaction_id"] == transaction_id].iloc[0]
            edited_row = self.generics_validator.validate_series(edited_row)

            # Compare all columns except transaction_id
            comparison_cols = [col for col in original_row.index if col != "transaction_id"]

            og_to_compare = self.generics_validator.validate_series(original_row[comparison_cols])
            ed_to_compare = self.generics_validator.validate_series(edited_row[comparison_cols])

            if not og_to_compare.equals(ed_to_compare):
                modified_transactions.append(edited_row.to_dict())

        return {
            "new": self._to_transactions(new_transactions),
            "modified": self._to_transactions(modified_transactions),
            "deleted": self._to_transactions(deleted_transactions),
        }

    def modify_transactions(
        self, original_transactions: pd.DataFrame, edited_transactions: pd.DataFrame
    ) -> None:
        modified_transactions = self._extract_modified_transactions(
            original_transactions, edited_transactions
        )

        if not modified_transactions:
            return

        with self.batch_conn() as conn:
            transactions_db = TransactionsDBService(conn)

            if modified_transactions["new"]:
                transactions_db.add_records(modified_transactions["new"])

            if modified_transactions["modified"]:
                transactions_db.update_transactions(modified_transactions["modified"])

            if modified_transactions["deleted"]:
                transactions_db.delete_transactions(modified_transactions["deleted"])

    def get_potential_duplicate_transactions(self) -> list[Transaction]:
        with self.quick_read_conn() as conn:
            transactions_db = TransactionsDBService(conn)

            transactions = transactions_db.get_transactions(
                user_id=self.user_id, duplicate_potential_state=True
            )
            transactions = self.transaction_validator.validate_list_transactions(transactions)

            return transactions

    def add_select_widget(self, df: pd.DataFrame) -> pd.DataFrame:
        columns: list[str] = df.columns.tolist()

        df["To edit"] = False
        df = self.generics_validator.validate_dataframe(df[["To edit", *columns]])

        return df

    def ignore_duplicate_transaction(self, t: Transaction) -> None:
        with self.session_conn() as conn:
            transactions_db = TransactionsDBService(conn)

            t.duplicate_potential_state = False

            transactions_db.update_transactions([t])

    def delete_transaction(self, t: Transaction) -> None:
        with self.session_conn() as conn:
            transactions_db = TransactionsDBService(conn)

            transactions_db.delete_transactions([t])
