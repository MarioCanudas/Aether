from abc import ABC, abstractmethod
from typing import Literal, Dict, List, Tuple
import pandas as pd

class DocumentReader(ABC):
    """
    Base class for reading documents and extracting text data with positional information.

    Attributes:
        file_path (str): Path to the document file.
    """

    def __init__(self, file_path: str):
        self.file_path = file_path

    @abstractmethod
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

    #@abstractmethod
    #def standardize_dates(self, structured_df: pd.DataFrame) -> pd.DataFrame:
    #    """
    #    Standardize dates to the format YYYY-MM-DD, based on the statement's date pattern.

    #    Args:
    #        structured_df (pd.DataFrame): The DataFrame in the bank's statement format.

    #    Returns:
    #        pd.DataFrame: The DataFrame with standardized dates.
    #    """
    #    pass

    @abstractmethod
    def get_structured_table(self) -> pd.DataFrame:
        """
        Generate the final structured transaction table.

        Returns:
            pd.DataFrame: The structured table with properly classified data.
        """
        pass


class TransactionExtractor(ABC):
    def __init__(self, month_patterns: Dict[str, str]):
        self.month_patterns = month_patterns
        self.year = None

    @abstractmethod
    def extract_month_from_pdf(self, lines: List[str]) -> List[str]:
        """
        This method should be implemented by any subclass.
        It is responsible for scanning the PDF lines and extracting
        the month abbreviation (e.g., 'ENE' for January, 'FEB' for February)
        from the content.

        :param lines: A list of strings representing the lines of the PDF text.
        :return: The detected month abbreviation as a string.
        """
        pass

    @abstractmethod
    def extract_transactions(self, lines: List[str]) -> List[Dict[str, str]]:
        """Extracts transactions from the provided lines based on the specified month."""
        pass

    def detect_year_from_pdf(self, lines: List[str]) -> int:
        """
        Detects the year from the PDF content by searching for a year pattern.

        Parameters:
        - lines (List[str]): Extracted text lines from the PDF.

        Returns:
        - int: Detected year, or None if not found.
        """
        for line in lines:
            year_match = re.search(r'\b(20\d{2})\b', line)
            if year_match:
                return int(year_match.group(1))
        return None

    def classify_words_from_page(self, pages: List[Tuple[float, float, str]]) -> Dict[str, List[Tuple[float, float, int, str]]]:
        """
        Classifies words extracted from PDF pages into three categories: dates, descriptions, and amounts.

        The classification is based on the x-coordinate of the words, which determines their alignment and
        positional significance. This method processes a list of words with their x-coordinates, y-coordinates,
        and text content, and organizes them into a dictionary.

        Parameters:
            pages (List[Tuple[float, float, str]]):
            - A list of tuples where each tuple contains:
                - x (float): The x-coordinate of the word.
                - y (float): The y-coordinate of the word.
                - text (str): The content of the word.

        Returns:
            Dict[str, List[Tuple[float, float, int, str]]]:
            - A dictionary with the following keys:
                - 'dates': A list of strings representing words classified as dates.
                - 'descriptions': A list of strings representing words classified as descriptions.
                - 'amounts': A list of strings representing words classified as amounts.
            - Where each list contains a tuple with the following elements:
                - x (float): The x-coordinate of the word.
                - y (float): The y-coordinate of the word.
                - page (int): The page number where the word is located.
                - text (str): The content of the word.
        """
        pass
class TransactionProcessor(ABC):
    def __init__(self, reader: DocumentReader, extractor: TransactionExtractor):
        self.reader = reader
        self.extractor = extractor

    @abstractmethod
    def process_transactions(self, month: str) -> pd.DataFrame:
        """Processes the transactions for the specified month and returns them as a DataFrame."""
        pass
