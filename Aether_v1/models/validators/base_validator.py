import asyncio
from typing import Any


class BaseValidator:
    @staticmethod
    async def validate_type(
        value: Any, expected_type: Any, index: int | None = None
    ) -> TypeError | None:
        if not isinstance(value, expected_type):
            if index is not None:
                return TypeError(
                    f"Expected type {expected_type.__name__}, got {type(value).__name__}"
                )
            else:
                return TypeError(
                    f"Expected type {expected_type.__name__} in index {index}, got {type(value).__name__}"
                )

    async def validate_list_of(self, data: Any, item_type: Any) -> list[Any]:
        if not isinstance(data, list):
            raise TypeError(f"Expected a list, got {type(data).__name__}")

        errors_tasks: list[asyncio.Task] = []

        for i, item in enumerate(data):
            errors_tasks.append(asyncio.create_task(self.validate_type(item, item_type, i)))

        errors_results: list[TypeError | None] = await asyncio.gather(*errors_tasks)
        errors = [e for e in errors_results if e is not None]

        if errors:
            raise ExceptionGroup(f"It was obtained {len(errors)} TypeErros: ", errors)
        else:
            return data
