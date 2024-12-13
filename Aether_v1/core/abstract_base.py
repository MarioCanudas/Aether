from abc import ABC, abstractmethod
from typing import List, Dict, Tuple
import pandas as pd
import re
class DocumentReader(ABC):
    def __init__(self, file_path: str):
        self.file_path = file_path

    @abstractmethod
    def extract_text_by_page(self) -> List[str]:
        """Extracts text page by page from the document."""
        pass
    
    @abstractmethod
    def extract_words_with_coordinates(self) -> List[Tuple[float, float, str]]:
        """Extracts words with their x-coordinates, y-coordinates, and text content from the document."""
        pass
    
    @abstractmethod
    def extract_words_with_coordinates_with_ocr(self) -> List[Tuple[float, float, str]]:
        """
        Extracts words along with their coordinates from a PDF file using OCR.

        This method processes each page of the PDF specified by the file path,
        converts the pages into images at a specified resolution (DPI), and applies
        OCR to detect text. For each detected word, the method retrieves its
        bounding box coordinates, extracts the top-left corner's position (x, y),
        and associates it with the detected text.

        Returns:
            A list of lists, where each inner list contains tuples representing
            the words detected on a single page. Each tuple consists of:
            - float: The x-coordinate of the word's top-left corner.
            - float: The y-coordinate of the word's top-left corner.
            - str: The text of the word.
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
    
    @abstractmethod
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
