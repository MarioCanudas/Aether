import asyncio
from typing import cast

from models.bank_properties import BankName
from models.cards import Card
from models.templates import Template, TemplateType
from models.transactions import DuplicateResult, Transaction
from services import (
    CardsDBService,
    CategoryDBService,
    DuplicateTreatmentService,
    TemplatesDBService,
    TransactionsDBService,
)

from .base_controller import BaseController


class AddTransactionController(BaseController):
    TEMPLATE_TYPE = TemplateType.TRANSACTION

    def get_cards(self, bank: BankName | None = None) -> list[str]:
        with self.quick_read_conn() as conn:
            cards_db = CardsDBService(conn)

            cards = cards_db.get_cards(self.user_id)

            if bank:
                return [card.card_name for card in cards if card.card_bank == bank]
            else:
                return [card.card_name for card in cards]

    def get_card_by_id(self, card_id: int) -> Card | None:
        with self.quick_read_conn() as conn:
            cards_db = CardsDBService(conn)

            return cards_db.get_card_by_id(self.user_id, card_id)

    def get_card_by_name(self, card_name: str) -> Card | None:
        with self.quick_read_conn() as conn:
            cards_db = CardsDBService(conn)

            card_id = cards_db.find_id(user_id=self.user_id, card_name=card_name)

            if card_id is not None:
                return cards_db.get_card_by_id(self.user_id, card_id)
            else:
                return None

    def get_categories(self) -> list[str]:
        with self.quick_read_conn() as conn:
            category_db = CategoryDBService(conn)

            return category_db.get_categories_by_user(self.user_id)

    def get_category_id(self, category: str) -> int | None:
        with self.quick_read_conn() as conn:
            category_db = CategoryDBService(conn)

            return category_db.find_id(name=category)

    def get_category_name(self, category_id: int) -> str | None:
        with self.quick_read_conn() as conn:
            category_db = CategoryDBService(conn)

            result = category_db.find_by_id(category_id, columns=["name"])

            return result["name"] if result else None

    def get_duplicate_result(self, transaction: Transaction) -> DuplicateResult:
        dt_service = DuplicateTreatmentService()

        with self.quick_read_conn() as conn:
            duplicate_result = asyncio.run(
                dt_service.detect_duplicates(conn, self.user_id, transaction)
            )

            return cast(DuplicateResult, duplicate_result)

    def modify_potential_duplicate_transactions(self, transactions: list[Transaction]) -> None:
        transactions_to_modify = []

        for t in transactions:
            if not t.duplicate_potential_state:
                t.duplicate_potential_state = True
                transactions_to_modify.append(t)

        with self.batch_conn() as conn:
            transactions_db = TransactionsDBService(conn)

            transactions_db.update_transactions(transactions_to_modify)

    def add_transaction(self, transaction: Transaction) -> None:
        with self.session_conn() as conn:
            transactions_db = TransactionsDBService(conn)

            transactions_db.add_records([transaction])

    def add_template(self, template: Template) -> None:
        with self.session_conn() as conn:
            transactions_templates_db = TemplatesDBService(conn)

            transactions_templates_db.add_template(template)

    def get_templates_names(self) -> dict[str, int]:
        with self.quick_read_conn() as conn:
            transactions_templates_db = TemplatesDBService(conn)

            return transactions_templates_db.get_templates_names(self.user_id, self.TEMPLATE_TYPE)

    def get_template(self, template_id: int) -> Template | None:
        with self.quick_read_conn() as conn:
            transactions_templates_db = TemplatesDBService(conn)

            return transactions_templates_db.get_template(template_id)

    def update_template(self, template_id: int, updated_template: Template) -> None:
        with self.session_conn() as conn:
            transactions_templates_db = TemplatesDBService(conn)

            transactions_templates_db.update_template(template_id, updated_template)

    def delete_template(self, template_id: int) -> None:
        with self.session_conn() as conn:
            transactions_templates_db = TemplatesDBService(conn)

            transactions_templates_db.delete_template(template_id)
