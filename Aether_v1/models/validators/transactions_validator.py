from typing import Any

from ..transactions import DuplicateResult, Transaction
from .base_validator import BaseValidator


class TransactionValidator(BaseValidator):
    def validate_list_transactions(self, data: Any) -> list[Transaction]:
        return self.validate_list_of(data, Transaction)

    def validate_list_transactions_async(self, data: Any) -> list[Transaction]:
        # Deprecated wrapper for backward compatibility, now fully synchronous.
        return self.validate_list_of(data, Transaction)

    def validate_list_duplicate_result(self, data: Any) -> list[DuplicateResult]:
        return self.validate_list_of(data, DuplicateResult)

    def validate_list_duplicate_result_async(self, data: Any) -> list[DuplicateResult]:
        # Deprecated wrapper for backward compatibility, now fully synchronous.
        return self.validate_list_of(data, DuplicateResult)
