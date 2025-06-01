from core import TableBoundaryDetector
from functools import cached_property
import pandas as pd
import re

class TransactionTableBoundaryDetector(TableBoundaryDetector):
    @cached_property
    def df_corrected(self):
        df = self.extracted_words
        
        amount_pattern = r'^\$?(0|[1-9]\d{0,2}(?:,\d{3})*)\.\d{2}$'
        date_pattern = self.statement_propertys['date_pattern']
        
        for i, row in df.iterrows():
            text = str(row['text']).strip()
            
            date_match = re.match(date_pattern, text)
            amount_match = re.match(amount_pattern, text)
            
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
                
            elif amount_match:
                previous_text = df.loc[i - 1, 'text']
                if previous_text == '+' or previous_text == '-':
                    df.loc[i, 'text'] = previous_text + text
                
        return df   
        
    @cached_property
    def start_idx(self) -> int:
        df = self.df_corrected
        start_phrase = self.statement_propertys['start_phrase']
        
        for i in range(len(df) - len(start_phrase)):
            if list(df["text"].iloc[i : i + len(start_phrase)].str.lower()) == start_phrase:
                return i + len(start_phrase)  # First row after match
        
        return None
    
    @cached_property
    def end_idx(self) -> int:
        df = self.df_corrected
        
        start_idx = self.start_idx
        
        if start_idx is None:
            return None
        
        end_phrase = self.statement_propertys['end_phrase']
        
        for i in range(start_idx, len(df) - len(end_phrase)):
            if list(df["text"].iloc[i : i + len(end_phrase)].str.lower()) == end_phrase:
                return i
            
        return None
    
    def get_filtered_table_words(self) -> pd.DataFrame:
        df = self.df_corrected
        start_idx = self.start_idx
        end_idx = self.end_idx
        
        if start_idx and end_idx and start_idx < end_idx:
            return df.iloc[start_idx : end_idx].reset_index(drop=True)
        else:
            return pd.DataFrame(columns= df)  # Empty DataFrame if no match