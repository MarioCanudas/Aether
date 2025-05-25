import pandas as pd
from io import BytesIO
from new_model import (
    PDFReader, 
    DefaultBankDetector, 
    TransactionTableBoundaryDetector, 
    TransactionRowSegmenter, 
    TransactionTableReconstructor, 
    TransactionTableNormalizer
)

class TransactionProcessorController:
    def identify_pdf(self, file: str | BytesIO) -> str:
        reader = PDFReader(file)
        bank_detector = DefaultBankDetector(reader)
        
        bank_name = bank_detector.detect_bank()
        statement_type = bank_detector.detect_statement_type()

        return {
            "bank": bank_name,
            "statement_type": statement_type
        }
    
    def process_transactions(self, file: str | BytesIO) -> pd.DataFrame:
        reader = PDFReader(file)
        bank_detector = DefaultBankDetector(reader)

        boundary_detector = TransactionTableBoundaryDetector(bank_detector)
        if boundary_detector.start_idx is None or boundary_detector.end_idx is None:
            bank_detector = DefaultBankDetector(reader, new_credit_format=True)
            boundary_detector = TransactionTableBoundaryDetector(bank_detector)
        df_table = boundary_detector.get_filtered_table_words()
        
        row_segmenter = TransactionRowSegmenter(df_table, bank_detector)
        column_delimitation = row_segmenter.delimit_column_positions()
        grouped_rows = row_segmenter.group_rows()

        table_reconstructor = TransactionTableReconstructor(grouped_rows, column_delimitation, bank_detector)
        df_structured = table_reconstructor.reconstruct_table()

        table_normalizer = TransactionTableNormalizer(df_structured, bank_detector)
        
        return table_normalizer.normalize_table()
        