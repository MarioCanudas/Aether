from core import TableNormalizer
import re
import pandas as pd
from functools import cached_property
from typing import List, Tuple

def clean_amount(amount: str) -> str:
    return amount.replace(',', '').replace('$', '').replace('+', '').replace('-','')

class TransactionTableNormalizer(TableNormalizer):  
    @cached_property
    def period_idx(self) -> int:
        """
        Finds the index position where the statement period information starts.
        Searches for a specific phrase and returns the index after the match.
        """
        df_extracted_words = self.bank_detector.get_extracted_words().copy()
        statement_properties = self.bank_detector.get_statement_properties()
        period_phrase = statement_properties['period_phrase']

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
    
    def get_initial_balance(self) -> float:
        """
        Extracts the initial balance amount from the statement text.
        Searches for the initial balance phrase and returns the following numeric value.
        """
        df_extracted_words = self.bank_detector.get_extracted_words().copy()
        statement_properties = self.bank_detector.get_statement_properties()
        initial_balance_phrase = statement_properties['initial_balance_phrase']
        
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

        raise ValueError(f"Initial balance phrase '{initial_balance_phrase}' not found in the extracted words.")
        
    @cached_property
    def years(self) -> List[int]:
        """
        Extracts year information from the statement period section.
        Uses regex patterns to identify and collect valid years.
        """
        df_extracted_words = self.bank_detector.get_extracted_words().copy()
        statement_properties = self.bank_detector.get_statement_properties()
        detected_years = []
        
        if self.period_idx is None:
            return detected_years
            
        # Search for years in the period section (limited window after period phrase)
        period_values = df_extracted_words.iloc[self.period_idx : self.period_idx + 15]
        
        for text in period_values['text']:
            # Use custom pattern if available, otherwise fallback to generic year pattern
            if statement_properties['period_pattern']:
                year_match = re.search(statement_properties['period_pattern'], text)
                
                if year_match:
                    try:
                        year = int(year_match.group(statement_properties['year_group']))
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
    
    @cached_property
    def months(self) -> str:
        pass
    
    def normalize_date_with_year(self, date: str, date_pattern: str, groups_date: Tuple[int], month_pattern: dict) -> str:
        """
        Normalizes dates that already contain year information to ISO format (YYYY-MM-DD).
        Handles both numeric and text month formats.
        """
        year_group, month_group, day_group = groups_date
        
        date_match = re.match(date_pattern, date)
        
        if date_match:
            year = date_match.group(year_group)
            month = date_match.group(month_group)
            day = date_match.group(day_group)
            
            # Convert month name to number if needed
            month = month if month.isnumeric() else month_pattern[month]
            
            # Add century prefix if year is 2-digit
            return f"{year}-{month}-{day}" if len(year) == 4 else f"20{year}-{month}-{day}"
        else:
            return ""
        
    def normalize_date_without_year(self, date: str, years: List[int], date_pattern: str, groups_date: Tuple[None, int, int], month_pattern: dict) -> str:
        """
        Normalizes dates without year by inferring the year from the statement period.
        Handles single-year and cross-year periods with month-based logic.
        """
        _, month_group, day_group = groups_date
        
        date_match = re.match(date_pattern, date)

        # Single year period - straightforward assignment
        if len(years) == 1:
            year = years[0]
            
            if date_match:
                month = date_match.group(month_group)
                day = date_match.group(day_group)
                
                month = month_pattern[month] if not month.isnumeric() else month
                
                return f"{year}-{month}-{day}"
            else:
                return ""
        # Cross-year period - assign year based on month logic        
        elif len(years) == 2:
            year1 = years[0]
            year2 = years[1]
            
            if date_match:
                month = date_match.group(month_group)
                day = date_match.group(day_group)
                
                month = month_pattern[month] if not month.isnumeric() else month
                
                # Assign year based on month value
                if int(month) <= 12:
                    return f"{year1}-{month}-{day}"
                else:
                    return f"{year2}-{month}-{day}"
            else:
                return ""
        else:
            return ""  # No valid year found
            
    def normalize_dates(self, date_column: pd.Series) -> pd.Series:
        """
        Normalizes all dates in a column to ISO format based on date pattern analysis.
        Routes to appropriate normalization method based on year presence.
        """
        statement_properties = self.bank_detector.get_statement_properties()
        date_pattern = statement_properties['date_pattern']
        groups_date = statement_properties['date_groups']
        month_pattern = statement_properties['month_pattern']

        have_year: bool = groups_date[0] is not None
        
        # Route to appropriate normalization method
        if have_year:
            return date_column.apply(
                lambda x: self.normalize_date_with_year(x, date_pattern, groups_date, month_pattern)
            )
        else:
            years = self.years

            return date_column.apply(
                lambda x: self.normalize_date_without_year(x, years, date_pattern, groups_date, month_pattern)
            )
    
    def normalize_amount_for_single_column(self, value: str, income_sign: str, expense_sign: str) -> float:
        """
        Normalizes amounts from a single column using sign indicators.
        Determines transaction type and applies appropriate sign based on income/expense indicators.
        """
        amount = 0.0
        transaction_type = None
        
        # Handle different sign indicator combinations
        if income_sign and not expense_sign:
            if income_sign in value:
                amount = float(clean_amount(value.replace(income_sign, '')))
                transaction_type = 'Abono'
            else:
                amount = float(clean_amount(value)) * -1
                transaction_type = 'Cargo'
        
        elif not income_sign and expense_sign:
            if expense_sign in value:
                amount = float(clean_amount(value.replace(expense_sign, ''))) * -1
                transaction_type = 'Cargo'
            else:
                amount = float(clean_amount(value))
                transaction_type = 'Abono'
        
        elif income_sign and expense_sign:
            if income_sign in value:
                amount = float(clean_amount(value.replace(income_sign, '')))
                transaction_type = 'Abono'
            elif expense_sign in value:
                amount = float(clean_amount(value.replace(expense_sign, ''))) * -1
                transaction_type = 'Cargo'
                
        return pd.Series({'Amount': amount, 'Type': transaction_type})
    
    def normalize_amount_for_multiple_columns(self, row, income_column: str, expense_column: str, balance_column: str) -> pd.Series:
        """
        Normalizes amounts from separate income/expense columns.
        Handles various combinations including balance-only transactions and conflicting amounts.
        """
        amount = 0.0
        transaction_type = None

        income_val = row[income_column]
        expense_val = row[expense_column]

        # Determine value presence for each column
        is_income_present = not pd.isna(income_val) and income_val != ''
        is_expense_present = not pd.isna(expense_val) and expense_val != ''
        is_income_effectively_empty = pd.isna(income_val) or income_val == ''
        is_expense_effectively_empty = pd.isna(expense_val) or expense_val == ''

        # Process based on which columns have values
        if is_income_present and is_expense_effectively_empty:
            try:
                amount = float(clean_amount(income_val))
                transaction_type = 'Abono'
            except ValueError:
                pass
            
        elif is_expense_present and is_income_effectively_empty:
            try:
                amount = float(clean_amount(expense_val)) * -1
                transaction_type = 'Cargo'
            except ValueError:
                pass
        
        # Handle balance column when both income/expense are empty
        elif balance_column and is_income_effectively_empty and is_expense_effectively_empty:
            balance_val = row[balance_column]
            is_balance_present = not pd.isna(balance_val) and balance_val != ''
            if is_balance_present:
                try:
                    amount = float(clean_amount(balance_val))
                    transaction_type = 'Saldo'
                except ValueError:
                    pass
        
        # Handle conflicting amounts (both income and expense present)        
        elif is_income_present and is_expense_present:
            try:
                income_amount = float(clean_amount(income_val))
                expense_amount = float(clean_amount(expense_val))
                
                if income_amount > expense_amount:
                    amount = income_amount - expense_amount
                    transaction_type = 'Abono'
                else:
                    amount = expense_amount - income_amount
                    transaction_type = 'Cargo'
            except ValueError:
                pass
        
        return pd.Series({'Amount': amount, 'Type': transaction_type})
        
    def normalize_amounts(self, amount_columns: pd.Series | pd.DataFrame) -> pd.Series:
        """
        Routes amount normalization based on column structure.
        Uses single-column method for unified amounts or multi-column method for separate income/expense.
        """
        statement_properties = self.bank_detector.get_statement_properties()
        
        # Route based on input type
        if isinstance(amount_columns, pd.Series):
            income_sign = statement_properties['income_sign']
            expense_sign = statement_properties['expense_sign']

            return amount_columns.apply(lambda x: self.normalize_amount_for_single_column(x, income_sign, expense_sign))
        else:
            income_column = statement_properties['income_column']
            expense_column = statement_properties['expense_column']
            balance_column = statement_properties['balance_column']

            return amount_columns.apply(lambda x: self.normalize_amount_for_multiple_columns(x, income_column, expense_column, balance_column), axis=1)
        
    def add_initial_balance(self, df_table: pd.DataFrame) -> pd.DataFrame:
        """
        Adds initial balance row to the transaction table.
        Either marks existing balance entry or creates new initial balance record.
        """
        statement_type = self.bank_detector.detect_statement_type()
        
        # Skip initial balance for credit statements
        if statement_type == 'credit':
            return df_table
                
        statement_properties = self.bank_detector.get_statement_properties()
        initial_balance_description = statement_properties['initial_balance_description']
        
        # Try to find and mark existing initial balance entry
        if initial_balance_description is not None:
            normalized_target = initial_balance_description.strip().lower()
            condition = df_table['Description'].str.strip().str.lower() == normalized_target
            
            if condition.any():
                df_table.loc[condition, 'Type'] = 'Saldo Inicial'
                return df_table
        
        # Create new initial balance entry if not found
        initial_balance_amount = self.get_initial_balance()
        first_date = df_table['Date'].min()
        initial_balance = {'Date': first_date, 'Description': 'Saldo Inicial', 'Amount': initial_balance_amount, 'Type': 'Saldo Inicial'}
        df_table = pd.concat([df_table, pd.DataFrame([initial_balance])], ignore_index=True)
            
        return df_table
    
    def normalize_table(self) -> pd.DataFrame:
        """
        Main method that orchestrates the complete table normalization process.
        Normalizes dates and amounts, adds initial balance, and sorts by date.
        """
        df_table = self.df_table
        df_normalized = pd.DataFrame()      
        
        statement_properties = self.bank_detector.get_statement_properties()
        amount_column = statement_properties['amount_column']
        
        # Normalize each column type
        df_normalized['Date'] = self.normalize_dates('Date')
        df_normalized['Description'] = df_table['Description']
        
        # Handle single vs multiple amount columns
        df_amount = self.normalize_amounts(df_table[amount_column]) if len(amount_column) > 1 else self.normalize_amounts(df_table[amount_column[0]])
        
        df_normalized['Amount'] = df_amount['Amount']
        df_normalized['Type'] = df_amount['Type']
        
        # Convert dates and finalize
        df_normalized['Date'] = pd.to_datetime(df_normalized['Date'])
        df_normalized = self.add_initial_balance(df_normalized)
        
        return df_normalized.sort_values(by='Date')