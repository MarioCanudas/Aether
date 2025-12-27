import asyncio
from io import BytesIO
from typing import Any

from pandas import DataFrame, Series

from .base_validator import BaseValidator


class GenericsValidator(BaseValidator):
    @staticmethod
    async def validate_dict(
        value: Any, index: int | None = None, str_key: bool = True
    ) -> TypeError | None:
        if not isinstance(value, dict):
            return (
                TypeError(f"Expected a dict, got {type(value).__name__}")
                if index is None
                else TypeError(f"Expected a dict at index {index}, got {type(value).__name__}")
            )

        if str_key and all(not isinstance(k, str) for k in value.keys()):
            return (
                TypeError("All keys in the dict must be of type str")
                if index is None
                else TypeError(f"All keys in the dict at index {index} must be of type str")
            )

        return None

    @staticmethod
    async def validate_list_of_dicts(data: Any) -> list[dict[str, Any]]:
        if not isinstance(data, list):
            raise TypeError(f"Expected a list, got {type(data).__name__}")

        errors_tasks: list[asyncio.Task[TypeError | None]] = []

        for i, item in enumerate(data):
            errors_tasks.append(asyncio.create_task(GenericsValidator.validate_dict(item, i)))

        errors_results: list[TypeError | None] = await asyncio.gather(*errors_tasks)
        errors = [e for e in errors_results if e is not None]

        if errors:
            raise ExceptionGroup(f"It was obtained {len(errors)} TypeErrors: ", errors)
        else:
            return data

    @staticmethod
    def validate_dataframe(data: Any) -> DataFrame:
        if not isinstance(data, DataFrame):
            raise TypeError(f"Expected a pandas DataFrame, got {type(data).__name__}")
        return data

    @staticmethod
    def validate_series(data: Any) -> Series:
        if not isinstance(data, Series):
            raise TypeError(f"Expected a pandas Series, got {type(data).__name__}")
        return data

    def validate_list_bytesio(self, data: Any) -> list[BytesIO]:
        return asyncio.run(self.validate_list_of(data, BytesIO))

    def validate_list_str(self, data: Any) -> list[str]:
        return asyncio.run(self.validate_list_of(data, str))

    def validate_list_int(self, data: Any) -> list[int]:
        return asyncio.run(self.validate_list_of(data, int))
