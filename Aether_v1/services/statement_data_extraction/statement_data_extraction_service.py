from io import BytesIO
from functools import cache, cached_property
from models.bank_properties import BankProperties
from models.tables import ExtractedWords, ReconstructedTable, TransactionsTable
from .document_processing import PDFReader, DefaultDocumentAnalyzer, DefaultTextProcessor
from .table_processing import DefaultColumnSegmenter, DefaultRowSegmenter, TableReconstructor
from .data_processing import DefaultMetadataExtractor, DefaultTableNormalizer, DateNormalizer, AmountNormalizer

class StatementDataExtractionService:
    def __init__(self, file: str | BytesIO):
        if not isinstance(file, (str, BytesIO)):
            raise ValueError("File must be a string or a BytesIO object")
        
        self.file = file
        self.reader = PDFReader(self.file)
        self.analyzer = DefaultDocumentAnalyzer(self.reader)
       
    @property
    def filename(self) -> str:
        if isinstance(self.file, BytesIO):
            return self.file.name
        else:
            return self.file
        
    @cache
    def get_bank_properties(self) -> BankProperties:
        analyzer = DefaultDocumentAnalyzer(self.reader)
        bank_properties = analyzer.get_bank_properties()
        
        return bank_properties
        
    @cache
    def get_corrected_extracted_words(self) -> ExtractedWords:
        extracted_words = self.reader.extract_words()
        
        text_processor = DefaultTextProcessor(extracted_words, self.get_bank_properties())
        
        return text_processor.correct_text()
    
    @cached_property
    def metadata_extractor(self) -> DefaultMetadataExtractor:
        corrected_extracted_words = self.get_corrected_extracted_words()
        bank_properties = self.get_bank_properties()
        
        return DefaultMetadataExtractor(corrected_extracted_words, bank_properties)
    
    def get_reconstructed_table(self) -> ReconstructedTable:
        corrected_extracted_words = self.get_corrected_extracted_words()
        bank_properties = self.get_bank_properties()
        
        start_phrase = bank_properties.start_phrase
        end_phrase = bank_properties.end_phrase
        filtered_table_words = corrected_extracted_words.filter_table_by_phrases(start_phrase, end_phrase)
        
        column_segmenter = DefaultColumnSegmenter(filtered_table_words, bank_properties)
        column_delimitations = column_segmenter.delimit_column_positions()
        
        row_segmenter = DefaultRowSegmenter(filtered_table_words)
        grouped_rows = row_segmenter.group_rows()
        
        reconstructed_table = TableReconstructor(grouped_rows, column_delimitations, bank_properties)
        
        return reconstructed_table.reconstruct_table()
    
    def get_normalized_table(self) -> TransactionsTable:
        reconstructed_table = self.get_reconstructed_table()
        bank_properties = self.get_bank_properties()
        
        years = self.metadata_extractor.get_years()
        
        date_normalizer = DateNormalizer()
        amount_normalizer = AmountNormalizer()
        
        table_normalizer = DefaultTableNormalizer(reconstructed_table, bank_properties, (date_normalizer, amount_normalizer))
        
        return table_normalizer.normalize_table(years, self.filename)
    
    def get_transactions(self) -> TransactionsTable:
        normalized_table = self.get_normalized_table()
        
        initial_balance_row = self.metadata_extractor.get_initial_balance_row(self.filename)
        generated_amount_row = self.metadata_extractor.get_generated_amount_row(self.filename)
        
        if initial_balance_row is not None:
            normalized_table.add_row(initial_balance_row)
            
        if generated_amount_row is not None:
            normalized_table.add_row(generated_amount_row)
        
        return normalized_table
    