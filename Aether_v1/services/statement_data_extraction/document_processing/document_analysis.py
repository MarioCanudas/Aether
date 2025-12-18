import re
from functools import cache
import pandas as pd
from typing import cast
from ..core import DocumentAnalyzer, Reader
from utils import search_phrase_in_df
from constants.banks_properties import BANKS_CODES
from models.bank_properties import BankName, StatementType, BankProperties
from .bank_properties_factory import BankPropertiesFactory
       
class DefaultDocumentAnalyzer(DocumentAnalyzer):
    """
    A class that detects the bank metadata of a given document.

    Args:
        document_reader (DocumentReader): A document reader object.
    """
    def __init__(self, reader: Reader):
        super().__init__(reader)
        self.bank_properties_factory = BankPropertiesFactory()
    
    def detect_bank_in_footer(self) -> BankName | None:
        """
        Detect the bank by analyzing the footer of the document.
        
        Returns:
            BankName | None: The detected bank name if found, otherwise None.
        """
        try:
            extracted_words = self.reader.extract_words()
            document_height = self.reader.get_height() # Get height to determine the footer threshold
            
            footer_percentage = 0.15
            footer_threshold = document_height * footer_percentage # Calculate the footer threshold using 15% of the document height

            df_footer = extracted_words.df[extracted_words.df['bottom'] > document_height - footer_threshold] # Filter the rows that are in the footer
            df_footer = cast(pd.DataFrame, df_footer)
            
            # Convert all footer text to lowercase for case-insensitive searches
            footer_text = df_footer['text'].apply(lambda x: x.lower())
            
            # Iterate through all known banks to search for matches
            for bank in BankName:
                # Create a boolean mask that searches for the bank name as a complete word
                # \b = word boundary to avoid partial matches
                # re.escape() escapes special characters in the bank name
                # regex=True enables the use of regular expressions
                # na=False ensures that NaN values are treated as False instead of NaN
                mask = footer_text.str.contains(f"\\b{re.escape(bank.value)}\\b", regex=True, na=False)
                
                # If at least one match of the bank is found in the footer
                if mask.any():
                    return bank
            
            # Special case for Nu credit, because the document dosen't have a footer either CLABE
            if search_phrase_in_df(extracted_words.df, ['nu', 'méxico', 'financiera,'], type_return='bool'):
                return BankName.NU
        
            return None
        
        except Exception as e:
            raise ValueError(f"Error detecting bank in footer: {e}")
        
    def detect_bank_by_code(self) -> BankName | str | None:
        """
        Detect the bank by analyzing the CLABE code in the document.
        
        Returns:
            BankName | None: The detected bank name if found, otherwise None.
        """
        try:
            extracted_words = self.reader.extract_words()
            df_extracted_words = extracted_words.df
        
            clabe_keyword = r'\bclabe\b'
            
            clabe_pattern = r'(\d{3})(\d{7,15})?'
            
            # Create a boolean Series (mask) that searches for the CLABE keyword in the text column
            # na=False ensures that NaN values are treated as False instead of NaN
            mask = extracted_words.df['text'].str.contains(clabe_keyword, regex=True, case=False, na=False)
            
            if mask.any():
                # Get the indices of the rows where the CLABE keyword is found
                clabe_indices = extracted_words.df.index[mask].tolist()
                
                for idx in clabe_indices:
                    # Determine the range of the nearest text to the CLABE keyword
                    start_idx = max(0, idx - 5)
                    end_idx = min(len(extracted_words.df), idx + 20)
                    
                    # Extract text in that range and remove spaces
                    nearby_text = extracted_words.df.iloc[start_idx:end_idx]['text'].astype(str)
                    nearby_text = nearby_text.str.replace(r'\s+', '', regex=True) # Remove spaces
                    
                    for text in nearby_text:
                        # Find all matches of the CLABE pattern in the text
                        clabe_matches = re.findall(clabe_pattern, text)
                        
                        if clabe_matches:
                            for bank_code, _ in clabe_matches:
                                if bank_code in BANKS_CODES:
                                    return BANKS_CODES[bank_code]
                    
            return None
        
        except Exception as e:
            raise ValueError(f"Error detecting bank by code: {e}")
    
    @cache
    def detect_bank(self) -> BankName:
        """
        Detect the bank by analyzing the CLABE code or the footer of the document.
        
        Returns:
            BankName: The detected bank name.
        """
        try:
            bank = self.detect_bank_by_code()
            
            # If no bank is found by CLABE code, try to detect it in the footer
            if not bank:
                bank = self.detect_bank_in_footer()
        
        except Exception as e:
            file_name = self.reader.get_file_name()
            raise ValueError(f"Error detecting bank in {file_name}: {e}")
        
        if bank:
            if not isinstance(bank, BankName):
                bank = BankName(bank)
            return bank
        else:
            raise ValueError(f"Bank not detected in {self.reader.get_file_name()}")

    @cache
    def detect_statement_type(self) -> StatementType:
        """
        Detect the statement type by analyzing the credit condition phrase in the document.
        
        Returns:
            StatementType: The detected statement type if found, otherwise 'debit'.
        """
        try:
            extracted_words = self.reader.extract_words()
            credit_condition_phrase = ['límite', 'de', 'crédito']

            # Convert the text column to lowercase and remove colons
            text_column = extracted_words.df['text']
            processed_text = text_column.str.lower().str.replace(':', '', regex=False)

            # If the credit condition phrase is found, return 'credit'
            if search_phrase_in_df(processed_text, credit_condition_phrase, type_return='bool'):
                return StatementType.CREDIT

            # Otherwise, return 'debit'
            return StatementType.DEBIT
        
        except Exception as e:
            raise ValueError(f"Error detecting statement type: {e}")
    
    def _is_new_credit_format(self, bank_properties: BankProperties) -> bool:
        """
        Detects if the statement is in the new credit format. Given the old format statement properties,
        it checks if the start and end phrases are found in the document.
        - If the start and end phrases are found, it returns False, indicating that the statement is in the old format.
        - If the start and end phrases are not found, it returns True, indicating that the statement is in the new format.
        
        Args:
            bank_properties: BankProperties instance to check
        
        Returns:
            bool: True if the statement is in the new credit format, False otherwise.
        """
        try:
            if self.detect_statement_type() == StatementType.DEBIT.value:
                return False
            
            extracted_words = self.reader.extract_words()
            start_phrase = bank_properties.start_phrase
            end_phrase = bank_properties.end_phrase
            
            start_phrase_found = search_phrase_in_df(extracted_words.df, start_phrase, type_return='bool')
            end_phrase_found = search_phrase_in_df(extracted_words.df, end_phrase, type_return='bool')
            
            if not start_phrase_found or not end_phrase_found:
                return True
            else:   
                return False
        except Exception as e:
            raise ValueError(f"Error determining credit format: {e}")
        
    def get_bank_properties(self) -> BankProperties:
        """
        Get the statement properties for a given bank and statement type.
        Uses lazy loading to only load the properties for the detected bank.
        
        Returns:
            BankProperties: The statement properties for the given bank and statement type.
            
        Raises:
            ValueError: If bank or statement type cannot be detected or properties not found
        """
        try:
            bank = self.detect_bank()
            statement_type = self.detect_statement_type()
            
            # For credit statements, we need to check both old and new formats
            if statement_type == StatementType.CREDIT:
                # First try to get old format properties
                old_properties = self.bank_properties_factory.get_bank_properties(bank, statement_type, new_format=False)
                
                if old_properties and self._is_new_credit_format(old_properties):
                    # Try to get new format properties
                    new_properties = self.bank_properties_factory.get_bank_properties(bank, statement_type, new_format=True)
                    if new_properties:
                        return new_properties
                    else:
                        raise ValueError(f"No new format properties found for {bank} credit")
                
                if old_properties:
                    return old_properties
                else:
                    raise ValueError(f"No old format properties found for {bank} credit")
                    
            elif statement_type == StatementType.DEBIT:
                properties = self.bank_properties_factory.get_bank_properties(bank, statement_type, new_format=None)
                
                if properties:
                    return properties
                else:
                    raise ValueError(f"No properties found for {bank} debit")
            else:
                raise ValueError(f"Unsupported statement type: {statement_type}")
                    
        except ValueError as e:
            # Re-raise ValueError as is
            raise e
        except Exception as e:
            raise ValueError(f"Error getting statement properties for bank {bank} and statement type {statement_type}: {e}")