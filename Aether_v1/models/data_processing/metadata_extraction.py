import re
from typing import List, Tuple, Literal
from functools import cache
from datetime import date
from dateutil.relativedelta import relativedelta
import pandas as pd
from ..core import MetadataExtractor
from ..document_processing import StatementType
from utils import clean_amount, search_phrase_in_df

class DefaultMetadataExtractor(MetadataExtractor):
    @cache
    def get_period_idx(self) -> int:
        """
        Finds the index position where the statement period information starts.
        Searches for a specific phrase and returns the index after the match.
        """
        df_extracted_words = self.corrected_extracted_words.copy()
        period_phrase = self.statement_properties['period_phrase']

        if not period_phrase or df_extracted_words.empty:
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
    
    @cache
    def get_period(self) -> Tuple[date, date] | None:
        """"""
        period_idx = self.get_period_idx()
        
        print(period_idx)
        
        if period_idx is None:
            raise ValueError("Period phrase not found in the extracted words.")
        
        search_window: pd.DataFrame = self.corrected_extracted_words.iloc[period_idx : period_idx + 20]
        texts: list[str] = search_window['text'].tolist()
        
        period_pattern: str | None = self.statement_properties['period_pattern']
        
        if not period_pattern:
            return None
        
        pattern_parts: list[str] = period_pattern.split(' ')
        n_parts: int = len(pattern_parts)
        
        found_dates = []
        for i in range(len(texts) - n_parts):
            candidate = ' '.join(texts[i:i+n_parts]) if n_parts > 1 else texts[i]
            date_match = re.match(period_pattern, candidate)
            
            if date_match:
                found_dates.append(date_match)
                
            if len(found_dates) == 2:
                break
                
        if not found_dates:
            return None
            
        period_dates = []
        for date_match in found_dates:
            # Convert month to number if needed
            month_pattern: dict[str, str] | None = self.statement_properties['period_month_pattern']
            year_group: int = self.statement_properties['period_group']['year']
            month_group: int = self.statement_properties['period_group']['month']
            day_group: int = self.statement_properties['period_group']['day']
            
            year: str = date_match.group(year_group)
            month: str = date_match.group(month_group)
            day: str = date_match.group(day_group)
            
            # Validate date values
            if len(year) == 2:
                year = '20' + year
            
            if month_pattern is not None and month in month_pattern.keys():
                month = month_pattern[month]
            
            if not day.isdigit():
                raise ValueError(f"Invalid day format: {day}")
            
            date_period = date(int(year), int(month), int(day))
            period_dates.append(date_period)
            
        period_dates = list(set(period_dates))
            
        if len(period_dates) == 0:
            raise ValueError("No period dates found in the statement.")
        elif len(period_dates) == 1:
            previous_date = period_dates[0] - relativedelta(months=1) + relativedelta(days=1)
            period = (previous_date, period_dates[0])
            return period
        elif len(period_dates) == 2:
            return tuple(sorted(period_dates))
        else:
            raise ValueError("More than 2 period dates found in the statement.")
        
    @cache
    def get_generated_amount(self) -> float | None:
        """
        Get the generated amount from the statement text.
        Searches for the generated amount phrase and returns the following numeric value.
        """
        if self.statement_properties['statement_type'] == StatementType.CREDIT:
            return None
        
        df_extracted_words = self.corrected_extracted_words.copy()
        
        generated_amount_phrase = self.statement_properties['generated_amount_phrase']
        
        if not generated_amount_phrase or df_extracted_words.empty:
            return None
        
        phrase_idx = search_phrase_in_df(df_extracted_words, generated_amount_phrase)
        
        if phrase_idx is None:
            return None
        
        search_window: pd.DataFrame = df_extracted_words.iloc[phrase_idx + len(generated_amount_phrase) : phrase_idx + 15]
        texts: list[str] = search_window['text'].tolist()
        
        for text in texts:
            text = clean_amount(text)
            
            try: 
                amount = float(text)
                
                if amount > 0:
                    return amount
            except ValueError:
                continue
        else:
            return None
                
    def get_balance(self, balance: Literal['initial', 'final']) -> float | None:
        """
        Extracts the initial balance amount from the statement text.
        Searches for the initial balance phrase and returns the following numeric value.
        """
        if self.statement_properties['statement_type'] == StatementType.CREDIT:
            return None
        
        df_extracted_words = self.corrected_extracted_words.copy()
        
        if balance == 'initial':
            balance_phrase = self.statement_properties['initial_balance_phrase']
        elif balance == 'final':
            balance_phrase = self.statement_properties['final_balance_phrase']
        else:
            raise ValueError(f"Invalid balance type: {balance}")
        
        if not balance_phrase or df_extracted_words.empty:
            return None
        
        # Search for initial balance phrase and extract the amount that follows
        for i in range(len(df_extracted_words) - len(balance_phrase)):
            window_words = df_extracted_words["text"].iloc[i : i + len(balance_phrase)]
            processed_window = [word.lower().rstrip(':') for word in window_words]
            
            if processed_window == balance_phrase:
                balance = df_extracted_words["text"].iloc[i + len(balance_phrase)]
                balance = clean_amount(balance)
                
                try:
                    return float(balance)
                except ValueError:
                    return None

        return None    
    
    def get_years(self) -> List[int]:
        """
        
        """
        period: Tuple[date, date] | None = self.get_period()
        
        if not period: 
            period_idx = self.get_period_idx()
            
            df_extracted_words = self.corrected_extracted_words.copy()
            period_pattern = self.statement_properties['period_pattern']
            year_group = self.statement_properties['year_group']
            detected_years = []
            
            if period_idx is None or df_extracted_words.empty:
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
        
        else:
            years = [period[0].year, period[1].year]
            years = list(set(years))
            
            return sorted(years)
    
    def get_months(self) -> List[str]:
        """
        Extracts the months from the statement text.
        """
        period: Tuple[date, date] | None = self.get_period()
        
        if not period:
            return None
        
        months = [period[0].month, period[1].month]
        months = list(set(months))
        
        return sorted(months)