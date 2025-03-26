from core import TableNormalizer
import re
import pandas as pd
from functools import cached_property
from typing import List

class TransactionTableNormalizer(TableNormalizer):
    @cached_property
    def period_idx(self) -> int:
        period_phrase = self.statement_properties['period_phrase']
        
        for i in range(len(self.df_extracted_words) - len(period_phrase)):
            if list(self.df_extracted_words["text"].iloc[i : i + len(period_phrase)].str.lower()) == period_phrase:
                return i + len(period_phrase)  # First word after match

        return None
    
    def get_month(self) -> str:
        pass
    
    def get_year(self) -> List[int]:
        detected_years = []
        
        # Check if period_idx is valid
        if self.period_idx is None:
            return detected_years
            
        # Get the text values after the period phrase
        period_values = self.df_extracted_words.iloc[self.period_idx : self.period_idx + 10]
        
        for text in period_values['text']:
            if self.statement_properties['period_pattern']:
                year_match = re.search(self.statement_properties['period_pattern'], text)
                
                if year_match:
                    try:
                        year = int(year_match.group(self.statement_properties['year_group']))
                        detected_years.append(year)  # Append the integer directly
                    except (ValueError, IndexError):
                        continue
                    
            else:
                year_match = re.search(r'\b20\d{2}\b', text)  # More specific regex for years
                
                if year_match:
                    try:
                        year = int(year_match.group())
                        detected_years.append(year)  # Append the integer, not 'int'
                    except ValueError:
                        continue
                    
        return sorted(list(set(detected_years)))
    
    def normalize_date(self, value: str) -> str:
        date_match = re.search(self.statement_properties['date_pattern'], value)
        
        if date_match:
            pass
        
    def normalize_amount(self, value: str) -> float:
        pass
    
    def normalize_table(self) -> pd.DataFrame:
        df_normalized = pd.DataFrame()
        
        date_column = self.statement_properties['date_column']
        description_column = self.statement_properties['description_column']
        amount_column = self.statement_properties['amount_column']
        
        df_normalized['date'] = self.df_table[date_column].apply(self.normalize_date)
        df_normalized['description'] = self.df_table[description_column]
        df_normalized['amount'] = self.df_table[amount_column].apply(self.normalize_amount)
        
        df_normalized['date'] = pd.to_datetime(normalized['date'])
        
        return df_normalized