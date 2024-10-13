import fitz
from core import DocumentReader
from typing import List


class PDFReader(DocumentReader):
    def extract_text_by_page(self) -> List[str]:
        with fitz.open(self.file_path) as doc:
            return [page.get_text() for page in doc]
