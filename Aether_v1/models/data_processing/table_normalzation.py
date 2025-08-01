import pandas as pd
import re
from typing import List, Tuple
from ..core import ColumnNormalizer, TableNormalizer
from utils import clean_amount

class DateNormalizer(ColumnNormalizer):
    @staticmethod
    def normalize_date_with_year(date: str, date_pattern: str, groups_date: Tuple[int], month_pattern: dict) -> str:
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
    
    @staticmethod
    def normalize_date_without_year(date: str, years: List[int], date_pattern: str, groups_date: Tuple[None, int, int], month_pattern: dict) -> str:
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
            
    def normalize_column(self, date_column: pd.Series, years: List[int]) -> pd.Series:
        """
        Normalizes all dates in a column to ISO format based on date pattern analysis.
        Routes to appropriate normalization method based on year presence.
        """
        date_pattern = self.statement_properties['date_pattern']
        groups_date = self.statement_properties['date_groups']
        month_pattern = self.statement_properties['month_pattern']

        have_year: bool = groups_date[0] is not None
        
        # Route to appropriate normalization method
        if have_year:
            return date_column.apply(
                lambda x: self.normalize_date_with_year(x, date_pattern, groups_date, month_pattern)
            )
        else:
            return date_column.apply(
                lambda x: self.normalize_date_without_year(x, years, date_pattern, groups_date, month_pattern)
            )
        
class AmountNormalizer(ColumnNormalizer):
    @staticmethod
    def normalize_amount_for_single_column(value: str, income_sign: str, expense_sign: str) -> float:
        """
        Normalizes amounts from a single column using sign indicators.
        Determines transaction type and applies appropriate sign based on income/expense indicators.
        """
        amount = 0.0
        transaction_type = None
        
        # Convert value to string to handle both string and float inputs
        value = str(value)
        
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
                
        return pd.Series({'amount': amount, 'type': transaction_type})
    
    @staticmethod
    def normalize_amount_for_multiple_columns(row, income_column: str, expense_column: str, balance_column: str) -> pd.Series:
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
                amount = float(clean_amount(str(income_val)))
                transaction_type = 'Abono'
            except ValueError:
                pass
            
        elif is_expense_present and is_income_effectively_empty:
            try:
                amount = float(clean_amount(str(expense_val))) * -1
                transaction_type = 'Cargo'
            except ValueError:
                pass
        
        # Handle balance column when both income/expense are empty
        elif balance_column and is_income_effectively_empty and is_expense_effectively_empty:
            balance_val = row[balance_column]
            is_balance_present = not pd.isna(balance_val) and balance_val != ''
            if is_balance_present:
                try:
                    amount = float(clean_amount(str(balance_val)))
                    transaction_type = 'Saldo'
                except ValueError:
                    pass
        
        # Handle conflicting amounts (both income and expense present)        
        elif is_income_present and is_expense_present:
            try:
                income_amount = float(clean_amount(str(income_val)))
                expense_amount = float(clean_amount(str(expense_val)))
                
                if income_amount > expense_amount:
                    amount = income_amount - expense_amount
                    transaction_type = 'Abono'
                else:
                    amount = expense_amount - income_amount
                    transaction_type = 'Cargo'
            except ValueError:
                pass
        
        return pd.Series({'amount': amount, 'type': transaction_type})
        
    def normalize_column(self, amount_columns: pd.Series | pd.DataFrame) -> pd.Series:
        """
        Routes amount normalization based on column structure.
        Uses single-column method for unified amounts or multi-column method for separate income/expense.
        """
        statement_properties = self.statement_properties
        
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

class DefaultTableNormalizer(TableNormalizer):
    def add_initial_balance(self, reconstructed_table: pd.DataFrame, initial_balance: float) -> pd.DataFrame:
        """
        Adds initial balance row to the transaction table.
        Either marks existing balance entry or creates new initial balance record.
        """
        statement_type = self.statement_properties['statement_type']
        
        # Skip initial balance for credit statements
        if statement_type == 'credit':
            return reconstructed_table
                
        initial_balance_description = self.statement_properties['initial_balance_description']
        
        # Try to find and mark existing initial balance entry
        if initial_balance_description is not None:
            normalized_target = initial_balance_description.strip().lower()
            condition = reconstructed_table['description'].str.strip().str.lower() == normalized_target
            
            if condition.any():
                reconstructed_table.loc[condition, 'type'] = 'Saldo inicial'
                return reconstructed_table
        
        # Create new initial balance entry if not found
        first_date = reconstructed_table['date'].min()
        initial_balance_row = {'date': first_date, 'description': 'Saldo inicial', 'amount': initial_balance, 'type': 'Saldo inicial'}
        reconstructed_table = pd.concat([reconstructed_table, pd.DataFrame([initial_balance_row])], ignore_index=True)
            
        return reconstructed_table
    
    def normalize_table(self, years: List[int], initial_balance: float) -> pd.DataFrame:
        """
        Main method that orchestrates the complete table normalization process.
        Normalizes dates and amounts, adds initial balance, and sorts by date.
        """
        reconstructed_table = self.reconstructed_table
        
        if reconstructed_table.empty:
            raise ValueError("Reconstructed table is empty")
        
        df_normalized = pd.DataFrame()      
        
        amount_column = self.statement_properties['amount_column']
        
        # Normalize each column type
        df_normalized['date'] = self.date_normalizer.normalize_column(reconstructed_table['date'], years)
        df_normalized['description'] = reconstructed_table['description']
        
        # Handle single vs multiple amount columns
        df_amount = self.amount_normalizer.normalize_column(reconstructed_table[amount_column]) if len(amount_column) > 1 else self.amount_normalizer.normalize_column(reconstructed_table[amount_column[0]])
        
        df_normalized['amount'] = df_amount['amount']
        df_normalized['type'] = df_amount['type']
        
        # Convert dates and finalize
        df_normalized['date'] = pd.to_datetime(df_normalized['date'])
        df_normalized = self.add_initial_balance(df_normalized, initial_balance)
        
        return df_normalized.sort_values(by='date')
