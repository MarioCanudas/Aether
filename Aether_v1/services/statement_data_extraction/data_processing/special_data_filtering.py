import re
from typing import cast

import pandas as pd
from models.tables import TransactionsTable

from ..core import SpecialDataFiltering


class NuSpecialDataFiltering(SpecialDataFiltering):
    @staticmethod
    def filter_special_data(normalized_table: TransactionsTable) -> TransactionsTable:
        key_words = ["retiro de cajita", "depósito en cajita"]

        pattern = "|".join(map(re.escape, key_words))

        mask = ~normalized_table.descriptions.str.lower().str.contains(
            pattern, case=False, regex=True
        )

        result = cast(pd.DataFrame, normalized_table.df[mask])

        return TransactionsTable(df=result)
