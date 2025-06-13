import pandas as pd
from ..core import ColumnSegmenter, RowSegmenter

class DefaultColumnSegmenter(ColumnSegmenter):
    def delimit_column_positions(self) -> dict:
        filtered_words = self.filtered_table_words
        
        rows = filtered_words.to_dict(orient='records') # Convert the DataFrame to a list of dictionaries
        columns = self.statement_properties['columns']
        
        # Initialize a dictionary to store the column positions
        delimitations = {
            'column': [],
            'x0': [],
            'x1': [],
        }
        
        for col in columns:
            delimitations['column'].append(col) # Add the column name to the list
            words_col = col.split() # Split the column name into a list of words
            words_num = len(words_col) # Get the number of words in the column name
            
            # Initialize a dictionary to store the verification of the column name
            words_col_verification = {col: False for col in words_col}
            
            col_x0 = None
            col_x1 = None
            
            for row in rows:
                word = row['text'].strip() # Get the text of the row
                x0 = row['x0'] # Get the x0 position of the row
                x1 = row['x1'] # Get the x1 position of the row
                
                if word in words_col:
                    if words_col_verification[word]: # If the word is already verified, skip it
                        continue
                    else:
                        words_col_verification[word] = True # Verify the word
                    
                    word_idx = words_col.index(word) # Get the index of the word
                    
                    if words_num == 1: # If the column name has only one word, set the x0 and x1 positions
                        col_x0 = x0
                        col_x1 = x1
                        break 
                    
                    elif words_num > 1: # If the column name has more than one word, set the x0 and x1 positions
                        if word_idx == 0 and col_x0 is None:
                            col_x0 = x0
                        elif word_idx == words_num - 1 and col_x1 is None:
                            col_x1 = x1
                            
                        if col_x0 is not None and col_x1 is not None: # If the x0 and x1 positions are set, break the loop
                            break
            
            # Add the x0 and x1 positions to the list, once the loop is finished
            delimitations['x0'].append(col_x0)
            delimitations['x1'].append(col_x1)
                    
        return delimitations
    
class DefaultRowSegmenter(RowSegmenter):
    def get_row_threshold(self) -> float:
        filtered_words = self.filtered_table_words
        
        top_diffs = filtered_words.groupby("page")["top"].diff()
        positive_diffs = top_diffs[top_diffs > 0].dropna()

        q1 = positive_diffs.quantile(0.25)
        q3 = positive_diffs.quantile(0.75)
        iqr = q3 - q1

        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr

        filtered_diffs = positive_diffs[(positive_diffs >= lower_bound) & (positive_diffs <= upper_bound)]
        
        min_threshold = 2
        max_threshold = 7
        
        return min(max(filtered_diffs.median(), min_threshold), max_threshold)
    
    def group_rows(self) -> pd.DataFrame:
        filtered_words = self.filtered_table_words
        row_threshold = self.get_row_threshold()    
        
        filtered_words["row_group"] = (filtered_words["top"].diff().abs() > row_threshold).cumsum()
        
        filtered_words["words"] = filtered_words.apply(lambda row: (row['text'], row['x0'], row['x1']), axis=1)
        
        grouped_rows = filtered_words.groupby("row_group").agg({
            "text": lambda x: " ".join(x),  # Concatenate all words in row
            "words": lambda x: list(x),  # Keep all words in row as a list
            "top": "min",  # Top position of row
            "bottom": "max",  # Bottom position of row
            "page": "first"  # Keep page number
        }).reset_index()
        
        return grouped_rows
    