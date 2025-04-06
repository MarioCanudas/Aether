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
        rows = self.sorted_df.to_dict(orient='records')
        
        columns = self.statement_propertys['columns']
        
        header_row = {
            'columns': [],
            'x0': [],
            'x1': [],
        }
        
        for col in columns:
            header_row['columns'].append(col)
            words_col = col.split()
            words_num = len(words_col)
            
            words_col_verification = {col: False for col in words_col}
            
            col_x0 = None
            col_x1 = None
            
            for i, row in enumerate(rows):
                word = row['text'].strip()
                x0 = row['x0']
                x1 = row['x1']
                
                if word in words_col:
                    if words_col_verification[word]:
                        continue
                    else:
                        words_col_verification[word] = True
                    
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
                        
                    rows[i]['text'] = ''
                        
            header_row['x0'].append(col_x0)
            header_row['x1'].append(col_x1)
                    
        return header_row
    
    def construct_word(self, row: pd.Series) -> str:
        text = row['text']
        x0 = row['x0']
        x1 = row['x1']
        
        return (text, x0, x1)
    
    def group_rows(self) -> pd.DataFrame:
        sorted_df = self.sorted_df.copy()
        row_threshold = self.row_threshold
        
        sorted_df["row_group"] = (sorted_df["top"].diff().abs() > row_threshold).cumsum()
        
        sorted_df["words"] = sorted_df.apply(self.construct_word, axis=1)
        
        grouped_rows = sorted_df.groupby("row_group").agg({
            "text": lambda x: " ".join(x),  # Concatenate all words in row
            "words": lambda x: list(x),  # Keep all words in row as a list
            "top": "min",  # Top position of row
            "bottom": "max",  # Bottom position of row
            "page": "first"  # Keep page number
        }).reset_index()
        
        return grouped_rows