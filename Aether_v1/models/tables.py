import pandas as pd
from pydantic import BaseModel,ConfigDict, field_validator, ValidationError
from typing import List, Literal
from .amounts import AmountColumns
from .records import TransactionRecord, MonthlyResultRecord

TABLE_CONFIG = ConfigDict(arbitrary_types_allowed=True) 

class ExtractedWords(BaseModel):
    model_config = TABLE_CONFIG
    
    df: pd.DataFrame
    
    @field_validator('df', mode='before')
    @classmethod
    def _validate_df_structure(cls, v: pd.DataFrame) -> pd.DataFrame:
        if not isinstance(v, pd.DataFrame):
            raise ValidationError("The dataframe must be a pandas dataframe")
        
        if v.empty:
            v = pd.DataFrame(columns= ['page', 'text', 'x0', 'top', 'x1', 'bottom'])
        
        if not all(col in v.columns for col in ['page', 'text', 'x0', 'top', 'x1', 'bottom']):
            raise ValidationError("The dataframe must have the following columns: page, text, x0, top, x1, bottom")
        
        return v
    
    @property
    def pages(self) -> pd.Series:
        return self.df['page']
    
    @pages.setter
    def pages(self, pages: pd.Series) -> None:
        if not isinstance(pages, pd.Series):
            raise ValueError("The pages must be a pandas series")
        
        self.df['page'] = pages
    
    @property
    def texts(self) -> pd.Series:
        return self.df['text']
    
    @texts.setter
    def texts(self, texts: pd.Series) -> None:
        if not isinstance(texts, pd.Series):
            raise ValueError("The texts must be a pandas series")
        
        self.df['text'] = texts
        
    @property
    def x0(self) -> pd.Series:
        return self.df['x0']
    
    @x0.setter
    def x0(self, x0: pd.Series) -> None:
        if not isinstance(x0, pd.Series):
            raise ValueError("The x0 must be a pandas series")
        
        self.df['x0'] = x0
        
    @property
    def top(self) -> pd.Series:
        return self.df['top']
    
    @top.setter 
    def top(self, top: pd.Series) -> None:
        if not isinstance(top, pd.Series):
            raise ValueError("The top must be a pandas series")
        
        self.df['top'] = top
        
    @property
    def x1(self) -> pd.Series:
        return self.df['x1']
    
    @x1.setter
    def x1(self, x1: pd.Series) -> None:
        if not isinstance(x1, pd.Series):
            raise ValueError("The x1 must be a pandas series")
        
        self.df['x1'] = x1
        
    @property
    def bottom(self) -> pd.Series:
        return self.df['bottom']
    
    @bottom.setter
    def bottom(self, bottom: pd.Series) -> None:
        if not isinstance(bottom, pd.Series):
            raise ValueError("The bottom must be a pandas series")
        
        self.df['bottom'] = bottom
        
    def search_phrase(self, phrase: List[str], type_return: Literal['idx', 'bool'] = 'idx') -> int | bool | None:
        texts = self.texts
        
        for i in range(len(self.df) - len(phrase)):
            # Extract a slice of text from the current position with the same length as the phrase
            # Convert all text to lowercase for case-insensitive comparison
            current_slice = list(texts.iloc[i : i + len(phrase)].str.lower())
            
            # Check if the current slice exactly matches the target phrase
            if current_slice == phrase:
                # Return based on the requested return type
                if type_return == 'idx':
                    return i  # Return the starting index where the phrase was found
                elif type_return == 'bool':
                    return True  # Return True indicating the phrase was found

        # If no match was found, return appropriate default value based on return type
        if type_return == 'idx':
            return None  # Return None when no index is found
        elif type_return == 'bool':
            return False  # Return False when phrase is not found
        
    def filter_table_by_phrases(self, start_phrase: List[str], end_phrase: List[str]) -> 'ExtractedWords':
        start_idx = self.search_phrase(start_phrase, type_return='idx')
        end_idx = self.search_phrase(end_phrase, type_return='idx')
        
        if start_idx and end_idx and start_idx < end_idx:
            return ExtractedWords(df= self.df.iloc[start_idx : end_idx].sort_values(by=["page", "top"]).reset_index(drop=True))
        else:
            raise ValueError(f"The start_idx: {start_idx} and end_idx: {end_idx} are not valid")
        
        
