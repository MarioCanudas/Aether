from abc import ABC, abstractmethod
from typing import Literal, Dict, List, Tuple
import pandas as pd

class NewDocumentReader(ABC):
    """
    Base class for reading documents and extracting text data with positional information.

    Attributes:
        file_path (str): Path to the document file.
    """

    def __init__(self, file_path: str):
        self.file_path = file_path
        
    @abstractmethod
    def get_height(self) -> float:
        """
        Get the height of the document.

        Returns:
            float: Height of the document.
        """
        pass

    @abstractmethod
    def extract_words(self) -> pd.DataFrame:
        """
        Extract words along with their x and y coordinates and text content.

        Returns:
            pd.DataFrame: A DataFrame with columns ['page', 'text', 'x0', 'top', 'x1', 'bottom'] representing
                        the bounding box coordinates and the word content.
        """
        pass

class BankDetector(ABC):
    """
    Base class for detecting the bank and statement type from extracted words.

    Attributes:
        extracted_words (pd.DataFrame): DataFrame containing the extracted words and their positions.
    """

    def __init__(self, DocumentReader: NewDocumentReader):
        self.document_reader = DocumentReader
        
    @property
    @abstractmethod
    def extracted_words(self) -> pd.DataFrame:
        """
        Extract words from the document using the DocumentReader.

        Returns:
            pd.DataFrame: DataFrame containing the extracted words and their positions.
        """
        pass

    @abstractmethod
    def detect_bank(self, document_height: float) -> Literal['amex', 'banorte', 'bbva', 'citibanamex', 'hsbc', 'inbursa', 'nu', 'santander']:
        """
        Detect the bank associated with the extracted words.

        Returns:
            Literal: The detected bank name.
        """
        pass

    @abstractmethod
    def detect_statement_type(self) -> Literal['debit', 'credit']:
        """
        Detect the type of bank statement (debit or credit).

        Returns:
            Literal: The statement type.
        """
        pass

    @abstractmethod
    def get_statement_properties(self, new_credit_format: bool) -> dict:
        """
        Determine the characteristics of the bank statement, such as transaction table columns, start and end phrases, and date patterns.

        Returns:
            dict: A dictionary containing statement properties.
        """
        pass

class TableBoundaryDetector(ABC):
    """
    Base class for detecting the boundaries of the transaction table within the extracted words.

    Attributes:
        extracted_words (pd.DataFrame): DataFrame of extracted words.
        statement_properties (dict): Dictionary with the statement's metadata.
    """

    def __init__(self, extracted_words: pd.DataFrame, statement_propertys: dict):
        self.extracted_words = extracted_words.copy()
        self.statement_propertys = statement_propertys
        
    @property    
    @abstractmethod
    def df_corrected(self) -> pd.DataFrame:
        """
        Correct the extracted words DataFrame by removing unnecessary words and correcting reading pdf errors.

        Returns:
            pd.DataFrame: Corrected DataFrame of extracted words.
        """
        pass

    @property
    @abstractmethod
    def start_idx(self) -> int:
        """
        Get the index where the transaction table starts.

        Returns:
            int: The index of the start phrase.
        """
        pass

    @property
    @abstractmethod
    def end_idx(self) -> int:
        """
        Get the index where the transaction table ends.

        Returns:
            int: The index of the end phrase.
        """
        pass

    @abstractmethod
    def get_filtered_table_words(self) -> pd.DataFrame:
        """
        Extract the rows that correspond to the transaction table between the start and end indices.

        Returns:
            pd.DataFrame: DataFrame containing the transaction table.
        """
        pass

class RowSegmenter(ABC):
    """
    Base class for segmenting rows by grouping words that are horizontally aligned.

    Attributes:
        df_table (pd.DataFrame): DataFrame containing the transaction table.
    """

    def __init__(self, df_table: pd.DataFrame, statement_propertys: dict):
        self.df_table = df_table.copy()
        self.statement_propertys = statement_propertys

    @property
    @abstractmethod
    def sorted_df(self) -> pd.DataFrame:
        """
        Sort the DataFrame by page and top coordinates.
        """
        pass
    
    @abstractmethod
    def delimit_column_positions(self) -> dict:
        """
        Delimit the column positions based on the header row.

        Returns:
            dict: A dictionary with column names as keys and their x-coordinates as values.
        """
        pass

    @property
    @abstractmethod
    def row_threshold(self) -> float:
        """
        Calculate the threshold for grouping words into rows based on their vertical position.
        """
        pass

    @abstractmethod
    def group_rows(self) -> pd.DataFrame:
        """
        Group words that are on the same row based on their vertical position.

        Returns:
            pd.DataFrame: A DataFrame with grouped rows.
        """
        pass

