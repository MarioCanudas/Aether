from core import RowSegmenter
import pandas as pd
import numpy as np
from functools import cached_property

class TransactionRowSegmenter(RowSegmenter):
    @cached_property
    def sorted_df(self) -> pd.DataFrame:
        df_table = self.df_table.copy()
        
        return df_table.sort_values(by=["page", "top"]).reset_index(drop=True)
    
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
    
    def get_header_row(self) -> dict:
        df_table = self.df_table.copy()
        
        columns = self.statement_propertys['columns']
        
        header_row = {
            'columns': [],
            'x0': [],
            'x1': [],
        }
        
        used_words_idx = []
        
        for col in columns:
            header_row['columns'].append(col)
            
            words_col = col.split()
            words_num = len(words_col)
            
            col_x0 = None
            col_x1 = None
            
            for i, row in df_table.iterrows():
                if i in used_words_idx:
                    continue
                
                word = row['text'].strip()
                x0 = row['x0']
                x1 = row['x1']
                
                if word in words_col:
                    used_words_idx.append(i)
                    word_idx = words_col.index(word)
                    
                    if words_num == 1:
                        col_x0 = x0
                        col_x1 = x1
                        
                        break 
                    elif words_num > 1:
                        if word_idx == 0 and col_x0 is None:
                            col_x0 = x0
                        elif word_idx == words_num - 1 and col_x1 is None:
                            col_x1 = x1
                            
                        if col_x0 is not None and col_x1 is not None:
                            break
                        
            header_row['x0'].append(col_x0)
            header_row['x1'].append(col_x1)
                    
        return header_row
    
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