import pdfplumber
import pandas as pd
from io import BytesIO
import re
from functools import cache

class PDFReader:
    """
    A class that reads a PDF file and can return file metadata and extracted words.
    This class is a wrapper around the pdfplumber library.
    
    Args:
        file (str | BytesIO): The path to the PDF file or a BytesIO object.
    """
    def __init__(self, file: str | BytesIO):
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
        pdf_pattern = r'.*\.pdf$'
        return bool(re.match(pdf_pattern, self.file))
    
    def get_valid_file(self) -> str | BytesIO:
        """
        Validate the file and return a BytesIO object or a path.

        Returns:
            BytesIO | str: The validated file.

        Raises:
            ValueError: If the file is not a path or a BytesIO object.
        """
        if self._is_path():
            return self.file
        elif self._is_bytes_io():
            return BytesIO(self.file)
        else:
            raise ValueError("Invalid file type")
    
    def get_height(self) -> float:
        """
        Get the height of the first page of the PDF.

        Returns:
            float: Height of the first page.
        """
        file = self.get_valid_file()
        
        with pdfplumber.open(file) as pdf:
            return pdf.pages[0].height
        
    def get_width(self) -> float:
        """
        Get the width of the first page of the PDF.

        Returns:
            float: Width of the first page.
        """
        file = self.get_valid_file()
        
        with pdfplumber.open(file) as pdf:
            return pdf.pages[0].width
    
    @cache
    def extract_words(self) -> pd.DataFrame:
        """
        Extract words from the PDF using pdfplumber.

        Returns:
            pd.DataFrame: A DataFrame with the following columns:

            - page: The page number of the word.
            - text: The text of the word.
            - x0: The left coordinate of the word.
            - top: The top coordinate of the word.
            - x1: The right coordinate of the word.
            - bottom: The bottom coordinate of the word.
        """
        extracted_words = []
        
        file = self.get_valid_file()
        
        with pdfplumber.open(file) as pdf:
            for page_number, page in enumerate(pdf.pages, start= 1):
                words = page.extract_words()
                
                for word in words:
                    extracted_words.append(
                        {
                            'page' : page_number,
                            'text' : word['text'],
                            "x0": word["x0"],  # Left coordinate
                            "top": word["top"],  # Top coordinate
                            "x1": word["x1"],  # Right coordinate
                            "bottom": word["bottom"],  # Bottom coordinate
                        }
                    )
                    
        return pd.DataFrame(extracted_words)