class GroupedRows(BaseModel):
    model_config = TABLE_CONFIG
    
    df: pd.DataFrame
    
    @field_validator('df', mode='before')
    @classmethod
    def _validate_df_structure(cls, v: pd.DataFrame) -> pd.DataFrame:
        if not isinstance(v, pd.DataFrame):
            raise ValidationError("The dataframe must be a pandas dataframe")
        
        if v.empty:
            v = pd.DataFrame(columns= ['row_group', 'text', 'words', 'top', 'bottom', 'page'])
        
        if not all(col in v.columns for col in ['row_group', 'text', 'words', 'top', 'bottom', 'page']):
            raise ValidationError("The dataframe must have the following columns: row_group, text, words, top, bottom, page")
        
        return v
    
    @property
    def row_groups(self) -> pd.Series:
        return self.df['row_group']
    
    @row_groups.setter
    def row_groups(self, row_groups: pd.Series) -> None:
        if not isinstance(row_groups, pd.Series):
            raise ValueError("The row groups must be a pandas series")
        else:
            self.df['row_group'] = row_groups
            
    @property
    def texts(self) -> pd.Series:
        return self.df['text']
    
    @texts.setter
    def texts(self, texts: pd.Series) -> None:
        if not isinstance(texts, pd.Series):
            raise ValueError("The texts must be a pandas series")
        else:
            self.df['text'] = texts
            
    @property
    def words(self) -> pd.Series:
        return self.df['words']
    
    @words.setter
    def words(self, words: pd.Series) -> None:
        if not isinstance(words, pd.Series):
            raise ValueError("The words must be a pandas series")
        else:
            self.df['words'] = words
            
    @property
    def top_column(self) -> pd.Series:
        return self.df['top']
    
    @top_column.setter
    def top_column(self, top_column: pd.Series) -> None:
        if not isinstance(top_column, pd.Series):
            raise ValueError("The top column must be a pandas series")
        else:
            self.df['top'] = top_column
            
    @property
    def bottom_column(self) -> pd.Series:
        return self.df['bottom']
    
    @bottom_column.setter
    def bottom_column(self, bottom_column: pd.Series) -> None:
        if not isinstance(bottom_column, pd.Series):
            raise ValueError("The bottom column must be a pandas series")
        else:
            self.df['bottom'] = bottom_column
            
    @property
    def pages(self) -> pd.Series:
        return self.df['page']
    
    @pages.setter
    def pages(self, pages: pd.Series) -> None:
        if not isinstance(pages, pd.Series):
            raise ValueError("The pages must be a pandas series")
        else:
            self.df['page'] = pages
            
    
class ReconstructedTable(BaseModel):
    model_config = TABLE_CONFIG
    
    df: pd.DataFrame
    amount_columns: AmountColumns
    
    @field_validator('amount_columns', mode='before')
    @classmethod
    def _validate_amount_columns(cls, v: AmountColumns) -> AmountColumns:
        if not isinstance(v, AmountColumns):
            raise ValidationError("The amount columns must be an AmountColumns object")
        
        return v
    
    @field_validator('df', mode='before')
    @classmethod
    def _validate_df_structure(cls, v: pd.DataFrame) -> pd.DataFrame:
        if not isinstance(v, pd.DataFrame):
            raise ValidationError("The dataframe must be a pandas dataframe")
        
        if v.empty:
            v = pd.DataFrame(columns= ['date', 'description'] + cls.amount_columns.all_list)
            
        if not all(col in v.columns for col in ['date', 'description'] + cls.amount_columns.all_list):
            raise ValidationError("The dataframe must have the following columns: date, description, " + ", ".join(cls.amount_columns.all_list))
        
        return v
    
    @property
    def dates(self) -> pd.Series:
        return self.df['date']
    
    @dates.setter
    def dates(self, dates: pd.Series) -> None:
        if not isinstance(dates, pd.Series):
            raise ValueError("The dates must be a pandas series")
        else:
            self.df['date'] = dates
            
    @property
    def descriptions(self) -> pd.Series:
        return self.df['description']
    
    @descriptions.setter
    def descriptions(self, descriptions: pd.Series) -> None:
        if not isinstance(descriptions, pd.Series):
            raise ValueError("The descriptions must be a pandas series")
        else:
            self.df['description'] = descriptions
            
    @property
    def amount_column(self) -> pd.Series:
        if self.amount_columns.is_mono_column:
            return self.df[self.amount_columns.income]
        else:
            raise ValueError("The amount column is not defined")
        
    @amount_column.setter
    def amount_column(self, amount_column: pd.Series) -> None:
        if not isinstance(amount_column, pd.Series):
            raise ValueError("The amount column must be a pandas series")
        elif self.amount_columns.is_mono_column:
            self.df[self.amount_columns.income] = amount_column
        else:
            raise ValueError("The amount column is not defined")
            
    @property
    def income_column(self) -> pd.Series:
        return self.df[self.amount_columns.income]
    
    @income_column.setter
    def income_column(self, income_column: pd.Series) -> None:
        if not isinstance(income_column, pd.Series):
            raise ValueError("The income column must be a pandas series")
        else:
            self.df[self.amount_columns.income] = income_column
    
    @property
    def expense_column(self) -> pd.Series:
        return self.df[self.amount_columns.expense]
    
    @expense_column.setter
    def expense_column(self, expense_column: pd.Series) -> None:
        if not isinstance(expense_column, pd.Series):
            raise ValueError("The expense column must be a pandas series")
        else:
            self.df[self.amount_columns.expense] = expense_column
            
    @property
    def balance_column(self) -> pd.Series | None:
        if self.amount_columns.has_balance:
            return self.df[self.amount_columns.balance]
        else:
            return None
    
    @balance_column.setter
    def balance_column(self, balance_column: pd.Series) -> None:
        if not isinstance(balance_column, pd.Series):
            raise ValueError("The balance column must be a pandas series")
        elif self.amount_columns.has_balance:
            self.df[self.amount_columns.balance] = balance_column
        else:
            raise ValueError("The balance column is not defined")
        
    
