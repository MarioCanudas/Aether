from core import TableBoundaryDetector
from functools import cached_property
import pandas as pd
import re

class TransactionTableBoundaryDetector(TableBoundaryDetector):
    @cached_property
    def df_corrected(self):
        df = self.extracted_words.copy()
        date_pattern = self.statement_propertys['date_pattern']
        
        for i, row in df.iterrows():
            text = row['text']
            date_match = re.match(date_pattern, text)
            
            if date_match:
                date_str = date_match.group(0)
                word = text[len(date_str):]
                
                try: 
                    if not word[0] == ' ':
                        word = ' ' + word
                        
                    df.loc[i, 'text'] = date_str
                    
                    if i + 1 < len(df):
                        df.loc[i + 1, 'text'] = word + ' ' + df.loc[i + 1, 'text']
                except: 
                    continue
        return df
        
    @cached_property
    def start_idx(self) -> int:
        start_phrase = self.statement_propertys['start_phrase']
        
        for i in range(len(self.df_corrected) - len(start_phrase)):
            if list(self.df_corrected["text"].iloc[i : i + len(start_phrase)].str.lower()) == start_phrase:
                return i + len(start_phrase)  # First row after match
        
        return None
    
    @cached_property
    def end_idx(self) -> int:
        end_phrase = self.statement_propertys['end_phrase']
        
        for i in range(self.start_idx, len(self.df_corrected) - len(end_phrase)):
            if list(self.df_corrected["text"].iloc[i : i + len(end_phrase)].str.lower()) == end_phrase:
                return i
            
        return None
    
    def get_filtered_table_words(self) -> pd.DataFrame:
        if self.start_idx and self.end_idx and self.start_idx < self.end_idx:
            return self.df_corrected.iloc[self.start_idx : self.end_idx].reset_index(drop=True)
        else:
            return pd.DataFrame(columns= self.df_corrected.columns)  # Empty DataFrame if no match