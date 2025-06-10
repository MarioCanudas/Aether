from abc import ABC, abstractmethod
from typing import Literal
import pandas as pd

class Reader(ABC):
    """Reads and extracts information from documents."""
    
    @abstractmethod
    def get_height(self) -> float: 
        """Obtains the document height."""
        pass
    
    @abstractmethod
    def get_width(self) -> float: 
        """Obtains the document width."""
        pass
    
    @abstractmethod
    def extract_words(self) -> pd.DataFrame: 
        """Extracts all words with their positional information from the document."""
        pass
    
class DocumentAnalyzer(ABC):
    """Analyzes document content to identify bank and statement characteristics."""

    def __init__(self, reader: Reader):
        self.reader = reader

    @abstractmethod
    def detect_bank(self) -> Literal['amex', 'banorte', 'bbva', 'citibanamex', 'hsbc', 'inbursa', 'nu', 'santander']:
        """Identifies which bank issued the statement."""
        pass

    @abstractmethod
    def detect_statement_type(self) -> Literal['debit', 'credit']:
        """Determines whether the statement is for a debit or credit account."""
        pass

    @abstractmethod
    def get_statement_properties(self) -> dict:
        """Retrieves the configuration properties specific to the detected bank and statement type."""
        pass
    
class TextProcessor(ABC):
    """Processes text data to extract relevant information."""
    def __init__(self, extracted_words: pd.DataFrame, statement_properties: dict):
        self.extracted_words = extracted_words
        self.statement_properties = statement_properties
    
    @abstractmethod
    def correct_text(self) -> pd.DataFrame:
        """Corrects the text data to extract relevant information."""
        pass
    
class TableBoundaryDetector(ABC):
    """Detects the boundaries of the table in the document."""
    def __init__(self, corrected_extracted_words: pd.DataFrame, statement_properties: dict):
        self.corrected_extracted_words = corrected_extracted_words
        self.statement_properties = statement_properties
    
    @abstractmethod
    def get_start_idx(self) -> int:
        """Gets the index of the start of the table."""
        pass
    
    @abstractmethod
    def get_end_idx(self) -> int:
        """Gets the index of the end of the table."""
        pass
    
    @abstractmethod
    def get_filtered_table_words(self) -> pd.DataFrame:
        """Filters the table words to only include the words that are part of the table."""
        pass
    
class ColumnSegmenter(ABC):
    """Segments the columns of the table."""
    def __init__(self, filtered_table_words: pd.DataFrame, statement_properties: dict):
        self.filtered_table_words = filtered_table_words
        self.statement_properties = statement_properties
    
    @abstractmethod
    def delimit_column_positions(self) -> dict:
        """Delimits the column positions of the table."""
        pass
    
class RowSegmenter(ABC):
    """Segments the rows of the table."""
    def __init__(self, filtered_table_words: pd.DataFrame):
        self.filtered_table_words = filtered_table_words
    
    @abstractmethod
    def get_row_threshold(self) -> float:
        """Gets the threshold for grouping rows."""
        pass
    
    @abstractmethod
    def group_rows(self) -> pd.DataFrame:
        """Groups the rows of the table."""
        pass
    
class Reconstructor(ABC):
    """Reconstructs the table from the segmented rows and columns."""
    def __init__(self, grouped_rows: pd.DataFrame, column_delimitation: dict, statement_properties: dict):
        self.grouped_rows = grouped_rows
        self.column_delimitation = column_delimitation
        self.statement_properties = statement_properties
        
    @abstractmethod
    def classify_columns(self) -> pd.DataFrame:
        """Classifies the words in the table into columns (date, description 
        and amount columns, that depend on the statement properties)"""
        pass
    
    @abstractmethod
    def get_structured_table(self) -> pd.DataFrame:
        """Gets the structured table from the segmented rows and columns."""
        pass
    
    @abstractmethod
    def reconstruct_table(self) -> pd.DataFrame:
        """Reconstructs the table from the segmented rows and columns."""
        pass

class MetadataExtractor(ABC):
    """Extracts metadata from a given document, like the initial balance, the date of the statement, etc."""
    def __init__(self, corrected_extracted_words: pd.DataFrame, statement_properties: dict):
        self.corrected_extracted_words = corrected_extracted_words
        self.statement_properties = statement_properties
    
    @abstractmethod
    def get_period(self) -> tuple[str, str]:
        """Gets the period of the statement."""
        pass
    
    @abstractmethod
    def get_initial_balance(self) -> float:
        """Gets the initial balance of the statement."""
        pass
    
    @abstractmethod
    def get_years(self) -> list[int]:
        """Gets the years of the statement."""
        pass
    
    @abstractmethod
    def get_months(self) -> list[str]:
        """Gets the months of the statement."""
        pass
    
class ColumnNormalizer(ABC):
    def __init__(self, statement_properties: dict):
        self.statement_properties = statement_properties
    
    @abstractmethod
    def normalize_column(self, column: pd.Series | pd.DataFrame) -> pd.Series:
        """Normalizes the column into a consistent format."""
        pass
    
class TableNormalizer(ABC):
    """Normalizes the obtained table into a consistent format."""
    def __init__(self, reconstructed_table: pd.DataFrame, statement_properties: dict, date_normalizer: ColumnNormalizer, amount_normalizer: ColumnNormalizer):
        self.reconstructed_table = reconstructed_table
        self.statement_properties = statement_properties
        self.date_normalizer = date_normalizer
        self.amount_normalizer = amount_normalizer
    
    @abstractmethod
    def normalize_table(self, initial_balance: float) -> pd.DataFrame:
        """Normalizes the table into a consistent format."""
        pass
    