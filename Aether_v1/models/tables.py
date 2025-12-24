import asyncio
from typing import Any, Literal

import pandas as pd
from pydantic import BaseModel, ConfigDict, field_validator

from .amounts import AmountColumns
from .transactions import Transaction
from .validators.generics_validator import GenericsValidator
from .validators.transactions_validator import TransactionValidator

generics_validator = GenericsValidator()
transactions_validator = TransactionValidator()

TABLE_CONFIG: ConfigDict = ConfigDict(arbitrary_types_allowed=True)


class ExtractedWords(BaseModel):
    model_config = TABLE_CONFIG

    df: pd.DataFrame

    @field_validator("df", mode="before")
    @classmethod
    def _validate_df_structure(cls, v: pd.DataFrame) -> pd.DataFrame:
        v = generics_validator.validate_dataframe(v)

        if v.empty:
            v = pd.DataFrame({"page": [], "text": [], "x0": [], "top": [], "x1": [], "bottom": []})

        if not all(col in v.columns for col in ["page", "text", "x0", "top", "x1", "bottom"]):
            missing_cols = [
                col for col in ["page", "text", "x0", "top", "x1", "bottom"] if col not in v.columns
            ]
            raise ValueError(
                f"ExtractedWords dataframe missing required columns: {missing_cols}. Available columns: {list(v.columns)}"
            )

        return v

    @property
    def num_rows(self) -> int:
        return len(self.df)

    @property
    def records(self) -> list[dict[str, Any]]:
        records = self.df.to_dict(orient="records")
        records = asyncio.run(generics_validator.validate_list_of_dicts(records))

        return records

    @property
    def pages(self) -> pd.Series:
        col = self.df["page"]
        col = generics_validator.validate_series(col)

        return col

    @pages.setter
    def pages(self, pages: pd.Series) -> None:
        self.df["page"] = pages

    @property
    def texts(self) -> pd.Series:
        col = self.df["text"]
        col = generics_validator.validate_series(col)

        return col

    @texts.setter
    def texts(self, texts: pd.Series) -> None:
        self.df["text"] = texts

    @property
    def x0(self) -> pd.Series:
        col = self.df["x0"]
        col = generics_validator.validate_series(col)

        return col

    @x0.setter
    def x0(self, x0: pd.Series) -> None:
        self.df["x0"] = x0

    @property
    def top(self) -> pd.Series:
        col = self.df["top"]
        col = generics_validator.validate_series(col)

        return col

    @top.setter
    def top(self, top: pd.Series) -> None:
        self.df["top"] = top

    @property
    def x1(self) -> pd.Series:
        col = self.df["x1"]
        col = generics_validator.validate_series(col)

        return col

    @x1.setter
    def x1(self, x1: pd.Series) -> None:
        self.df["x1"] = x1

    @property
    def bottom(self) -> pd.Series:
        col = self.df["bottom"]
        col = generics_validator.validate_series(col)

        return col

    @bottom.setter
    def bottom(self, bottom: pd.Series) -> None:
        self.df["bottom"] = bottom

    def search_phrase(
        self, phrase: list[str], type_return: Literal["idx", "bool"] = "idx"
    ) -> int | bool | None:
        texts = self.texts

        for i in range(len(self.df) - len(phrase)):
            # Extract a slice of text from the current position with the same length as the phrase
            # Convert all text to lowercase for case-insensitive comparison
            current_slice = list(texts.iloc[i : i + len(phrase)].str.lower())

            # Check if the current slice exactly matches the target phrase
            if current_slice == phrase:
                # Return based on the requested return type
                if type_return == "idx":
                    return i  # Return the starting index where the phrase was found
                elif type_return == "bool":
                    return True  # Return True indicating the phrase was found

        # If no match was found, return appropriate default value based on return type
        if type_return == "idx":
            return None  # Return None when no index is found
        elif type_return == "bool":
            return False  # Return False when phrase is not found

    def filter_table_by_phrases(
        self, start_phrase: list[str], end_phrase: list[str]
    ) -> "ExtractedWords":
        start_idx = self.search_phrase(start_phrase, type_return="idx")
        end_idx = self.search_phrase(end_phrase, type_return="idx")

        if isinstance(start_idx, int) and isinstance(end_idx, int) and start_idx < end_idx:
            return ExtractedWords(
                df=self.df.iloc[start_idx:end_idx]
                .sort_values(by=["page", "top"])
                .reset_index(drop=True)
            )
        else:
            raise ValueError(f"The start_idx: {start_idx} and end_idx: {end_idx} are not valid")


