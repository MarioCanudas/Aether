import pandas as pd
import re
from typing import Any, cast
from utils import clean_amount
from models.amounts import AmountSigns, AmountColumns
from models.bank_properties import BankProperties
from models.dates import DateGroups
from models.tables import ReconstructedTable, TransactionsTable
from ..core import ColumnNormalizer, TableNormalizer

class DateNormalizer(ColumnNormalizer):
    @staticmethod
    def normalize_date_with_year(date: str, date_pattern: str, groups_date: DateGroups, month_pattern: dict[str, str]) -> str:
        """
        Normalizes dates that already contain year information to ISO format (YYYY-MM-DD).
        Handles both numeric and text month formats.
        """
        date_match = re.match(date_pattern, date)
        
        if date_match:
            year = date_match.group(groups_date.year) if groups_date.year is not None else ""
            month = date_match.group(groups_date.month)
            day = date_match.group(groups_date.day)
            
            # Convert month name to number if needed
            month = month if month.isnumeric() else month_pattern[month]
            
            # Add century prefix if year is 2-digit
            return f"{year}-{month}-{day}" if len(year) == 4 else f"20{year}-{month}-{day}"
        else:
            return ""
    
    @staticmethod
    def normalize_date_without_year(date: str, years: list[int], date_pattern: str, groups_date: DateGroups, month_pattern: dict[str, str]) -> str:
        """
        Normalizes dates without year by inferring the year from the statement period.
        Handles single-year and cross-year periods with month-based logic.
        """
        month_group = groups_date.month
        day_group = groups_date.day
        
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
                if 1 <= int(month) <= 6:
                    return f"{year2}-{month}-{day}"
                else:
                    return f"{year1}-{month}-{day}"
            else:
                return ""
        else:
            raise ValueError(f"Invalid detected years: {years}")
            
    def normalize_column(self, reconstructed_table: ReconstructedTable | Any, bank_properties: BankProperties | Any = None, years: list[int] | Any = None) -> pd.Series:
        """
        Normalizes all dates in a column to ISO format based on date pattern analysis.
        Routes to appropriate normalization method based on year presence.
        """
        if not isinstance(reconstructed_table, ReconstructedTable):
             # Try to handle if it was passed as something else, or just annotate correctly
             pass

        date_column = reconstructed_table.dates
        
        date_groups = bank_properties.date_groups
        date_pattern = bank_properties.date_pattern
        month_pattern = bank_properties.month_pattern
        
        if date_groups.has_year:
            dates = date_column.apply(
                lambda x: self.normalize_date_with_year(x, date_pattern, date_groups, month_pattern)
            )
        else:
            dates = date_column.apply(
                lambda x: self.normalize_date_without_year(x, years, date_pattern, date_groups, month_pattern)
            )
            
        return pd.to_datetime(dates)
        
