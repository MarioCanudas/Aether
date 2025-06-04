import pdfplumber
import pandas as pd
from io import BytesIO
from core import DocumentReader

class PDFReader(DocumentReader):
    def _is_bytes_io(self) -> bool:
        """
        Check if self.file is a BytesIO object.

        Returns:
            bool: True if self.file is BytesIO, False if it's a path.
        """
        return isinstance(self.file, BytesIO)

    def get_height(self) -> float:
        """
        Get the height of the first page of the PDF.

        Returns:
            float: Height of the first page.
        """
        file = self.file if not self._is_bytes_io() else BytesIO(self.file)
        with pdfplumber.open(file) as pdf:
            return pdf.pages[0].height
        
    def get_width(self) -> float:
        """
        Get the width of the first page of the PDF.

        Returns:
            float: Width of the first page.
        """
        file = self.file if not self._is_bytes_io() else BytesIO(self.file)
        with pdfplumber.open(file) as pdf:
            return pdf.pages[0].width
    
    def extract_words(self) -> pd.DataFrame:
        extracted_words = []
        
        file = self.file if not self._is_bytes_io() else BytesIO(self.file)
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