class TransactionsTable(BaseModel):
    """Represents a table of transactions per individual statement with the following columns:
    - date: The date of the transaction
    - description: The description of the transaction
    - amount: The amount of the transaction
    - type: The type of the transaction
    - bank: The bank of the transaction
    """
    model_config = TABLE_CONFIG
    
    df: pd.DataFrame
    
    @field_validator('df', mode='before')
    @classmethod
    def _validate_df_structure(cls, v: pd.DataFrame) -> pd.DataFrame:
        if v.empty:
            v = pd.DataFrame(columns= ['date', 'description', 'amount', 'type', 'bank', 'statement_type', 'filename'])
        
        if not all(col in v.columns for col in ['date', 'description', 'amount', 'type', 'bank', 'statement_type', 'filename']):
            raise ValidationError("The dataframe must have the following columns: date, description, amount, type, bank, statement_type, filename")
        
        return v
    
    @property
    def dates(self) -> pd.Series:
        return self.df['date']
    
    @dates.setter
    def dates(self, dates: pd.Series) -> None:
        if not isinstance(dates, pd.Series):
            raise ValueError("The dates must be a pandas series")
        
        self.df['date'] = dates
    
    @property
    def descriptions(self) -> pd.Series:
        return self.df['description']
    
    @descriptions.setter
    def descriptions(self, descriptions: pd.Series) -> None:
        if not isinstance(descriptions, pd.Series):
            raise ValueError("The descriptions must be a pandas series")
        
        self.df['description'] = descriptions
    
    @property
    def amounts(self) -> pd.Series:
        return self.df['amount']
    
    @amounts.setter
    def amounts(self, amounts: pd.Series) -> None:
        if not isinstance(amounts, pd.Series):
            raise ValueError("The amounts must be a pandas series")
        
        self.df['amount'] = amounts
    
    @property
    def types(self) -> pd.Series:
        return self.df['type']
    
    @types.setter
    def types(self, types: pd.Series) -> None:
        if not isinstance(types, pd.Series):
            raise ValueError("The types must be a pandas series")
        
        self.df['type'] = types
    
    @property
    def bank_col(self) -> pd.Series:
        return self.df['bank']
    
    @bank_col.setter
    def bank_col(self, bank_col: pd.Series) -> None:
        if not isinstance(bank_col, pd.Series):
            raise ValueError("The bank column must be a pandas series")
        
        self.df['bank'] = bank_col
    
    @property
    def bank(self) -> str | List[str]:
        return self.df['bank'].iloc[0]
    
    @property
    def statement_type_col(self) -> pd.Series:
        return self.df['statement_type']
    
    @statement_type_col.setter
    def statement_type_col(self, statement_type_col: pd.Series) -> None:
        if not isinstance(statement_type_col, pd.Series):
            raise ValueError("The statement type column must be a pandas series")
        
        self.df['statement_type'] = statement_type_col
    
    @property
    def statement_type(self) -> str:
        return self.df['statement_type'].iloc[0]
    
    @property
    def filename_col(self) -> pd.Series:
        return self.df['filename']
    
    @filename_col.setter
    def filename_col(self, filename_col: pd.Series) -> None:
        if not isinstance(filename_col, pd.Series):
            raise ValueError("The filename column must be a pandas series")
        
        self.df['filename'] = filename_col
    
    @property
    def filename(self) -> str:
        return self.df['filename'].iloc[0]
    
    def add_row(self, row: TransactionRecord) -> None:
        self.df = pd.concat([self.df, pd.DataFrame([row])], ignore_index=True)
        
    @property
    def records(self) -> List[TransactionRecord]:
        return self.df.to_dict(orient='records')
    
    def get_all_incomes(self) -> float:
        return self.df[self.df.types == 'Abono']['amount'].sum()
    
    def get_all_expenses(self) -> float:
        return self.df[self.df.types == 'Cargo']['amount'].sum()
    
    def get_all_transactions(self) -> float:
        return self.df['amount'].sum()
    
    @property
    def records(self) -> List[TransactionRecord]:
        return self.df.to_dict(orient='records')
    
