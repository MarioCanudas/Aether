import pandas as pd
from typing import Dict
from .metadata_extraction import DefaultMetadataExtractor
from .table_normalzation import DefaultTableNormalizer, DateNormalizer, AmountNormalizer
from .special_data_filtering import SpecialDataFiltering

class DataProcessingFacade:
    def __init__(self, corrected_extracted_words: pd.DataFrame, reconstructed_table: pd.DataFrame, statement_properties: dict):
        self.corrected_extracted_words = corrected_extracted_words
        self.reconstructed_table = reconstructed_table
        self.statement_properties = statement_properties
        self.metadata_extractor = DefaultMetadataExtractor(self.corrected_extracted_words, self.statement_properties)
        self.table_normalizer = DefaultTableNormalizer(self.reconstructed_table, self.statement_properties, DateNormalizer(self.statement_properties), AmountNormalizer(self.statement_properties))
        
    def get_period(self) -> Dict[str, int | str]:
        months = self.metadata_extractor.get_months() # TODO: Implement month extraction
        years = self.metadata_extractor.get_years()
        
        return {
            'start_month': None,
            'start_year': years[0],
            'end_month': None,
            'end_year': years[-1]
        }
    
    def get_normalized_table(self) -> pd.DataFrame:
        years = self.metadata_extractor.get_years()
        initial_balance = self.metadata_extractor.get_initial_balance()
        
        bank = self.statement_properties['bank']
        statement_type = self.statement_properties['statement_type']
        
        table_normalized = self.table_normalizer.normalize_table(years, initial_balance)
        special_data_filtering = SpecialDataFiltering(table_normalized)
        filtered_table = special_data_filtering.filter_special_data(bank, statement_type)
        
        return filtered_table
    