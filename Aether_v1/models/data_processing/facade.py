import pandas as pd
from typing import Tuple
from datetime import date
from .metadata_extraction import DefaultMetadataExtractor
from .table_normalzation import DefaultTableNormalizer, DateNormalizer, AmountNormalizer
from .special_data_filtering import DefaultSpecialDataFiltering

class DataProcessingFacade:
    def __init__(self, corrected_extracted_words: pd.DataFrame, reconstructed_table: pd.DataFrame, statement_properties: dict):
        self.corrected_extracted_words = corrected_extracted_words
        self.reconstructed_table = reconstructed_table
        self.statement_properties = statement_properties
        self.metadata_extractor = DefaultMetadataExtractor(self.corrected_extracted_words, self.statement_properties)
        self.table_normalizer = DefaultTableNormalizer(self.reconstructed_table, self.statement_properties, DateNormalizer(self.statement_properties), AmountNormalizer(self.statement_properties))
        
    def get_period(self) -> Tuple[date, date] | None:
        """
        Get the period of the statement.
        
        Returns:
            Tuple[date, date]: The start and end date of the statement.
            None: If the period is not found in the statement based in the bank properties.
        """
        return self.metadata_extractor.get_period()
    
    def get_balances(self) -> Tuple[float | None, float | None]:
        """
        Get the initial or final balance from the debit statements.
        For credit statements the function will return (None, None)
        
        Returns:
            Tuple[float, float]: The initial and final balance, if the statement is a debit statement.
            Tuple[None, None]: If the statement is a credit statement.
        """
        initial_balance = self.metadata_extractor.get_balance('initial')
        final_balance = self.metadata_extractor.get_balance('final')
        return initial_balance, final_balance
    
    def get_transactions(self) -> pd.DataFrame:
        years = self.metadata_extractor.get_years()
        initial_balance, final_balance = self.get_balances()
        
        bank = self.statement_properties['bank']
        statement_type = self.statement_properties['statement_type']
        
        table_normalized = self.table_normalizer.normalize_table(years, initial_balance)
        special_data_filtering = DefaultSpecialDataFiltering(table_normalized)
        filtered_table = special_data_filtering.filter_special_data(bank, statement_type)
        
        return filtered_table
    