from core import TableNormalizer
import re
from functools import cached_property
from typing import List

class TransactionTableNormalizer(TableNormalizer):
    @cached_property
    def period_idx(self) -> int:
        period_phrase = self.statement_propertys['period_phrase']
        
        for i in range(len(self.df_extracted_words) - len(period_phrase)):
            if list(self.df_extracted_words["text"].iloc[i : i + len(period_phrase)].str.lower()) == period_phrase:
                return i + len(period_phrase)  # First word after match

        return None
    
    def get_month(self) -> str:
        pass
    
    def get_year(self) -> List[int]:
        detected_years = []
        
        period_values = self.df_extracted_words['text'].iloc[self.period_idx : self.period_idx + self.statement_properties['len_period_values']]
        
        for text in period_values['text']:
            if self.statement_properties['period_pattern']:
                year_match = re.search(self.statement_properties['period_pattern'], text)

                if year_match:
                    year = int(year_match.group(self.statement_properties['year_group']))
                    detected_years.append(year_match.group(year))
                    
            else:
                year_match = re.search(r'\b\d{4}\b', text)

                if year_match:
                    year = int(year_match.group())
                    detected_years.append(int)
                    
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