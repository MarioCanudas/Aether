from abc import ABC, abstractmethod
from typing import List, Dict
import pandas as pd

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

    @abstractmethod
    def extract_transactions(self, lines: List[str], month: str) -> List[Dict[str, str]]:
        """Extracts transactions from the provided lines based on the specified month."""
        pass

class TransactionProcessor(ABC):
    def __init__(self, reader: DocumentReader, extractor: TransactionExtractor):
        self.reader = reader
        self.extractor = extractor

    @abstractmethod
    def process_transactions(self, month: str) -> pd.DataFrame:
        """Processes the transactions for the specified month and returns them as a DataFrame."""
        pass