class AmountNormalizer(ColumnNormalizer):
    @staticmethod
    def normalize_amount_for_single_column(value: str | float, amount_signs: AmountSigns) -> float:
        """
        Normalizes amounts from a single column using sign indicators.
        Determines transaction type and applies appropriate sign based on income/expense indicators.
        """
        income_sign = amount_signs.income.value
        expense_sign = amount_signs.expense.value
        
        amount = 0.0
        
        # Convert value to string to handle both string and float inputs
        value = str(value)
        
        # Handle different sign indicator combinations
        if income_sign and not expense_sign:
            if income_sign in value:
                amount = float(clean_amount(value.replace(income_sign, '')))
            else:
                amount = float(clean_amount(value)) * -1
        
        elif not income_sign and expense_sign:
            if expense_sign in value:
                amount = float(clean_amount(value.replace(expense_sign, ''))) * -1
            else:
                amount = float(clean_amount(value))
        
        elif income_sign and expense_sign:
            if income_sign in value:
                amount = float(clean_amount(value.replace(income_sign, '')))
            elif expense_sign in value:
                amount = float(clean_amount(value.replace(expense_sign, ''))) * -1
                
        return amount
    
    @staticmethod
    def normalize_amount_for_multiple_columns(row: Any, amount_columns: AmountColumns) -> float:
        """
        Normalizes amounts from separate income/expense columns.
        Handles various combinations including balance-only transactions and conflicting amounts.
        """
        amount = 0.0

        income_val = row[amount_columns.income]
        expense_val = row[amount_columns.expense]

        # Determine value presence for each column
        is_income_present = not pd.isna(income_val) and income_val != ''
        is_expense_present = not pd.isna(expense_val) and expense_val != ''
        is_income_effectively_empty = pd.isna(income_val) or income_val == ''
        is_expense_effectively_empty = pd.isna(expense_val) or expense_val == ''

        # Process based on which columns have values
        if is_income_present and is_expense_effectively_empty:
            try:
                amount = float(clean_amount(str(income_val)))
            except ValueError:
                pass
            
        elif is_expense_present and is_income_effectively_empty:
            try:
                amount = float(clean_amount(str(expense_val))) * -1
            except ValueError:
                pass
        
        # Handle balance column when both income/expense are empty
        elif amount_columns.has_balance and is_income_effectively_empty and is_expense_effectively_empty:
            balance_val = row[amount_columns.balance] if amount_columns.balance else None
            is_balance_present = not bool(pd.isna(balance_val)) and balance_val != ''
            if is_balance_present:
                try:
                    amount = float(clean_amount(str(balance_val)))
                except ValueError:
                    pass
        
        # Handle conflicting amounts (both income and expense present)        
        elif is_income_present and is_expense_present:
            try:
                income_amount = float(clean_amount(str(income_val)))
                expense_amount = float(clean_amount(str(expense_val)))
                
                if income_amount > expense_amount:
                    amount = income_amount - expense_amount
                else:
                    amount = expense_amount - income_amount
            except ValueError:
                pass
        
        return amount
    
    def normalize_column(self, reconstructed_table: ReconstructedTable | Any, amount_columns: AmountColumns | Any = None, amount_signs: AmountSigns | Any = None) -> pd.Series:
        """
        Routes amount normalization based on column structure.
        Uses single-column method for unified amounts or multi-column method for separate income/expense.
        """      
        # Route based on input type. We explicitly cast the result of `apply`
        # because pandas' type stubs allow `DataFrame | Series`, but in this
        # usage we always get a `Series`.
        if amount_columns.is_mono_column:
            column = reconstructed_table.df[amount_columns.column]
            return cast(
                pd.Series,
                column.apply(
                    lambda value: self.normalize_amount_for_single_column(
                        value,
                        amount_signs,
                    ),
                ),
            )
        else:
            columns = reconstructed_table.df[amount_columns.all_list]
            return cast(
                pd.Series,
                columns.apply(
                    lambda row: self.normalize_amount_for_multiple_columns(
                        row,
                        amount_columns,
                    ),
                    axis=1,
                ),
            )

class DefaultTableNormalizer(TableNormalizer):
    def normalize_table(self, years: list[int], filename: str) -> TransactionsTable:
        """
        Main method that orchestrates the complete table normalization process.
        Normalizes dates and amounts, adds initial balance, and sorts by date.
        """
        reconstructed_table = self.reconstructed_table
        
        if reconstructed_table.empty:
            raise ValueError("Reconstructed table is empty")
        
        # Type ignored because we know the concrete types in tuple for this implementation
        if len(self.columns_normalizers) >= 2:
             date_normalizer = self.columns_normalizers[0]
             amount_normalizer = self.columns_normalizers[1]
        else:
             # Should warn or raise, but adhering to prior logic, maybe fallback?
             # Assuming standard injection, it should have them.
             # I'll raise error if missing to be type safe
             raise ValueError("Missing normalizers")
        
        normalized_table = TransactionsTable(df=pd.DataFrame())
        
        # Normalize dates
        # Casting to DateNormalizer to satisfy type checker if needed, or rely on duck typing if Python 
        # But here explicit call.
        if isinstance(date_normalizer, DateNormalizer):
             normalized_table.dates = date_normalizer.normalize_column(reconstructed_table, self.bank_properties, years)
        
        # Restrict descriptions to 500 characters. Cast is used to satisfy the
        # type checker because `apply` may be typed as returning a DataFrame or
        # Series, but here it is always a Series.
        normalized_table.descriptions = cast(
            pd.Series,
            reconstructed_table.descriptions.apply(lambda x: x[:500]),
        )
        
        # Normalize amounts
        amount_columns = self.bank_properties.amount_columns
        amount_signs = self.bank_properties.amount_signs
        
        if isinstance(amount_normalizer, AmountNormalizer):
            normalized_table.amounts = amount_normalizer.normalize_column(reconstructed_table, amount_columns, amount_signs) 
        
        # Add transaction type, ensuring the result is treated as a Series for
        # static type checking purposes.
        normalized_table.types = cast(
            pd.Series,
            normalized_table.amounts.apply(
                lambda amount: 'Abono' if amount > 0 else 'Cargo',
            ),
        )
        
        normalized_table.bank_col = self.bank_properties.bank
        normalized_table.statement_type_col = self.bank_properties.statement_type
        normalized_table.filename_col = filename
        
        if self.bank_properties.special_data_filtering is not None:
            normalized_table = self.bank_properties.special_data_filtering.filter_special_data(normalized_table)
        
        return normalized_table
