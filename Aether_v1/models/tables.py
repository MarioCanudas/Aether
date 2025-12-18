import pandas as pd
from pydantic import BaseModel,ConfigDict, field_validator, model_validator
from decimal import Decimal
from typing import Literal, Any, cast
from utils import to_decimal
from .amounts import AmountColumns
from .records import MonthlyResultRecord
from .transactions import Transaction

TABLE_CONFIG = ConfigDict(arbitrary_types_allowed=True) 

class ExtractedWords(BaseModel):
    model_config = TABLE_CONFIG
    
    df: pd.DataFrame
    
    @field_validator('df', mode='before')
    @classmethod
    def _validate_df_structure(cls, v: pd.DataFrame) -> pd.DataFrame:
        if not isinstance(v, pd.DataFrame):
            raise ValueError(f"ExtractedWords dataframe must be a pandas DataFrame, got {type(v).__name__}")
        
        if v.empty:
            v = pd.DataFrame({'page': [], 'text': [], 'x0': [], 'top': [], 'x1': [], 'bottom': []})
        
        if not all(col in v.columns for col in ['page', 'text', 'x0', 'top', 'x1', 'bottom']):
            missing_cols = [col for col in ['page', 'text', 'x0', 'top', 'x1', 'bottom'] if col not in v.columns]
            raise ValueError(f"ExtractedWords dataframe missing required columns: {missing_cols}. Available columns: {list(v.columns)}")
        
        return v
    
    @property
    def num_rows(self) -> int:
        return len(self.df)
    
    @property
    def records(self) -> list[dict[str, Any]]:
        return cast(list[dict[str, Any]], self.df.to_dict(orient='records'))
    
    @property
    def pages(self) -> pd.Series:
        return cast(pd.Series, self.df['page'])
    
    @pages.setter
    def pages(self, pages: pd.Series) -> None:
        if not isinstance(pages, pd.Series):
            raise ValueError("The pages must be a pandas series")
        
        self.df['page'] = pages
    
    @property
    def texts(self) -> pd.Series:
        return cast(pd.Series, self.df['text'])
    
    @texts.setter
    def texts(self, texts: pd.Series) -> None:
        if not isinstance(texts, pd.Series):
            raise ValueError("The texts must be a pandas series")
        
        self.df['text'] = texts
        
    @property
    def x0(self) -> pd.Series:
        return cast(pd.Series, self.df['x0'])
    
    @x0.setter
    def x0(self, x0: pd.Series) -> None:
        if not isinstance(x0, pd.Series):
            raise ValueError("The x0 must be a pandas series")
        
        self.df['x0'] = x0
        
    @property
    def top(self) -> pd.Series:
        return cast(pd.Series, self.df['top'])
    
    @top.setter 
    def top(self, top: pd.Series) -> None:
        if not isinstance(top, pd.Series):
            raise ValueError("The top must be a pandas series")
        
        self.df['top'] = top
        
    @property
    def x1(self) -> pd.Series:
        return cast(pd.Series, self.df['x1'])
    
    @x1.setter
    def x1(self, x1: pd.Series) -> None:
        if not isinstance(x1, pd.Series):
            raise ValueError("The x1 must be a pandas series")
        
        self.df['x1'] = x1
        
    @property
    def bottom(self) -> pd.Series:
        return cast(pd.Series, self.df['bottom'])
    
    @bottom.setter
    def bottom(self, bottom: pd.Series) -> None:
        if not isinstance(bottom, pd.Series):
            raise ValueError("The bottom must be a pandas series")
        
        self.df['bottom'] = bottom
        
    def search_phrase(self, phrase: list[str], type_return: Literal['idx', 'bool'] = 'idx') -> int | bool | None:
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
        
    def filter_table_by_phrases(self, start_phrase: list[str], end_phrase: list[str]) -> 'ExtractedWords':
        start_idx = self.search_phrase(start_phrase, type_return='idx')
        end_idx = self.search_phrase(end_phrase, type_return='idx')
        
        if isinstance(start_idx, int) and isinstance(end_idx, int) and start_idx < end_idx:
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
            raise ValueError(f"GroupedRows dataframe must be a pandas DataFrame, got {type(v).__name__}")
        
        if v.empty:
            v = pd.DataFrame({'row_group': [], 'text': [], 'words': [], 'top': [], 'bottom': [], 'page': []})
        
        if not all(col in v.columns for col in ['row_group', 'text', 'words', 'top', 'bottom', 'page']):
            missing_cols = [col for col in ['row_group', 'text', 'words', 'top', 'bottom', 'page'] if col not in v.columns]
            raise ValueError(f"GroupedRows dataframe missing required columns: {missing_cols}. Available columns: {list(v.columns)}")
        
        return v
    
    @property
    def row_groups(self) -> pd.Series:
        return cast(pd.Series, self.df['row_group'])
    
    @row_groups.setter
    def row_groups(self, row_groups: pd.Series) -> None:
        if not isinstance(row_groups, pd.Series):
            raise ValueError("The row groups must be a pandas series")
        else:
            self.df['row_group'] = row_groups
            
    @property
    def texts(self) -> pd.Series:
        return cast(pd.Series, self.df['text'])
    
    @texts.setter
    def texts(self, texts: pd.Series) -> None:
        if not isinstance(texts, pd.Series):
            raise ValueError("The texts must be a pandas series")
        else:
            self.df['text'] = texts
            
    @property
    def words(self) -> pd.Series:
        return cast(pd.Series, self.df['words'])
    
    @words.setter
    def words(self, words: pd.Series) -> None:
        if not isinstance(words, pd.Series):
            raise ValueError("The words must be a pandas series")
        else:
            self.df['words'] = words
            
    @property
    def top_column(self) -> pd.Series:
        return cast(pd.Series, self.df['top'])
    
    @top_column.setter
    def top_column(self, top_column: pd.Series) -> None:
        if not isinstance(top_column, pd.Series):
            raise ValueError("The top column must be a pandas series")
        else:
            self.df['top'] = top_column
            
    @property
    def bottom_column(self) -> pd.Series:
        return cast(pd.Series, self.df['bottom'])
    
    @bottom_column.setter
    def bottom_column(self, bottom_column: pd.Series) -> None:
        if not isinstance(bottom_column, pd.Series):
            raise ValueError("The bottom column must be a pandas series")
        else:
            self.df['bottom'] = bottom_column
            
    @property
    def pages(self) -> pd.Series:
        return cast(pd.Series, self.df['page'])
    
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
            raise ValueError(f"ReconstructedTable amount_columns must be an AmountColumns object, got {type(v).__name__}")
        
        return v
    
    @field_validator('df', mode='before')
    @classmethod
    def _validate_df_structure(cls, v: pd.DataFrame) -> pd.DataFrame:
        if not isinstance(v, pd.DataFrame):
            raise ValueError(f"ReconstructedTable dataframe must be a pandas DataFrame, got {type(v).__name__}")
        
        if v.empty:
            # For empty dataframes, we'll create a basic structure and let the amount_columns validation handle the rest
            v = pd.DataFrame({'date': [], 'description': []})
            
        # Check for required base columns
        required_base_cols = ['date', 'description']
        if not all(col in v.columns for col in required_base_cols):
            missing_cols = [col for col in required_base_cols if col not in v.columns]
            raise ValueError(f"ReconstructedTable dataframe missing required base columns: {missing_cols}. Available columns: {list(v.columns)}")
        
        return v
    
    @model_validator(mode='after')
    def _validate_amount_columns_after_df(self) -> 'ReconstructedTable':
        if self.amount_columns.is_mono_column:
            if self.amount_columns.income not in self.df.columns:
                raise ValueError(f"ReconstructedTable amount_columns.income '{self.amount_columns.income}' not found in dataframe columns: {list(self.df.columns)}")
        else:
            if self.amount_columns.income not in self.df.columns:
                raise ValueError(f"ReconstructedTable amount_columns.income '{self.amount_columns.income}' not found in dataframe columns: {list(self.df.columns)}")
            if self.amount_columns.expense not in self.df.columns:
                raise ValueError(f"ReconstructedTable amount_columns.expense '{self.amount_columns.expense}' not found in dataframe columns: {list(self.df.columns)}")
            if self.amount_columns.has_balance and self.amount_columns.balance is not None and self.amount_columns.balance not in self.df.columns:
                raise ValueError(f"ReconstructedTable amount_columns.balance '{self.amount_columns.balance}' not found in dataframe columns: {list(self.df.columns)}")

        return self
    
    @property
    def empty(self) -> bool:
        return self.df.empty
    
    @property
    def records(self) -> list[dict[str, Any]]:
        return cast(list[dict[str, Any]], self.df.to_dict(orient='records'))
    
    @property
    def dates(self) -> pd.Series:
        return cast(pd.Series, self.df['date'])
    
    @dates.setter
    def dates(self, dates: pd.Series) -> None:
        if not isinstance(dates, pd.Series):
            raise ValueError("The dates must be a pandas series")
        else:
            self.df['date'] = dates
            
    @property
    def descriptions(self) -> pd.Series:
        return cast(pd.Series, self.df['description'])
    
    @descriptions.setter
    def descriptions(self, descriptions: pd.Series) -> None:
        if not isinstance(descriptions, pd.Series):
            raise ValueError("The descriptions must be a pandas series")
        else:
            self.df['description'] = descriptions
            
    @property
    def amount_column(self) -> pd.Series:
        if self.amount_columns.is_mono_column:
            return cast(pd.Series, self.df[self.amount_columns.income])
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
        return cast(pd.Series, self.df[self.amount_columns.income])
    
    @income_column.setter
    def income_column(self, income_column: pd.Series) -> None:
        if not isinstance(income_column, pd.Series):
            raise ValueError("The income column must be a pandas series")
        else:
            self.df[self.amount_columns.income] = income_column
    
    @property
    def expense_column(self) -> pd.Series:
        return cast(pd.Series, self.df[self.amount_columns.expense])
    
    @expense_column.setter
    def expense_column(self, expense_column: pd.Series) -> None:
        if not isinstance(expense_column, pd.Series):
            raise ValueError("The expense column must be a pandas series")
        else:
            self.df[self.amount_columns.expense] = expense_column
            
    @property
    def balance_column(self) -> pd.Series | None:
        if self.amount_columns.has_balance and self.amount_columns.balance is not None:
            return cast(pd.Series, self.df[self.amount_columns.balance])
        else:
            return None
    
    @balance_column.setter
    def balance_column(self, balance_column: pd.Series) -> None:
        if not isinstance(balance_column, pd.Series):
            raise ValueError("The balance column must be a pandas series")
        elif self.amount_columns.has_balance and self.amount_columns.balance is not None:
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
            v = pd.DataFrame({'date': [], 'description': [], 'amount': [], 'type': [], 'bank': [], 'statement_type': [], 'filename': []})
        
        if not all(col in v.columns for col in ['date', 'description', 'amount', 'type', 'bank', 'statement_type', 'filename']):
            missing_cols = [col for col in ['date', 'description', 'amount', 'type', 'bank', 'statement_type', 'filename'] if col not in v.columns]
            raise ValueError(f"TransactionsTable dataframe missing required columns: {missing_cols}. Available columns: {list(v.columns)}")
        
        return v
    
    @property
    def dates(self) -> pd.Series:
        return cast(pd.Series, self.df['date'])
    
    @dates.setter
    def dates(self, dates: pd.Series) -> None:
        if not isinstance(dates, pd.Series):
            raise ValueError("The dates must be a pandas series")
        
        self.df['date'] = dates
    
    @property
    def descriptions(self) -> pd.Series:
        return cast(pd.Series, self.df['description'])
    
    @descriptions.setter
    def descriptions(self, descriptions: pd.Series) -> None:
        if not isinstance(descriptions, pd.Series):
            raise ValueError("The descriptions must be a pandas series")
        
        self.df['description'] = descriptions
    
    @property
    def amounts(self) -> pd.Series:
        return cast(pd.Series, self.df['amount'])
    
    @amounts.setter
    def amounts(self, amounts: pd.Series) -> None:
        if not isinstance(amounts, pd.Series):
            raise ValueError("The amounts must be a pandas series")
        
        self.df['amount'] = amounts
    
    @property
    def types(self) -> pd.Series:
        return cast(pd.Series, self.df['type'])
    
    @types.setter
    def types(self, types: pd.Series) -> None:
        if not isinstance(types, pd.Series):
            raise ValueError("The types must be a pandas series")
        
        self.df['type'] = types
    
    @property
    def bank_col(self) -> pd.Series:
        return cast(pd.Series, self.df['bank'])
    
    @bank_col.setter
    def bank_col(self, bank: str) -> None:
        if not isinstance(bank, str):
            raise ValueError("The bank must be a string")
        
        self.df['bank'] = bank
    
    @property
    def bank(self) -> str | list[str]:
        return self.df['bank'].iloc[0]
    
    @property
    def statement_type_col(self) -> pd.Series:
        return cast(pd.Series, self.df['statement_type'])
    
    @statement_type_col.setter
    def statement_type_col(self, statement_type: str) -> None:
        if not isinstance(statement_type, str):
            raise ValueError("The statement type must be a string")
        
        self.df['statement_type'] = statement_type
    
    @property
    def statement_type(self) -> str:
        return self.df['statement_type'].iloc[0]
    
    @property
    def filename_col(self) -> pd.Series:
        return cast(pd.Series, self.df['filename'])
    
    @filename_col.setter
    def filename_col(self, filename: str) -> None:
        if not isinstance(filename, str):
            raise ValueError("The filename must be a string")
        
        self.df['filename'] = filename
    
    @property
    def filename(self) -> str:
        return self.df['filename'].iloc[0]
        
    @property
    def transactions(self) -> list[Transaction]:
        return [Transaction(**transaction) for transaction in cast(list[dict[str, Any]], self.df.to_dict(orient='records'))]
    
    def add_transaction(self, transaction: Transaction) -> None:
        record = transaction.model_dump()
        
        record['amount'] = float(record['amount'])
        self.df = pd.concat([self.df, pd.DataFrame([record])], ignore_index=True)
    
    def get_all_incomes(self) -> float:
        return self.df[self.df['type'] == 'Abono']['amount'].sum()
    
    def get_all_expenses(self) -> float:
        return self.df[self.df['type'] == 'Cargo']['amount'].sum()
    
    def get_all_transactions(self) -> float:
        return self.df['amount'].sum()
    
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
            raise ValueError(f"AllTransactionsTable dataframe missing required column 'user_id'. Available columns: {list(v.columns)}")
        
        if 'category_id' not in v.columns:
            v['category_id'] = None
            
        return v
    
    @property
    def banks(self) -> list[str]:
        return self.df['bank'].unique().tolist()
    
    @property
    def files(self) -> list[str]:
        return self.df['filename'].unique().tolist()
    
    @property
    def user_id(self) -> int:
        return self.df['user_id'].iloc[0]
    
    @property
    def category_id(self) -> pd.Series:
        return cast(pd.Series, self.df['category_id'])
    
    @category_id.setter
    def category_id(self, category_id: pd.Series) -> None:
        if not isinstance(category_id, pd.Series):
            raise ValueError("The category id must be a pandas series")
        
        self.df['category_id'] = category_id
        
    def get_transactions_dicts(self) -> list[dict[str, Any]]:   
        return cast(list[dict[str, Any]], self.df.to_dict(orient='records'))
    
