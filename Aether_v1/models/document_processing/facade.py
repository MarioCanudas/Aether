from io import BytesIO
import pandas as pd
from functools import cache
from .document_reading import PDFReader
from .document_analysis import DefaultDocumentAnalyzer
from .text_processing import DefaultTextProcessor

class DocumentProcessingFacade:
    def __init__(self, file: str | BytesIO):
        self.reader = PDFReader(file)
        self.analyzer = DefaultDocumentAnalyzer(self.reader)
        
    def get_extracted_words(self) -> pd.DataFrame:
        return self.reader.extract_words()
    
    @cache
    def get_statement_properties(self) -> dict:
        return self.analyzer.get_statement_properties()
        
    def get_text_processor(self) -> DefaultTextProcessor:
        extracted_words = self.get_extracted_words()
        statement_properties = self.get_statement_properties()
        
        return DefaultTextProcessor(extracted_words, statement_properties)
    
    def get_corrected_extracted_words(self) -> pd.DataFrame:
        text_processor = self.get_text_processor()
        
        return text_processor.correct_text()