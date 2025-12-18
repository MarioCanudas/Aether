from typing import Any, cast

import pandas as pd
from models.delimitations import ColumnDelimitations
from models.tables import GroupedRows

from ..core import ColumnSegmenter, RowSegmenter


class DefaultColumnSegmenter(ColumnSegmenter):
    def delimit_column_positions(self) -> ColumnDelimitations:
        filtered_words = self.filtered_table_words

        rows: list[dict[str, Any]] = (
            filtered_words.records
        )  # Convert the DataFrame to a list of dictionaries
        columns = self.bank_properties.columns

        # Initialize a dictionary to store the column positions
        delimitations = ColumnDelimitations(columns=[], x0=[], x1=[])

        for col in columns:
            delimitations.columns.append(col)  # Add the column name to the list
            words_col = col.split()  # Split the column name into a list of words
            words_num = len(words_col)  # Get the number of words in the column name

            # Initialize a dictionary to store the verification of the column name
            words_col_verification: dict[str, bool] = {col: False for col in words_col}

            col_x0: float | None = None
            col_x1: float | None = None

            for row in rows:
                word = row["text"].strip()  # Get the text of the row
                x0 = row["x0"]  # Get the x0 position of the row
                x1 = row["x1"]  # Get the x1 position of the row

                if word in words_col:
                    if words_col_verification[word]:  # If the word is already verified, skip it
                        continue
                    else:
                        words_col_verification[word] = True  # Verify the word

                    word_idx = words_col.index(word)  # Get the index of the word

                    if (
                        words_num == 1
                    ):  # If the column name has only one word, set the x0 and x1 positions
                        col_x0 = x0
                        col_x1 = x1
                        break

                    elif (
                        words_num > 1
                    ):  # If the column name has more than one word, set the x0 and x1 positions
                        if word_idx == 0 and col_x0 is None:
                            col_x0 = x0
                        elif word_idx == words_num - 1 and col_x1 is None:
                            col_x1 = x1

                        if (
                            col_x0 is not None and col_x1 is not None
                        ):  # If the x0 and x1 positions are set, break the loop
                            break

            # Add the x0 and x1 positions to the list, once the loop is finished
            delimitations.x0.append(col_x0 if col_x0 is not None else 0)
            delimitations.x1.append(col_x1 if col_x1 is not None else 0)

        return delimitations


class DefaultRowSegmenter(RowSegmenter):
    def get_row_threshold(self) -> float:
        df_filtered_words = self.filtered_table_words.df

        top_diffs = df_filtered_words.groupby("page")["top"].diff()
        top_diffs = cast(pd.Series, top_diffs)

        positive_diffs = cast(pd.Series, top_diffs[top_diffs >= 0]).dropna()

        q1 = positive_diffs.quantile(0.25)
        q3 = positive_diffs.quantile(0.75)
        iqr = q3 - q1

        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr

        filtered_diffs = positive_diffs[
            (positive_diffs >= lower_bound) & (positive_diffs <= upper_bound)
        ]

        min_threshold = 2
        max_threshold = 7

        median: float = cast(Any, filtered_diffs).median()
        return cast(float, min(max(median, min_threshold), max_threshold))

    def group_rows(self) -> GroupedRows:
        df_filtered_words = self.filtered_table_words.df
        row_threshold = self.get_row_threshold()

        df_filtered_words["row_group"] = (
            df_filtered_words["top"].diff().abs() > row_threshold
        ).cumsum()

        df_filtered_words["words"] = df_filtered_words.apply(
            lambda row: (row["text"], row["x0"], row["x1"]), axis=1
        )

        grouped_rows = (
            df_filtered_words.groupby("row_group")
            .agg(
                {
                    "text": lambda x: " ".join(x),  # Concatenate all words in row
                    "words": lambda x: list(x),  # Keep all words in row as a list
                    "top": "min",  # Top position of row
                    "bottom": "max",  # Bottom position of row
                    "page": "first",  # Keep page number
                }
            )
            .reset_index()
        )

        return GroupedRows(df=grouped_rows)