class MonthlyResultsTable(BaseModel):
    """Represents a table of monthly results with the following columns:
    - year_month: The year and month of the result
    - user_id: The user id of the result
    """
    model_config = TABLE_CONFIG
    
    df: pd.DataFrame = pd.DataFrame({'year_month': [], 'initial_balance': [], 'total_income': [], 'total_withdrawal': [], 'savings': [], 'user_id': []})
    
    @field_validator('df', mode='before')
    @classmethod
    def _validate_df_structure(cls, v: pd.DataFrame) -> pd.DataFrame:
        if not isinstance(v, pd.DataFrame):
            raise ValueError(f"MonthlyResultsTable dataframe must be a pandas DataFrame, got {type(v).__name__}")
        
        if v.empty:
            v = pd.DataFrame({'year_month': [], 'initial_balance': [], 'total_income': [], 'total_withdrawal': [], 'savings': [], 'user_id': []})
            
        if 'user_id' not in v.columns:
            v['user_id'] = None
        
        if not all(col in v.columns for col in ['year_month', 'initial_balance', 'total_income', 'total_withdrawal', 'savings', 'user_id']):
            missing_cols = [col for col in ['year_month', 'initial_balance', 'total_income', 'total_withdrawal', 'savings', 'user_id'] if col not in v.columns]
            raise ValueError(f"MonthlyResultsTable dataframe missing required columns: {missing_cols}. Available columns: {list(v.columns)}")
        
        return v
    
    @property
    def year_months(self) -> pd.Series:
        return cast(pd.Series, self.df['year_month'])
    
    @year_months.setter
    def year_months(self, year_months: pd.Series) -> None:
        if not isinstance(year_months, pd.Series):
            raise ValueError("The year months must be a pandas series")
        
        self.df['year_month'] = year_months
        
    @property
    def initial_balances(self) -> pd.Series:
        return cast(pd.Series, self.df['initial_balance'])
    
    @initial_balances.setter
    def initial_balances(self, initial_balances: pd.Series) -> None:
        if not isinstance(initial_balances, pd.Series):
            raise ValueError("The initial balances must be a pandas series")
        
        self.df['initial_balance'] = initial_balances
        
    @property
    def total_incomes(self) -> pd.Series:
        return cast(pd.Series, self.df['total_income'])
    
    @total_incomes.setter
    def total_incomes(self, total_incomes: pd.Series) -> None:
        if not isinstance(total_incomes, pd.Series):
            raise ValueError("The total incomes must be a pandas series")
        
        self.df['total_income'] = total_incomes
        
    @property
    def total_withdrawals(self) -> pd.Series:
        return cast(pd.Series, self.df['total_withdrawal'])
    
    @total_withdrawals.setter
    def total_withdrawals(self, total_withdrawals: pd.Series) -> None:
        if not isinstance(total_withdrawals, pd.Series):
            raise ValueError("The total withdrawals must be a pandas series")
        
        self.df['total_withdrawal'] = total_withdrawals
        
    @property
    def savings(self) -> pd.Series:
        return cast(pd.Series, self.df['savings'])
    
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
    def records(self) -> list[MonthlyResultRecord]:
        return cast(list[MonthlyResultRecord], self.df.to_dict(orient='records')) if not self.df.empty else []
    
    async def get_avg_savings_per_month(self) -> Decimal:
        return to_decimal(cast(float, self.savings.mean()))
    
    async def get_avg_income_per_month(self) -> Decimal:
        return to_decimal(cast(float, self.total_incomes.mean()))
    
    async def get_avg_withdrawal_per_month(self) -> Decimal:
        return to_decimal(cast(float, self.total_withdrawals.mean()))
    