class TableReconstructor(ABC):
    """
    Base class for reconstructing the transaction table from grouped rows.

    Attributes:
        grouped_rows (pd.DataFrame): DataFrame with words grouped by row.
    """

    def __init__(self, grouped_rows: pd.DataFrame, column_delimitation: dict, statement_propertys: dict):
        self.grouped_rows = grouped_rows
        self.column_delimitation = column_delimitation
        self.statement_propertys = statement_propertys
        
    @property
    @abstractmethod
    def column_positions(self) -> dict:
        """
        Get the positions of the columns based on the header row.

        Returns:
            dict: A dictionary with column names as keys and their x-coordinates as values.
        """
        pass
        
    @abstractmethod
    def classify_columns(self, row) -> pd.Series:
        """
        Classify words into the corresponding columns based on the x-coordinate.

        Args:
            row (pd.Series): A row from the DataFrame with grouped words.

        Returns:
            pd.Series: A Series with words classified by columns.
        """
        pass

    @abstractmethod
    def get_structured_table(self) -> pd.DataFrame:
        """
        Get the structured table with properly classified data, based in the columns positions.

        Returns:
            pd.DataFrame: The structured table with properly classified data.
        """
        pass
    
    @abstractmethod
    def reconstruct_table(self) -> pd.DataFrame:
        """
        Reconstruct the transaction table from the structured table.

        Returns:
            pd.DataFrame: The reconstructed transaction table.
        """
        pass
    
class TableNormalizer(ABC):
    """
    Base class for normalizing the reconstructed transaction table from the statement.

    Attributes:
        df_table (pd.DataFrame): DataFrame containing the reconstructed transaction table.
        df_extracted_words (pd.DataFrame): DataFrame containing the extracted words.
        statement_properties (dict): Dictionary with the statement's metadata.
    """
    
    def __init__(self, df_table: pd.DataFrame, df_extracted_words: pd.DataFrame, statement_properties: dict):
        self.df_table = df_table.copy()
        self.df_extracted_words = df_extracted_words.copy()
        self.statement_properties = statement_properties
        
    @property
    @abstractmethod
    def period_idx(self) -> int:
        """
        Determines the index of the column containing the period information.

        Returns:
            int: Index of the column containing the period information.
        """
        pass
        
    @property
    @abstractmethod
    def years(self) -> List[int]:
        """
        Extracts the year from the statement.

        Returns:
            List[int]: List of years extracted from the statement.
        """
        pass
    
    @property
    @abstractmethod
    def months(self) -> List[str]:
        """
        Extracts the month from the statement.
        
        Returns:
            List[str]: List of months extracted from the statement.
        """
        pass
    
    @abstractmethod
    def normalize_dates(self, date_column: pd.Series) -> pd.Series:
        """
        Normalize the dates in the transaction table.

        Args:
            date_column (pd.Series): Series containing the date column.

        Returns:
            pd.Series: Series with normalized dates.
        """
        pass
    
    @abstractmethod
    def normalize_amounts(self, amount_column: pd.Series) -> pd.Series:
        """
        Normalize the amounts in the transaction table.

        Args:
            amount_column (pd.Series): Series containing the amount column.

        Returns:
            pd.Series: Series with normalized amounts.
        """
        pass

    @abstractmethod
    def normalize_table(self) -> pd.DataFrame:
        """
        Standardizes the extracted transaction table into a uniform format suitable for database storage.

        Returns:
            pd.DataFrame: Normalized transaction table with standardized columns:
                - date: Transaction date (YYYY-MM-DD)
                - description: Standardized transaction description
                - amount: Transaction amount as decimal
                - type: Transaction type (expense/income/balance)
        """
        pass
    
class DataExporter(ABC):
    """
    Base class for exporting the normalized transaction table to a database.

    Attributes:
        df_table (pd.DataFrame): DataFrame containing the normalized transaction table.
    """

    def __init__(self, df_table: pd.DataFrame):
        self.df_table = df_table.copy()

    @abstractmethod
    def export_to_csv(self, file_path: str) -> None:
        """
        Export the DataFrame to a CSV file.

        Args:
            file_path (str): Path to save the CSV file.
        """
        pass