class GroupedRows(BaseModel):
    model_config = TABLE_CONFIG

    df: pd.DataFrame

    @field_validator("df", mode="before")
    @classmethod
    def _validate_df_structure(cls, v: pd.DataFrame) -> pd.DataFrame:
        v = generics_validator.validate_dataframe(v)

        if v.empty:
            v = pd.DataFrame(
                {
                    "row_group": [],
                    "text": [],
                    "words": [],
                    "top_column": [],
                    "bottom_column": [],
                    "page": [],
                }
            )

        required_cols = ["row_group", "text", "words", "top_column", "bottom_column", "page"]
        if not all(col in v.columns for col in required_cols):
            missing_cols = [col for col in required_cols if col not in v.columns]
            raise ValueError(
                f"GroupedRows dataframe missing required columns: {missing_cols}. Available columns: {list(v.columns)}"
            )

        return v

    @property
    def row_groups(self) -> pd.Series:
        return generics_validator.validate_series(self.df["row_group"])

    @row_groups.setter
    def row_groups(self, row_groups: pd.Series) -> None:
        self.df["row_group"] = row_groups

    @property
    def texts(self) -> pd.Series:
        return generics_validator.validate_series(self.df["text"])

    @texts.setter
    def texts(self, texts: pd.Series) -> None:
        self.df["text"] = texts

    @property
    def words(self) -> pd.Series:
        return generics_validator.validate_series(self.df["words"])

    @words.setter
    def words(self, words: pd.Series) -> None:
        self.df["words"] = words

    @property
    def top_column(self) -> pd.Series:
        return generics_validator.validate_series(self.df["top_column"])

    @top_column.setter
    def top_column(self, top_column: pd.Series) -> None:
        self.df["top_column"] = top_column

    @property
    def bottom_column(self) -> pd.Series:
        return generics_validator.validate_series(self.df["bottom_column"])

    @bottom_column.setter
    def bottom_column(self, bottom_column: pd.Series) -> None:
        self.df["bottom_column"] = bottom_column

    @property
    def pages(self) -> pd.Series:
        return generics_validator.validate_series(self.df["page"])

    @pages.setter
    def pages(self, pages: pd.Series) -> None:
        self.df["page"] = pages


class ReconstructedTable(BaseModel):
    model_config = TABLE_CONFIG

    df: pd.DataFrame
    amount_columns: AmountColumns

    @field_validator("amount_columns")
    @classmethod
    def _validate_amount_columns(cls, v: list[str]) -> list[str]:
        if not all(isinstance(item, str) for item in v):
            raise ValueError("All items in amount_columns must be strings")
        return v

    @field_validator("df", mode="before")
    @classmethod
    def _validate_df_structure(cls, v: pd.DataFrame) -> pd.DataFrame:
        v = generics_validator.validate_dataframe(v)

        if v.empty:
            v = pd.DataFrame({"date": [], "description": [], "amount": []})

        required_cols = ["date", "description", "amount"]
        if not all(col in v.columns for col in required_cols):
            missing_cols = [col for col in required_cols if col not in v.columns]
            raise ValueError(
                f"ReconstructedTable dataframe missing required columns: {missing_cols}. Available columns: {list(v.columns)}"
            )

        return v

    def _validate_amount_columns_after_df(self) -> None:
        for col_name in self.amount_columns:
            if col_name not in self.df.columns:
                raise ValueError(f"Column '{col_name}' not found in the DataFrame.")
            if not pd.api.types.is_numeric_dtype(self.df[col_name]):
                # Attempt to convert to numeric, coercing errors
                self.df[col_name] = pd.to_numeric(self.df[col_name], errors="coerce")
                # Check if all values are now numeric (non-numeric are converted to NaN)
                if bool(self.df[col_name].isnull().any()):
                    raise ValueError(
                        f"Column '{col_name}' contains non-numeric values that could not be converted."
                    )
            # Fill NaN values with 0, as they are valid for amount columns
            self.df[col_name] = self.df[col_name].fillna(0)

    @property
    def empty(self) -> bool:
        return self.df.empty

    @property
    def records(self) -> list[dict[str, Any]]:
        return self.df.to_dict(orient="records")

    @property
    def dates(self) -> pd.Series:
        return generics_validator.validate_series(self.df["date"])

    @dates.setter
    def dates(self, dates: pd.Series) -> None:
        self.df["date"] = dates

    @property
    def descriptions(self) -> pd.Series:
        return generics_validator.validate_series(self.df["description"])

    @descriptions.setter
    def descriptions(self, descriptions: pd.Series) -> None:
        self.df["description"] = descriptions

    @property
    def amount_column(self) -> pd.Series | None:
        if "amount" in self.df.columns:
            return generics_validator.validate_series(self.df["amount"])
        return None

    @amount_column.setter
    def amount_column(self, amount: pd.Series) -> None:
        self.df["amount"] = amount

    @property
    def income_column(self) -> pd.Series:
        return generics_validator.validate_series(self.df["income"])

    @income_column.setter
    def income_column(self, income: pd.Series) -> None:
        self.df["income"] = income

    @property
    def expense_column(self) -> pd.Series:
        return generics_validator.validate_series(self.df["expense"])

    @expense_column.setter
    def expense_column(self, expense: pd.Series) -> None:
        self.df["expense"] = expense

    @property
    def balance_column(self) -> pd.Series | None:
        if "balance" in self.df.columns:
            return generics_validator.validate_series(self.df["balance"])
        return None

    @balance_column.setter
    def balance_column(self, balance: pd.Series) -> None:
        self.df["balance"] = balance


