import pdfplumber
import pandas as pd
from io import BytesIO
from functools import cache
import logging
from models.tables import ExtractedWords
from ..core import Reader

class PDFReader(Reader):
    """
    A class that reads a PDF file and can return file metadata and extracted words.
    This class is a wrapper around the pdfplumber library.
    
    Args:
        file (str | BytesIO): The path to the PDF file or a BytesIO object.
    """
    def __init__(self, file: str | BytesIO):
        super().__init__(file)
        # Suppress pdfminer page warnings
        logging.getLogger('pdfminer.pdfpage').setLevel(logging.ERROR)
    
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
    def extract_words(self) -> ExtractedWords:
        """
        Extract words from the PDF using pdfplumber.

        Returns:
            ExtractedWords: A DataFrame with the following columns:

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
                    
        return ExtractedWords(df= pd.DataFrame(extracted_words))