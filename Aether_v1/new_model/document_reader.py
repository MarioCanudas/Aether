import pdfplumber
import pandas as pd
from core import DocumentReader

class PDFReader(DocumentReader):
    def extract_words_from_pdf(self) -> pd.DataFrame:
        extracted_words = []
        
        with pdfplumber.open(self.file_path) as pdf:
            for page_number, page in enumerate(pdf.pages, start= 1):
                words = page.extract_words()
                page_height = page.height
                
                for word in words:
                    extracted_words.append(
                        {
                            'page' : page_number,
                            'page_height' : page_height,
                            'text' : word['text'],
                            "x0": word["x0"],  # Left coordinate
                            "top": word["top"],  # Top coordinate
                            "x1": word["x1"],  # Right coordinate
                            "bottom": word["bottom"],  # Bottom coordinate
                        }
                    )
                    
        return pd.DataFrame(extracted_words)
