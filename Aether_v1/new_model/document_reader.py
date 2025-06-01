import pdfplumber
import pandas as pd
from core import NewDocumentReader

class PDFReader(NewDocumentReader):
    def get_height(self) -> float:
        """
        Get the height of the first page of the PDF.

        Returns:
            float: Height of the first page.
        """
        with pdfplumber.open(self.file_path) as pdf:
            return pdf.pages[0].height
        
    def get_width(self) -> float:
        """
        Get the width of the first page of the PDF.

        Returns:
            float: Width of the first page.
        """
        with pdfplumber.open(self.file_path) as pdf:
            return pdf.pages[0].width
    
    def extract_words(self) -> pd.DataFrame:
        extracted_words = []
        
        with pdfplumber.open(self.file_path) as pdf:
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
