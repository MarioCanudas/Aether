from typing import Any


class BaseValidator:
    @staticmethod
    def validate_type(
        value: Any, expected_type: Any, index: int | None = None
    ) -> TypeError | None:
        if not isinstance(value, expected_type):
            if index is not None:
                return TypeError(
                    f"Expected type {expected_type.__name__} in index {index}, got {type(value).__name__}"
                )
            else:
                return TypeError(
                    f"Expected type {expected_type.__name__}, got {type(value).__name__}"
                )
        return None

    def validate_list_of(self, data: Any, item_type: Any) -> list[Any]:
        if not isinstance(data, list):
            raise TypeError(f"Expected a list, got {type(data).__name__}")

        errors: list[TypeError] = []

        for i, item in enumerate(data):
            err = self.validate_type(item, item_type, i)
            if err is not None:
                errors.append(err)

        if errors:
            raise ExceptionGroup(f"It was obtained {len(errors)} TypeErros: ", errors)
        else:
            return data
