from core import RowSegmenter
import pandas as pd
import numpy as np
from functools import cached_property

class TransactionRowSegmenter(RowSegmenter):
    @cached_property
    def sorted_df(self) -> pd.DataFrame:
        return self.df_table.sort_values(by=["page", "top"]).reset_index(drop=True)
    
    @cached_property
    def row_threshold(self) -> float:
        top_diffs = self.sorted_df.groupby("page")["top"].diff()
        positive_diffs = top_diffs[top_diffs > 0].dropna()

        q1 = positive_diffs.quantile(0.25)
        q3 = positive_diffs.quantile(0.75)
        iqr = q3 - q1

        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr

        filtered_diffs = positive_diffs[(positive_diffs >= lower_bound) & (positive_diffs <= upper_bound)]

        return filtered_diffs.mean()
    
    def group_rows(self) -> pd.DataFrame:
        self.sorted_df["row_group"] = (self.sorted_df["top"].diff().abs() > self.row_threshold).cumsum()
        grouped_rows = self.sorted_df.groupby("row_group").agg({
            "text": lambda x: " ".join(x),  # Concatenate words in row order
            "x0": lambda x: list(x),  # Keep all x0 values as a list
            "x1": lambda x: list(x), # Right-most position of row
            "top": "min",  # Top position of row
            "bottom": "max",  # Bottom position of row
            "page": "first"  # Keep page number
        }).reset_index()
        
        return grouped_rows