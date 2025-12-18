from enum import Enum


class PeriodsOptions(str, Enum):
    CURRENT_MONTH = "Current Month"
    LAST_MONTH = "Last Month"
    AVARAGE = "Avarage"
    SPECIFIC_PERIOD = "Specific Period"
    ALL_TIME = "All Time"

    @classmethod
    def get_values(cls) -> list[str]:
        return [option.value for option in cls]
