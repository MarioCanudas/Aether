from abc import ABC, abstractmethod
from typing import List, Dict
import pandas as pd
import re
class DocumentReader(ABC):
    def __init__(self, file_path: str):
        self.file_path = file_path

    @abstractmethod
    def extract_text_by_page(self) -> List[str]:
        """Extracts text page by page from the document."""
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

class TransactionProcessor(ABC):
    def __init__(self, reader: DocumentReader, extractor: TransactionExtractor):
        self.reader = reader
        self.extractor = extractor

    @abstractmethod
    def process_transactions(self, month: str) -> pd.DataFrame:
        """Processes the transactions for the specified month and returns them as a DataFrame."""
        pass
