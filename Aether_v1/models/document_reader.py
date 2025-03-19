import fitz
import easyocr as ocr
import numpy as np
import pdfplumber
import pandas as pd
from core import DocumentReader
from typing import List, Tuple


class PDFReader(DocumentReader):
    def extract_text_by_page(self) -> List[str]:
        with fitz.open(self.file_path) as doc:
            return [page.get_text() for page in doc]

    def extract_words_with_coordinates(self) -> List[List[Tuple[float, float, str]]]:
        words_from_page = []
        extracted_words = []
        with fitz.open(self.file_path) as doc:
            for page in doc:
                words = page.get_text('words')
                for word in words:
                    words_from_page.append((word[0], word[1], word[4])) # (x initial coordinate, y initial coordinate, text)
                extracted_words.append(words_from_page)
                words_from_page = []

        return extracted_words

    def extract_words_with_coordinates_with_ocr(self) -> List[List[Tuple[float, float, str]]]:
        reader = ocr.Reader(['es', 'en'])

        words_from_page = []
        extracted_words = []

        with fitz.open(self.file_path) as doc:
            for page in doc:
                words_from_page = []
                pix = page.get_pixmap(dpi= 150)

                img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)

                results = reader.readtext(img)

                for result in results:
                    bbox, text, conf = result

                    x, y = bbox[0]

                    words_from_page.append((float(x), float(y), text))

                extracted_words.append(words_from_page)

        return extracted_words

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
