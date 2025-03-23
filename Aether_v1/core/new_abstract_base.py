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

    def extract_text_by_page(self) -> List[str]:
        """Extracts text page by page from the document."""
        pass

    def extract_words_from_pdf(self) -> pd.DataFrame:
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

    def __init__(self, extracted_words: pd.DataFrame):
        self.extracted_words = extracted_words.copy()

    @abstractmethod
    def detect_bank(self) -> Literal['amex', 'banorte', 'bbva', 'citibanamex', 'hsbc', 'inbursa', 'nu', 'santander']:
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

    @property
    @abstractmethod
    def statement_propertys(self) -> dict:
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

    def __init__(self, df_table: pd.DataFrame):
        self.df_table = df_table

    @property
    @abstractmethod
    def sorted_df(self) -> pd.DataFrame:
        """"""
        pass

    @property
    @abstractmethod
    def row_threshold(self) -> float:
        """"""
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

    def __init__(self, grouped_rows: pd.DataFrame, statement_propertys: dict):
        self.grouped_rows = grouped_rows
        self.statement_propertys = statement_propertys

    @property
    @abstractmethod
    def header_row(self) -> float:
        """
        Locate the header row of the transaction table, which contains the column names.

        Returns:
            float: The vertical position of the header row.
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
        Generate the final structured transaction table.

        Returns:
            pd.DataFrame: The structured table with properly classified data.
        """
        pass