class AllTransactionsTable(TransactionsTable):
    """Represents a table of all transactions from all statements with the following columns:
    - date: The date of the transaction
    - description: The description of the transaction
    - amount: The amount of the transaction
    - type: The type of the transaction
    - bank: The bank of the transaction
    - user_id: The user id of the transaction
    """
    @field_validator('df', mode='before')
    @classmethod
    def _validate_df_structure(cls, v: pd.DataFrame) -> pd.DataFrame:
        v = super()._validate_df_structure(v)
        
        if 'user_id' not in v.columns:
            raise ValidationError("The TransactionsTable must have the following columns: user_id")
            
        return v
    
    @property
    def banks(self) -> List[str]:
        return self.df['bank'].unique().tolist()
    
    @property
    def files(self) -> List[str]:
        return self.df['filename'].unique().tolist()
    
    @property
    def user_id(self) -> int:
        return self.df['user_id'].iloc[0]
    
class MonthlyResultsTable(BaseModel):
    """Represents a table of monthly results with the following columns:
    - year_month: The year and month of the result
    - user_id: The user id of the result
    """
    model_config = TABLE_CONFIG
    
    df: pd.DataFrame = pd.DataFrame(columns= ['year_month', 'initial_balance', 'total_income', 'total_withdrawal', 'savings', 'user_id'])
    
    @field_validator('df', mode='before')
    @classmethod
    def _validate_df_structure(cls, v: pd.DataFrame) -> pd.DataFrame:
        if not isinstance(v, pd.DataFrame):
            raise ValidationError("The dataframe must be a pandas dataframe")
        
        if not all(col in v.columns for col in ['year_month', 'initial_balance', 'total_income', 'total_withdrawal', 'savings', 'user_id']):
            raise ValidationError("The dataframe must have the following columns: year_month, initial_balance, total_income, total_withdrawal, savings, user_id")
        
        return v
    
    @property
    def year_months(self) -> pd.Series:
        return self.df['year_month']
    
    @year_months.setter
    def year_months(self, year_months: pd.Series) -> None:
        if not isinstance(year_months, pd.Series):
            raise ValueError("The year months must be a pandas series")
        
        self.df['year_month'] = year_months
        
    @property
    def initial_balances(self) -> pd.Series:
        return self.df['initial_balance']
    
    @initial_balances.setter
    def initial_balances(self, initial_balances: pd.Series) -> None:
        if not isinstance(initial_balances, pd.Series):
            raise ValueError("The initial balances must be a pandas series")
        
        self.df['initial_balance'] = initial_balances
        
    @property
    def total_incomes(self) -> pd.Series:
        return self.df['total_income']
    
    @total_incomes.setter
    def total_incomes(self, total_incomes: pd.Series) -> None:
        if not isinstance(total_incomes, pd.Series):
            raise ValueError("The total incomes must be a pandas series")
        
        self.df['total_income'] = total_incomes
        
    @property
    def total_withdrawals(self) -> pd.Series:
        return self.df['total_withdrawal']
    
    @total_withdrawals.setter
    def total_withdrawals(self, total_withdrawals: pd.Series) -> None:
        if not isinstance(total_withdrawals, pd.Series):
            raise ValueError("The total withdrawals must be a pandas series")
        
        self.df['total_withdrawal'] = total_withdrawals
        
    @property
    def savings(self) -> pd.Series:
        return self.df['savings']
    
    @savings.setter
    def savings(self, savings: pd.Series) -> None:
        if not isinstance(savings, pd.Series):
            raise ValueError("The savings must be a pandas series")
        
        self.df['savings'] = savings
        
    @property
    def user_id(self) -> int:
        return self.df['user_id'].iloc[0]
    
    @user_id.setter
    def user_id(self, user_id: int) -> None:
        if not isinstance(user_id, int):
            raise ValueError("The user id must be an integer")
        
        self.df['user_id'] = user_id
        
    @property
    def records(self) -> List[MonthlyResultRecord]:
        return self.df.to_dict(orient='records') if not self.df.empty else []	