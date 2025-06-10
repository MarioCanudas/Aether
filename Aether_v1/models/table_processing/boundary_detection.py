import pandas as pd
from functools import cache
from _core import TableBoundaryDetector
from utils import search_phrase_in_df

class DefaultBoundaryDetector(TableBoundaryDetector):
    @cache
    def get_start_idx(self) -> int:
        extracted_words = self.corrected_extracted_words
        start_phrase = self.statement_properties['start_phrase']
        
        try:
            return search_phrase_in_df(extracted_words, start_phrase, type_return='idx') + len(start_phrase)
        except:
            return None

    @cache
    def get_end_idx(self) -> int:
        start_idx = self.get_start_idx()
        
        if start_idx is None:
            return None
        
        extracted_words = self.corrected_extracted_words
        end_phrase = self.statement_properties['end_phrase']
        
        return search_phrase_in_df(extracted_words, end_phrase, type_return='idx') + len(end_phrase)
    
    @cache
    def get_filtered_table_words(self) -> pd.DataFrame:
        extracted_words = self.corrected_extracted_words
        start_idx = self.get_start_idx()
        end_idx = self.get_end_idx()
        
        if start_idx and end_idx and start_idx < end_idx:
            # Filter the DataFrame to include only the rows between the start and end indices
            return extracted_words.iloc[start_idx : end_idx].sort_values(by=["page", "top"]).reset_index(drop=True)
        else:
            return pd.DataFrame(columns= extracted_words)  # Empty DataFrame if no match
    