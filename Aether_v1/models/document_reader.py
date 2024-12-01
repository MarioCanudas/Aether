import fitz
from core import DocumentReader
from typing import List, Tuple


class PDFReader(DocumentReader):
    def extract_text_by_page(self) -> List[str]:
        with fitz.open(self.file_path) as doc:
            return [page.get_text() for page in doc]

    def extract_words_with_coordinates(self) -> List[List[Tuple[float, str]]]:
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