class TransactionsTable(BaseModel):
    """
    Represents a table of transactions, typically from a single financial statement.
    This class is initialized with a pandas DataFrame and provides methods to access
    and manipulate the transaction data.

    Attributes:
        df (pd.DataFrame): The DataFrame holding the transaction data.
                           Expected columns are 'date', 'description', 'amount', 'type',
                           'bank', 'statement_type', and 'filename'.
    """

    model_config = TABLE_CONFIG

    df: pd.DataFrame

    @field_validator("df", mode="before")
    @classmethod
    def _validate_df_structure(cls, v: Any) -> pd.DataFrame:
        """
        Validates the structure of the DataFrame upon initialization.
        Ensures that the input is a DataFrame and contains all the required columns.
        If the DataFrame is empty, it initializes it with the required columns.
        """
        v = generics_validator.validate_dataframe(v)

        if v.empty:
            return pd.DataFrame(
                {
                    "date": [],
                    "description": [],
                    "amount": [],
                    "type": [],
                    "bank": [],
                    "statement_type": [],
                    "filename": [],
                }
            )

        required_cols = [
            "date",
            "description",
            "amount",
            "type",
            "bank",
            "statement_type",
            "filename",
        ]
        if not all(col in v.columns for col in required_cols):
            missing_cols = [col for col in required_cols if col not in v.columns]
            raise ValueError(
                f"TransactionsTable dataframe missing required columns: {missing_cols}. Available columns: {list(v.columns)}"
            )

        return v

    @property
    def dates(self) -> pd.Series:
        return generics_validator.validate_series(self.df["date"])

    @dates.setter
    def dates(self, dates: pd.Series) -> None:
        self.df["date"] = dates

    @property
    def descriptions(self) -> pd.Series:
        return generics_validator.validate_series(self.df["description"])

    @descriptions.setter
    def descriptions(self, descriptions: pd.Series) -> None:
        self.df["description"] = descriptions

    @property
    def amounts(self) -> pd.Series:
        return generics_validator.validate_series(self.df["amount"])

    @amounts.setter
    def amounts(self, amounts: pd.Series) -> None:
        self.df["amount"] = amounts

    @property
    def types(self) -> pd.Series:
        return generics_validator.validate_series(self.df["type"])

    @types.setter
    def types(self, types: pd.Series) -> None:
        self.df["type"] = types

    @property
    def bank_col(self) -> pd.Series:
        return generics_validator.validate_series(self.df["bank"])

    @bank_col.setter
    def bank_col(self, value: Any) -> None:
        self.df["bank"] = value

    @property
    def bank(self) -> str:
        return self.df["bank"].iloc[0]

    @property
    def statement_type_col(self) -> pd.Series:
        return generics_validator.validate_series(self.df["statement_type"])

    @statement_type_col.setter
    def statement_type_col(self, statement_type: Any) -> None:
        self.df["statement_type"] = statement_type

    @property
    def statement_type(self) -> str:
        return self.df["statement_type"].iloc[0]

    @property
    def filename_col(self) -> pd.Series:
        return generics_validator.validate_series(self.df["filename"])

    @filename_col.setter
    def filename_col(self, value: Any) -> None:
        self.df["filename"] = value

    @property
    def filename(self) -> str:
        return self.df["filename"].iloc[0]

    @property
    def transactions(self) -> list[Transaction]:
        transactions_list = [Transaction(**row) for row in self.df.to_dict(orient="records")]
        return transactions_validator.validate_list_transactions(transactions_list)

    def add_transaction(self, transaction: Transaction) -> None:
        new_row = pd.DataFrame([transaction.model_dump()])
        self.df = pd.concat([self.df, new_row], ignore_index=True)

    def get_all_incomes(self) -> float:
        return self.df[self.df["type"] == "Abono"]["amount"].sum()

    def get_all_expenses(self) -> float:
        return self.df[self.df["type"] == "Cargo"]["amount"].sum()

    def get_all_transactions(self) -> float:
        return self.df["amount"].sum()


