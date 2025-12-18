import re
from abc import ABC, abstractmethod
from io import BytesIO
from typing import Literal

import pandas as pd
from models.bank_properties import BankProperties
from models.delimitations import ColumnDelimitations
from models.tables import ExtractedWords, GroupedRows, ReconstructedTable, TransactionsTable


class Reader(ABC):
    """Reads and extracts information from documents."""

    def __init__(self, file: str | BytesIO) -> None:
        self.file = file

    def _is_bytes_io(self) -> bool:
        """
        Check if self.file is a BytesIO object.

        Returns:
            bool: True if self.file is BytesIO, False if it's a path.
        """
        return isinstance(self.file, BytesIO)

    def _is_path(self) -> bool:
        """
        Check if self.file is a path.

        Returns:
            bool: True if self.file is a path, False if it's a BytesIO object.
        """

        pdf_pattern = r".*\.pdf$"
        return bool(re.match(pdf_pattern, self.file)) if isinstance(self.file, str) else False

    def get_valid_file(self) -> str | BytesIO:
        """
        Validate the file and return a BytesIO object or a path.

        Returns:
            BytesIO | str: The validated file.

        Raises:
            ValueError: If the file is not a path or a BytesIO object.
        """
        if self._is_path() or self._is_bytes_io():
            return self.file
        else:
            raise ValueError("Invalid file type")

    def get_file_name(self) -> str:
        """Gets the name of the file."""
        file = self.get_valid_file()

        return file.name if isinstance(file, BytesIO) else file

    @abstractmethod
    def get_height(self) -> float:
        """Obtains the document height."""
        pass

    @abstractmethod
    def get_width(self) -> float:
        """Obtains the document width."""
        pass

    @abstractmethod
    def extract_words(self) -> ExtractedWords:
        """Extracts all words with their positional information from the document."""
        pass


class DocumentAnalyzer(ABC):
    """Analyzes document content to identify bank and statement characteristics."""

    def __init__(self, reader: Reader) -> None:
        self.reader = reader

    @abstractmethod
    def detect_bank(
        self,
    ) -> Literal["amex", "banorte", "bbva", "citibanamex", "hsbc", "inbursa", "nu", "santander"]:
        """Identifies which bank issued the statement."""
        pass

    @abstractmethod
    def detect_statement_type(self) -> Literal["debit", "credit"]:
        """Determines whether the statement is for a debit or credit account."""
        pass

    @abstractmethod
    def get_bank_properties(self) -> BankProperties:
        """Retrieves the configuration properties specific to the detected bank and statement type."""
        pass


class TextProcessor(ABC):
    """Processes text data to extract relevant information."""

    def __init__(self, extracted_words: ExtractedWords, bank_properties: BankProperties) -> None:
        self.extracted_words = extracted_words
        self.bank_properties = bank_properties

    @abstractmethod
    def correct_text(self) -> ExtractedWords:
        """Corrects the text data to extract relevant information."""
        pass


class TableBoundaryDetector(ABC):
    """Detects the boundaries of the table in the document."""

    def __init__(
        self, corrected_extracted_words: ExtractedWords, bank_properties: BankProperties
    ) -> None:
        self.corrected_extracted_words = corrected_extracted_words
        self.bank_properties = bank_properties

    @abstractmethod
    def get_start_idx(self) -> int:
        """Gets the index of the start of the table."""
        pass

    @abstractmethod
    def get_end_idx(self) -> int:
        """Gets the index of the end of the table."""
        pass

    @abstractmethod
    def get_filtered_table_words(self) -> ExtractedWords:
        """Gets the filtered table words."""
        pass


class ColumnSegmenter(ABC):
    """Segments the columns of the table."""

    def __init__(
        self, filtered_table_words: ExtractedWords, bank_properties: BankProperties
    ) -> None:
        self.filtered_table_words = filtered_table_words
        self.bank_properties = bank_properties

    @abstractmethod
    def delimit_column_positions(self) -> ColumnDelimitations:
        """Delimits the column positions of the table."""
        pass


class RowSegmenter(ABC):
    """Segments the rows of the table."""

    def __init__(self, filtered_table_words: ExtractedWords) -> None:
        self.filtered_table_words = filtered_table_words

    @abstractmethod
    def get_row_threshold(self) -> float:
        """Gets the threshold for grouping rows."""
        pass

    @abstractmethod
    def group_rows(self) -> GroupedRows:
        """Groups the rows of the table."""
        pass


class Reconstructor(ABC):
    """Reconstructs the table from the segmented rows and columns."""

    def __init__(
        self,
        grouped_rows: GroupedRows,
        column_delimitation: ColumnDelimitations,
        bank_properties: BankProperties,
    ) -> None:
        self.grouped_rows = grouped_rows
        self.column_delimitation = column_delimitation
        self.bank_properties = bank_properties

    @abstractmethod
    def get_classified_rows(self) -> pd.DataFrame:
        """Classifies the words in the table into columns (date, description
        and amount columns, that depend on the statement properties)"""
        pass

    @abstractmethod
    def get_structured_table(self) -> ReconstructedTable:
        """Gets the structured table from the segmented rows and columns."""
        pass

    @abstractmethod
    def reconstruct_table(self) -> ReconstructedTable:
        """Reconstructs the table from the segmented rows and columns."""
        pass


class MetadataExtractor(ABC):
    """Extracts metadata from a given document, like the initial balance, the date of the statement, etc."""

    def __init__(
        self, corrected_extracted_words: ExtractedWords, bank_properties: BankProperties
    ) -> None:
        self.corrected_extracted_words = corrected_extracted_words
        self.bank_properties = bank_properties

    @abstractmethod
    def get_period(self) -> tuple[str, str]:
        """Gets the period of the statement."""
        pass

    @abstractmethod
    def get_balance(self, balance: Literal["initial", "final"]) -> float | None:
        """Gets the initial or final balance of the statement."""
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
    @abstractmethod
    def normalize_column(self, reconstructed_table: pd.DataFrame) -> pd.Series:
        """Normalizes the column into a consistent format."""
        pass


class TableNormalizer(ABC):
    """Normalizes the obtained table into a consistent format."""

    def __init__(
        self,
        reconstructed_table: ReconstructedTable,
        bank_properties: BankProperties,
        columns_normalizers: tuple[ColumnNormalizer, ColumnNormalizer],
    ) -> None:
        self.reconstructed_table = reconstructed_table
        self.bank_properties = bank_properties
        self.columns_normalizers = columns_normalizers

    @abstractmethod
    def normalize_table(self, years: list[int], filename: str) -> TransactionsTable:
        """Normalizes the table into a consistent format."""
        pass


class SpecialDataFiltering(ABC):
    """Filters out special data from the table."""

    @abstractmethod
    def filter_special_data(self, normalized_table: TransactionsTable) -> TransactionsTable:
        """Filters out special data from the table."""
        pass
