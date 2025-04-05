from core import TableNormalizer
import re
import pandas as pd
from functools import cached_property
from typing import List, Tuple

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
    
    def normalize_date_with_year(self, date: str, date_pattern: str, groups_date: Tuple[int], month_pattern: dict) -> str:
        year_group, month_group, day_group = groups_date
        
        date_match = re.match(date_pattern, date)
        
        if date_match:
            year = date_match.group(year_group)
            month = date_match.group(month_group)
            day = date_match.group(day_group)
            
            month = month_pattern[month]
            
            return f"{year}-{month}-{day}" if len(year) == 4 else f"20{year}-{month}-{day}"
        else:
            return ""
        
    def normalize_date_without_year(self, date: str, date_pattern: str, groups_date: Tuple[int], month_pattern: dict) -> str:
        years = self.get_year()
        _, month_group, day_group = groups_date
        
        date_match = re.match(date_pattern, date)

        if len(years) == 1:
            year = years[0]
            
            if date_match:
                month = date_match.group(month_group)
                day = date_match.group(day_group)
                
                month = month_pattern[month]
                
                return f"{year}-{month}-{day}"
            else:
                return ""
        elif len(years) == 2:
            year1 = years[0]
            year2 = years[1]
            
            if date_match:
                month = date_match.group(month_group)
                day = date_match.group(day_group)
                
                month = month_pattern[month]
                
                if int(month) <= 12:
                    return f"{year1}-{month}-{day}"
                else:
                    return f"{year2}-{month}-{day}"
            else:
                return ""
            
    def normalize_dates(self, date_column: pd.Series) -> pd.Series:
        date_pattern = self.statement_properties['date_pattern']
        groups_date = self.statement_properties['date_groups']
        month_pattern = self.statement_properties['month_pattern']
        
        if groups_date[0]:
            return date_column.apply(
                lambda x: self.normalize_date_with_year(x, date_pattern, groups_date, month_pattern)
            )
        else:
            return date_column.apply(
                lambda x: self.normalize_date_without_year(x, date_pattern, groups_date, month_pattern)
            )
    
    def income_idxs(self) -> List[int]:
        df_table = self.df_table.copy()
        
        income_condition = self.statement_properties['income_condition']
        description_column = self.statement_properties['description_column']
        income_idxs = []
        
        for i, row in df_table.iterrows():
            if income_condition in row[description_column].lower():
                income_idxs.append(i)
                
        return income_idxs
        
    def normalize_amounts(self, amount_columns: pd.Series | pd.DataFrame) -> pd.Series:
        column_names = amount_columns.columns.tolist()
        
        if len(column_names) == 1:
            def normalize_amount(amount: str, i: int) -> float:
                income_idxs = self.income_idxs()

                try:
                    if i in income_idxs:
                        return float(amount)
                    else:
                        return -float(amount)
                except ValueError:
                    return 0.0
        else:
            def normalize_amount(row: str) -> float:
                income_column = self.statement_properties['income_column']
                expense_column = self.statement_properties['expense_column']
                
                if not pd.isna(row[income_column]) and row[expense_column] == '':
                    try:
                        return float(row[income_column].replace(',', ''))
                    except ValueError:
                        return 0.0
                    
                elif not pd.isna(row[expense_column]) and row[income_column] == '':
                    try:
                        return float(row[expense_column].replace(',', '')) * -1
                    except ValueError:
                        return 0.0
                else:
                    return 0.0

        return amount_columns.apply(normalize_amount, axis=1)
    
    def normalize_table(self) -> pd.DataFrame:
        df_table = self.df_table.copy()
        df_normalized = pd.DataFrame()
        
        date_column = self.statement_properties['date_column']
        description_column = self.statement_properties['description_column']
        amount_column = self.statement_properties['amount_column']
        
        df_normalized['Date'] = self.normalize_dates(df_table[date_column])
        df_normalized['Description'] = df_table[description_column]
        df_normalized['Amount'] = self.normalize_amounts(df_table[amount_column])
        
        df_normalized['Type'] = df_normalized['Amount'].apply(
            lambda x: 'Abono' if x > 0 else 'Cargo' if x < 0 else 'Saldo'
        )
        df_normalized['Date'] = pd.to_datetime(df_normalized['Date'])
        
        return df_normalized