class AllTransactionsTable(TransactionsTable):
    """
    Represents a consolidated table of all transactions from multiple sources or statements.
    This class extends `TransactionsTable` and is designed to handle a larger, more diverse
    set of transaction data.

    Attributes:
        df (pd.DataFrame): The DataFrame holding all transaction data.
                           In addition to the columns from `TransactionsTable`, it may include
                           'user_id' and 'category_id' for more detailed analysis.
    """

    model_config = TABLE_CONFIG

    @field_validator("df", mode="before")
    @classmethod
    def _validate_df_structure(cls, v: Any) -> pd.DataFrame:
        """
        Validates the structure of the DataFrame for all transactions.
        Ensures it's a DataFrame and initializes it with an expanded set of columns
        if it's empty. This includes columns for user and category identification.
        """
        v = generics_validator.validate_dataframe(v)

        if v.empty:
            return pd.DataFrame(
                {
                    "date": [],
                    "description": [],
                    "amount": [],
                    "type": [],
                    "bank": [],
                    "statement_type": [],
                    "filename": [],
                    "user_id": [],
                    "category_id": [],
                }
            )

        if "category_id" not in v.columns:
            v["category_id"] = None

        return v

    @property
    def banks(self) -> list[str]:
        return generics_validator.validate_list_str(self.df["bank"].unique().tolist())

    @property
    def files(self) -> list[str]:
        return generics_validator.validate_list_str(self.df["filename"].unique().tolist())

    @property
    def user_id(self) -> int:
        return self.df["user_id"].iloc[0]

    @property
    def category_id(self) -> pd.Series:
        return generics_validator.validate_series(self.df["category_id"])

    @category_id.setter
    def category_id(self, category_id: pd.Series) -> None:
        self.df["category_id"] = category_id

    def get_transactions_dicts(self) -> list[dict[str, Any]]:
        return asyncio.run(
            generics_validator.validate_list_of_dicts(self.df.to_dict(orient="records"))
        )


