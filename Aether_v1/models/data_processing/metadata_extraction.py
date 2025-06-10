import re
from typing import List
from functools import cache
from _core import MetadataExtractor
from utils import clean_amount

class DefaultMetadataExtractor(MetadataExtractor):
    @cache
    def get_period_idx(self) -> int:
        """
        Finds the index position where the statement period information starts.
        Searches for a specific phrase and returns the index after the match.
        """
        df_extracted_words = self.corrected_extracted_words.copy()
        period_phrase = self.statement_properties['period_phrase']

        if not period_phrase:
            return None
        
        # Convert period_phrase to lowercase once for efficient comparison
        period_phrase_lower = [phrase.lower() for phrase in period_phrase]

        # Search for the period phrase in the extracted words
        for i in range(len(df_extracted_words) - len(period_phrase)):
            window_words = df_extracted_words["text"].iloc[i : i + len(period_phrase)]
            processed_window = [word.lower().rstrip(':') for word in window_words]
            
            if processed_window == period_phrase_lower:
                return i + len(period_phrase)  # First word after match

        raise ValueError(f"Period phrase '{period_phrase}' not found in the extracted words.")
    
    def get_period(self):
        period_idx = self.get_period_idx()
        
    def get_initial_balance(self) -> float:
        """
        Extracts the initial balance amount from the statement text.
        Searches for the initial balance phrase and returns the following numeric value.
        """
        df_extracted_words = self.corrected_extracted_words.copy()
        initial_balance_phrase = self.statement_properties['initial_balance_phrase']
        
        if not initial_balance_phrase:
            return None
        
        # Search for initial balance phrase and extract the amount that follows
        for i in range(len(df_extracted_words) - len(initial_balance_phrase)):
            window_words = df_extracted_words["text"].iloc[i : i + len(initial_balance_phrase)]
            processed_window = [word.lower().rstrip(':') for word in window_words]
            
            if processed_window == initial_balance_phrase:
                initial_balance = df_extracted_words["text"].iloc[i + len(initial_balance_phrase)]
                initial_balance = clean_amount(initial_balance)
                
                try:
                    return float(initial_balance)
                except ValueError:
                    return None

        return None
    
    def get_years(self) -> List[int]:
        """
        Extracts year information from the statement period section.
        Uses regex patterns to identify and collect valid years.
        """
        period_idx = self.get_period_idx()
        
        df_extracted_words = self.corrected_extracted_words.copy()
        period_pattern = self.statement_properties['period_pattern']
        year_group = self.statement_properties['year_group']
        detected_years = []
        
        if period_idx is None:
            return detected_years
            
        # Search for years in the period section (limited window after period phrase)
        period_values = df_extracted_words.iloc[period_idx : period_idx + 15]
        
        for text in period_values['text']:
            # Use custom pattern if available, otherwise fallback to generic year pattern
            if period_pattern:
                year_match = re.search(period_pattern, text)
                
                if year_match:
                    try:
                        year = int(year_match.group(year_group))
                        detected_years.append(year)
                    except (ValueError, IndexError):
                        continue
                    
            else:
                year_match = re.search(r'\b20\d{2}\b', text)
                
                if year_match:
                    try:
                        year = int(year_match.group())
                        detected_years.append(year)
                    except ValueError:
                        continue
                    
        return sorted(list(set(detected_years)))
    
    def get_months(self) -> List[str]:
        return None