import pandas as pd
from .boundary_detection import DefaultBoundaryDetector
from .segmentation import DefaultColumnSegmenter, DefaultRowSegmenter
from .reconstruction import TableReconstructor

class TableProcessingFacade:
    def __init__(self, corrected_extracted_words: pd.DataFrame, statement_properties: dict):
        self.corrected_extracted_words = corrected_extracted_words
        self.statement_properties = statement_properties
        self.boundary_detector = DefaultBoundaryDetector(corrected_extracted_words, statement_properties)
        
    def get_column_segmenter(self) -> DefaultColumnSegmenter:
        filtered_table_words = self.boundary_detector.get_filtered_table_words()
        
        return DefaultColumnSegmenter(filtered_table_words, self.statement_properties)
    
    def get_row_segmenter(self) -> DefaultRowSegmenter:
        filtered_table_words = self.boundary_detector.get_filtered_table_words()
        
        return DefaultRowSegmenter(filtered_table_words)
    
    def get_reconstructor(self) -> TableReconstructor:
        grouped_rows = self.row_segmenter.group_rows()
        column_delimitation = self.column_segmenter.delimit_column_positions()
        
        return TableReconstructor(grouped_rows, column_delimitation, self.statement_properties)
    
    def reconstruct_table(self) -> pd.DataFrame:
        reconstructed_table = self.reconstructor.reconstruct_table()
        
        return reconstructed_table