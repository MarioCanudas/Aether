import logging
from io import BytesIO
from typing import Any

import pandas as pd
from models.cards import Card
from models.transactions import DuplicateResult, FilteredTransactionsResult, Transaction
from models.validators import TransactionValidator
from services import (
    AutomaticCategorizationService,
    CardsDBService,
    DataProcessingService,
    DataValidationService,
    DuplicateTreatmentService,
    StatementDataExtractionService,
    TransactionsDBService,
)

from .base_controller import BaseController

logger = logging.getLogger(__name__)


class UploadStatementsController(BaseController):
    def __init__(self):
        super().__init__()
        self.data_processing_service = DataProcessingService()
        self.data_validation_service = DataValidationService()
        self.dt_service = DuplicateTreatmentService()
        self.ac_service = AutomaticCategorizationService()
        self.transaction_validator = TransactionValidator()

    def process_uploaded_files(
        self, uploaded_files: list[BytesIO], card: Card | None = None
    ) -> list[Transaction]:
        all_transactions = []

        for uploaded_file in uploaded_files:
            # Set the transaction extraction service per file
            statement_data_extraction_service = StatementDataExtractionService(
                self.user_id, uploaded_file
            )
            transactions_table = statement_data_extraction_service.get_transactions()
            metadata = statement_data_extraction_service.metadata_extractor.get_metadata()

            validated_transactions = self.data_validation_service.validate_transactions(
                transactions_table, metadata
            )

            all_transactions.append(validated_transactions.df)

        all_transactions_df = pd.concat(all_transactions, ignore_index=True)
        all_transactions_df["user_id"] = self.user_id
        all_transactions_df["category_id"] = None
        all_transactions_df["duplicate_potential_state"] = False
        all_transactions_df["transaction_id"] = None

        if card:
            all_transactions_df["card_id"] = card.card_id
        else:
            all_transactions_df["card_id"] = None

        return [Transaction(**r) for r in all_transactions_df.to_dict(orient="records")]

    async def filter_transactions(
        self, transactions: list[Transaction]
    ) -> FilteredTransactionsResult:
        clean_transactions, duplicated_transactions = (
            self.dt_service.eliminate_credit_and_debit_duplicates(transactions)
        )

        with self.quick_read_conn() as conn:
            duplicates_results = await self.dt_service.detect_duplicates(
                conn, self.user_id, clean_transactions
            )
            duplicates_results = self.transaction_validator.validate_list_duplicate_result(
                duplicates_results
            )

        filtered_transactions_result = FilteredTransactionsResult(
            duplicated=duplicated_transactions
        )

        for result in duplicates_results:
            if isinstance(
                result, list
            ):  # Handling potential distinct return type if any, though hint says list[DuplicateResult]
                continue
            if result.has_exact_duplicates:
                filtered_transactions_result.duplicated.append(result.transaction)
            elif result.has_potential_duplicates:
                filtered_transactions_result.potential_duplicates_to_upload.append(
                    result.transaction
                )
                filtered_transactions_result.potential_duplicates_to_modify.extend(
                    result.potential_duplicates
                )
            else:
                filtered_transactions_result.clean.append(result.transaction)

        return filtered_transactions_result

    def _auto_classiy_transactions(self, transactions: list[Transaction]) -> list[Transaction]:
        categories = self.get_categories_names()
        assert isinstance(categories, list), "Categories should be a list of strings"

        categorizaded_map = self.ac_service.categorize_transactions(transactions, categories)

        categories_map = self.get_categories_names(maped=True)
        assert isinstance(categories_map, dict), "Categories map should be a dict of str to int"

        for t in transactions:
            category = categorizaded_map.get(t)
            if category is not None:
                t.category_id = categories_map.get(category)

        return transactions

    def upload_transactions(
        self,
        filtered_transactions_result: FilteredTransactionsResult,
        autocacategorized: bool,
    ) -> None:
        with self.batch_conn() as conn:
            transactions_db = TransactionsDBService(conn)

            if len(filtered_transactions_result.potential_duplicates_to_modify) > 0:
                # Basedpyright error: attribute potential_duplicates_to_modify_unique is unknown.
                # Assuming intention was to unique-ify the list.
                unique_potential = list(
                    {
                        t.transaction_id: t
                        for t in filtered_transactions_result.potential_duplicates_to_modify
                    }.values()
                )
                transactions_db.update_transactions(unique_potential)

            transactions_to_upload = (
                self._auto_classiy_transactions(
                    filtered_transactions_result.potential_duplicates_to_upload
                    + filtered_transactions_result.clean
                )
                if autocacategorized
                else (
                    filtered_transactions_result.potential_duplicates_to_upload
                    + filtered_transactions_result.clean
                )
            )

            if len(transactions_to_upload) > 0:
                transactions_db.add_records(transactions_to_upload)

    def get_cards(self) -> list[str]:
        with self.quick_read_conn() as conn:
            cards_db = CardsDBService(conn)

            cards = cards_db.get_cards(self.user_id)

            return [card.card_name for card in cards]

    def get_card_by_name(self, card_name: str) -> Card:
        with self.quick_read_conn() as conn:
            cards_db = CardsDBService(conn)

            card_id = cards_db.find_id(card_name=card_name, user_id=self.user_id)
            if card_id is None:
                raise ValueError(f"Card {card_name} not found")

            card = cards_db.get_card_by_id(self.user_id, card_id)
            if card is None:
                raise ValueError(f"Card with id {card_id} not found")
            return card
