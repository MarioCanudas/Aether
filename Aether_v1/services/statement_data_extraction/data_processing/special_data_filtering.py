import re

from models.tables import TransactionsTable
from models.validators import GenericsValidator

from ..core import SpecialDataFiltering


class NuSpecialDataFiltering(SpecialDataFiltering):
    @property
    def generics_validator(self) -> GenericsValidator:
        return GenericsValidator()

    def filter_special_data(self, normalized_table: TransactionsTable) -> TransactionsTable:
        key_words = ["retiro de cajita", "depósito en cajita"]

        pattern = "|".join(map(re.escape, key_words))

        mask = ~normalized_table.descriptions.str.lower().str.contains(
            pattern, case=False, regex=True
        )

        result = self.generics_validator.validate_dataframe(normalized_table.df[mask])

        return TransactionsTable(df=result)
