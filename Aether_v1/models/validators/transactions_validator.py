import asyncio
from typing import Any

from ..transactions import DuplicateResult, Transaction
from .base_validator import BaseValidator


class TransactionValidator(BaseValidator):
    def validate_list_transactions(self, data: Any) -> list[Transaction]:
        return asyncio.run(self.validate_list_of(data, Transaction))

    async def validate_list_transactions_async(self, data: Any) -> list[Transaction]:
        return await self.validate_list_of(data, Transaction)

    def validate_list_duplicate_result(self, data: Any) -> list[DuplicateResult]:
        return asyncio.run(self.validate_list_of(data, DuplicateResult))
