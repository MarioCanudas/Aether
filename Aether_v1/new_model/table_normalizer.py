from core import TableNormalizer
import re
import pandas as pd
from functools import cached_property
from typing import List, Tuple

class TransactionTableNormalizer(TableNormalizer):
    @cached_property
    def period_idx(self) -> int:
        period_phrase = self.statement_properties['period_phrase']

        if not period_phrase:
            return None
        
        # Convert period_phrase to lowercase once for efficient comparison
        period_phrase_lower = [phrase.lower() for phrase in period_phrase]

        for i in range(len(self.df_extracted_words) - len(period_phrase)):
            # Extract the window of words
            window_words = self.df_extracted_words["text"].iloc[i : i + len(period_phrase)]
            
            # Process words: lowercase and remove trailing colon
            processed_window = [word.lower().rstrip(':') for word in window_words]
            
            # Compare the processed window with the lowercase period_phrase
            if processed_window == period_phrase_lower:
                return i + len(period_phrase)  # First word after match

        raise ValueError(f"Period phrase '{period_phrase}' not found in the extracted words.")
    
    @cached_property
    def years(self) -> List[int]:
        detected_years = []
        
        # Check if period_idx is valid
        if self.period_idx is None:
            return detected_years
            
        # Get the text values after the period phrase
        period_values = self.df_extracted_words.iloc[self.period_idx : self.period_idx + 15]
        
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
    
    @cached_property
    def months(self) -> str:
        pass
    
    def normalize_date_with_year(self, date: str, date_pattern: str, groups_date: Tuple[int], month_pattern: dict) -> str:
        year_group, month_group, day_group = groups_date
        
        date_match = re.match(date_pattern, date)
        
        if date_match:
            year = date_match.group(year_group)
            month = date_match.group(month_group)
            day = date_match.group(day_group)
            
            month = month if month.isnumeric() else month_pattern[month]
            
            return f"{year}-{month}-{day}" if len(year) == 4 else f"20{year}-{month}-{day}"
        else:
            return ""
        
    def normalize_date_without_year(self, date: str, years: List[int], date_pattern: str, groups_date: Tuple[None, int, int], month_pattern: dict) -> str:
        _, month_group, day_group = groups_date
        
        date_match = re.match(date_pattern, date)

        if len(years) == 1:
            year = years[0]
            
            if date_match:
                month = date_match.group(month_group)
                day = date_match.group(day_group)
                
                month = month_pattern[month] if not month.isnumeric() else month
                
                return f"{year}-{month}-{day}"
            else:
                return ""
        elif len(years) == 2:
            year1 = years[0]
            year2 = years[1]
            
            if date_match:
                month = date_match.group(month_group)
                day = date_match.group(day_group)
                
                month = month_pattern[month] if not month.isnumeric() else month
                
                if int(month) <= 12:
                    return f"{year1}-{month}-{day}"
                else:
                    return f"{year2}-{month}-{day}"
            else:
                return ""
        else:
            return ""  # No valid year found
            
    def normalize_dates(self, date_column: pd.Series) -> pd.Series:
        date_pattern = self.statement_properties['date_pattern']
        groups_date = self.statement_properties['date_groups']
        month_pattern = self.statement_properties['month_pattern']

        have_year: bool = groups_date[0] is not None
        
        if have_year:
            return date_column.apply(
                lambda x: self.normalize_date_with_year(x, date_pattern, groups_date, month_pattern)
            )
        else:
            years = self.years

            return date_column.apply(
                lambda x: self.normalize_date_without_year(x, years, date_pattern, groups_date, month_pattern)
            )
    
    def clean_amount(self, amount: str) -> str:
        return amount.replace(',', '').replace('$', '').replace('+', '').replace('-','')
    
    def normalize_amount_for_single_column(self, value: str, income_sign: str, expense_sign: str) -> float:
        amount = 0.0
        transaction_type = None
        
        if income_sign and not expense_sign:
            if income_sign in value:
                amount = float(self.clean_amount(value.replace(income_sign, '')))
                transaction_type = 'Abono'
            else:
                amount = float(self.clean_amount(value)) * -1
                transaction_type = 'Cargo'
        
        elif not income_sign and expense_sign:
            if expense_sign in value:
                amount = float(self.clean_amount(value.replace(expense_sign, ''))) * -1
                transaction_type = 'Cargo'
            else:
                amount = float(self.clean_amount(value))
                transaction_type = 'Abono'
        
        elif income_sign and expense_sign:
            if income_sign in value:
                amount = float(self.clean_amount(value.replace(income_sign, '')))
                transaction_type = 'Abono'
            elif expense_sign in value:
                amount = float(self.clean_amount(value.replace(expense_sign, ''))) * -1
                transaction_type = 'Cargo'
                
        return pd.Series({'Amount': amount, 'Type': transaction_type})
    
    def normalize_amount_for_multiple_columns(self, row, income_column: str, expense_column: str, balance_column: str) -> pd.Series:
        amount = 0.0
        transaction_type = None

        income_val = row[income_column]
        expense_val = row[expense_column]

        # Check if income_val is present (not NA and not empty string)
        is_income_present = not pd.isna(income_val) and income_val != ''
        # Check if expense_val is present (not NA and not empty string)
        is_expense_present = not pd.isna(expense_val) and expense_val != ''

        # Check if income_val is effectively empty (NA or empty string)
        is_income_effectively_empty = pd.isna(income_val) or income_val == ''
        # Check if expense_val is effectively empty (NA or empty string)
        is_expense_effectively_empty = pd.isna(expense_val) or expense_val == ''

        if is_income_present and is_expense_effectively_empty:
            try:
                amount = float(self.clean_amount(income_val))
                transaction_type = 'Abono'
            except ValueError:
                pass # Keep amount = 0.0, transaction_type = None
            
        elif is_expense_present and is_income_effectively_empty:
            try:
                amount = float(self.clean_amount(expense_val)) * -1
                transaction_type = 'Cargo'
            except ValueError:
                pass # Keep amount = 0.0, transaction_type = None
        
        elif balance_column and is_income_effectively_empty and is_expense_effectively_empty:
            balance_val = row[balance_column]
            # Check if balance_val is present (not NA and not empty string)
            is_balance_present = not pd.isna(balance_val) and balance_val != ''
            if is_balance_present:
                try:
                    amount = float(self.clean_amount(balance_val))
                    transaction_type = 'Saldo'
                except ValueError:
                    pass # Keep amount = 0.0, transaction_type = None
        
        return pd.Series({'Amount': amount, 'Type': transaction_type})
        
    def normalize_amounts(self, amount_columns: pd.Series | pd.DataFrame) -> pd.Series:    
        if isinstance(amount_columns, pd.Series):
            income_sign = self.statement_properties['income_sign']
            expense_sign = self.statement_properties['expense_sign']

            return amount_columns.apply(lambda x: self.normalize_amount_for_single_column(x, income_sign, expense_sign))
        else:
            income_column = self.statement_properties['income_column']
            expense_column = self.statement_properties['expense_column']
            balance_column = self.statement_properties['balance_column']

            return amount_columns.apply(lambda x: self.normalize_amount_for_multiple_columns(x, income_column, expense_column, balance_column), axis=1)
    
    def normalize_table(self) -> pd.DataFrame:
        df_table = self.df_table
        df_normalized = pd.DataFrame()
        
        date_column = self.statement_properties['date_column']
        description_column = self.statement_properties['description_column']
        amount_column = self.statement_properties['amount_column']
        
        df_normalized['Date'] = self.normalize_dates(df_table[date_column])
        df_normalized['Description'] = df_table[description_column]
        
        df_amount = self.normalize_amounts(df_table[amount_column]) if len(amount_column) > 1 else self.normalize_amounts(df_table[amount_column[0]])
        
        df_normalized['Amount'] = df_amount['Amount']
        df_normalized['Type'] = df_amount['Type']
        
        
        df_normalized['Date'] = pd.to_datetime(df_normalized['Date'])
        
        return df_normalized