class BudgetsTable(BaseModel):
    model_config = TABLE_CONFIG
    
    columns: list[str] = ['id', 'user_id', 'category_id', 'amount', 'name', 'created_at', 'start_date', 'end_date']
    df: pd.DataFrame
    
    @field_validator('df', mode='before')
    @classmethod
    def _validate_df_structure(cls, v: pd.DataFrame) -> pd.DataFrame:
        if not isinstance(v, pd.DataFrame):
            raise ValueError(f"BudgetsTable dataframe must be a pandas DataFrame, got {type(v).__name__}")
            
        if not all(col in v.columns for col in cls.columns):
            missing_cols = [col for col in cls.columns if col not in v.columns]
            raise ValueError(f"BudgetsTable dataframe missing required columns: {missing_cols}. Available columns: {list(v.columns)}")
            
        return v
    
    @property
    def user_id(self) -> int:
        return self.df['user_id'].iloc[0]
    
    @property
    def categories_id(self) -> pd.Series | None:
        if 'category_id' in self.df.columns:
            return cast(pd.Series, self.df['category_id'])
        return None
        
    @property
    def amounts(self) -> pd.Series:
        return cast(pd.Series, self.df['amount'])
    
    @property
    def names(self) -> pd.Series:
        return cast(pd.Series, self.df['name'])
    
    @property
    def created_at(self) -> pd.Series:
        return cast(pd.Series, self.df['created_at'])
    
    @property
    def start_dates(self) -> pd.Series:
        return cast(pd.Series, self.df['start_date'])
    
    @property
    def end_dates(self) -> pd.Series:
        return cast(pd.Series, self.df['end_date'])