class MonthlyResultsTable(BaseModel):
    """
    Represents a table summarizing financial results on a monthly basis.
    This class is used to analyze income, withdrawals, and savings over time.

    Attributes:
        df (pd.DataFrame): The DataFrame holding the monthly financial data.
                           Expected columns include 'year_month', 'initial_balance',
                           'total_income', 'total_withdrawal', 'saving', and 'user_id'.
    """

    model_config = TABLE_CONFIG

    df: pd.DataFrame = pd.DataFrame(
        {
            "year_month": [],
            "initial_balance": [],
            "total_income": [],
            "total_withdrawal": [],
            "savings": [],
            "user_id": [],
        }
    )

    @field_validator("df", mode="before")
    @classmethod
    def _validate_df_structure(cls, v: Any) -> pd.DataFrame:
        """
        Validates the structure of the monthly results DataFrame.
        Ensures the input is a DataFrame and contains the necessary columns for
        monthly financial analysis. Initializes an empty DataFrame with these columns
        if the input is empty.
        """
        v = generics_validator.validate_dataframe(v)

        if v.empty:
            return pd.DataFrame(
                {
                    "year_month": [],
                    "initial_balance": [],
                    "total_income": [],
                    "total_withdrawal": [],
                    "savings": [],
                    "user_id": [],
                }
            )

        if "user_id" not in v.columns:
            v["user_id"] = None

        if not all(
            col in v.columns
            for col in [
                "year_month",
                "initial_balance",
                "total_income",
                "total_withdrawal",
                "savings",
                "user_id",
            ]
        ):
            missing_cols = [
                col
                for col in [
                    "year_month",
                    "initial_balance",
                    "total_income",
                    "total_withdrawal",
                    "savings",
                    "user_id",
                ]
                if col not in v.columns
            ]
            raise ValueError(
                f"MonthlyResultsTable dataframe missing required columns: {missing_cols}. Available columns: {list(v.columns)}"
            )

        return v

    @property
    def year_months(self) -> pd.Series:
        return generics_validator.validate_series(self.df["year_month"])

    @year_months.setter
    def year_months(self, year_months: pd.Series) -> None:
        self.df["year_month"] = year_months

    @property
    def initial_balances(self) -> pd.Series:
        return generics_validator.validate_series(self.df["initial_balance"])

    @initial_balances.setter
    def initial_balances(self, initial_balances: pd.Series) -> None:
        self.df["initial_balance"] = initial_balances

    @property
    def total_incomes(self) -> pd.Series:
        return generics_validator.validate_series(self.df["total_income"])

    @total_incomes.setter
    def total_incomes(self, total_incomes: pd.Series) -> None:
        self.df["total_income"] = total_incomes

    @property
    def total_withdrawals(self) -> pd.Series:
        return generics_validator.validate_series(self.df["total_withdrawal"])

    @total_withdrawals.setter
    def total_withdrawals(self, total_withdrawals: pd.Series) -> None:
        self.df["total_withdrawal"] = total_withdrawals

    @property
    def savings(self) -> pd.Series:
        return generics_validator.validate_series(self.df["saving"])

    @savings.setter
    def savings(self, savings: pd.Series) -> None:
        self.df["saving"] = savings

    @property
    def user_id(self) -> pd.Series:
        return generics_validator.validate_series(self.df["user_id"])

    @user_id.setter
    def user_id(self, user_id: pd.Series) -> None:
        self.df["user_id"] = user_id

    @property
    def records(self) -> list[dict[str, Any]]:
        """
        Returns the DataFrame records as a list of dictionaries.
        """
        return asyncio.run(
            generics_validator.validate_list_of_dicts(self.df.to_dict(orient="records"))
        )

    async def get_avg_savings_per_month(self) -> float:
        avg = self.df["saving"].mean()
        if not isinstance(avg, float):
            raise ValueError("Average savings calculation did not return a float value.")
        return avg

    async def get_avg_income_per_month(self) -> float:
        avg = self.df["total_income"].mean()
        if not isinstance(avg, float):
            raise ValueError("Average income calculation did not return a float value.")
        return avg

    async def get_avg_withdrawal_per_month(self) -> float:
        avg = self.df["total_withdrawal"].mean()
        if not isinstance(avg, float):
            raise ValueError("Average withdrawal calculation did not return a float value.")
        return avg


class BudgetsTable(BaseModel):
    """
    Represents a table of budgets, linking users to categories with specified amounts.
    This class is used for managing and tracking budget allocations.

    Attributes:
        df (pd.DataFrame): The DataFrame holding the budget data.
                           Expected columns are 'user_id', 'category_id', 'amount',
                           'name', 'created_at', 'start_date', and 'end_date'.
    """

    model_config = TABLE_CONFIG

    df: pd.DataFrame

    @field_validator("df", mode="before")
    @classmethod
    def _validate_df_structure(cls, v: Any) -> pd.DataFrame:
        """
        Validates the structure of the budgets DataFrame.
        Ensures the input is a DataFrame and contains all necessary columns for
        budget management. Initializes an empty DataFrame with these columns if needed.
        """
        v = generics_validator.validate_dataframe(v)

        if v.empty:
            return pd.DataFrame(
                {
                    "user_id": [],
                    "category_id": [],
                    "amount": [],
                    "name": [],
                    "created_at": [],
                    "start_date": [],
                    "end_date": [],
                }
            )

        required_cols = [
            "user_id",
            "category_id",
            "amount",
            "name",
            "created_at",
            "start_date",
            "end_date",
        ]
        if not all(col in v.columns for col in required_cols):
            missing_cols = [col for col in required_cols if col not in v.columns]
            raise ValueError(
                f"BudgetsTable dataframe missing required columns: {missing_cols}. Available columns: {list(v.columns)}"
            )

        return v

    @property
    def user_id(self) -> pd.Series:
        return generics_validator.validate_series(self.df["user_id"])

    @property
    def categories_id(self) -> list[int]:
        return generics_validator.validate_list_int(self.df["category_id"].to_list())

    @property
    def amounts(self) -> pd.Series:
        return generics_validator.validate_series(self.df["amount"])

    @property
    def names(self) -> pd.Series:
        return generics_validator.validate_series(self.df["name"])

    @property
    def created_at(self) -> pd.Series:
        return generics_validator.validate_series(self.df["created_at"])

    @property
    def start_dates(self) -> pd.Series:
        return generics_validator.validate_series(self.df["start_date"])

    @property
    def end_dates(self) -> pd.Series:
        return generics_validator.validate_series(self.df["end_date"])
