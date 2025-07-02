import re
from functools import cache
from typing import Literal
from _core import DocumentAnalyzer
from config import BANKS, BANKS_CODES
from utils import search_phrase_in_df
from .banks_properties import (
    AMEX_CREDIT_PROPERTIES,
    BANAMEX_CREDIT_PROPERTIES, BANAMEX_DEBIT_PROPERTIES, BANAMEX_NEW_CREDIT_FORMAT_PROPERTIES,
    BANORTE_CREDIT_PROPERTIES, BANORTE_DEBIT_PROPERTIES, BANORTE_NEW_CREDIT_FORMAT_PROPERTIES,
    BBVA_CREDIT_PROPERTIES, BBVA_DEBIT_PROPERTIES, BBVA_NEW_CREDIT_FORMAT_PROPERTIES,
    HSBC_CREDIT_PROPERTIES, HSBC_DEBIT_PROPERTIES,
    INBURSA_CREDIT_PROPERTIES, INBURSA_DEBIT_PROPERTIES,
    NU_CREDIT_PROPERTIES, NU_DEBIT_PROPERTIES,
    SANTANDER_CREDIT_PROPERTIES, SANTANDER_DEBIT_PROPERTIES,
)
       
class DefaultDocumentAnalyzer(DocumentAnalyzer):
    """
    A class that detects the bank metadata of a given document.

    Args:
        document_reader (DocumentReader): A document reader object.
    """
    
    def detect_bank_in_footer(self) -> Literal['amex', 'banorte', 'bbva', 'citibanamex', 'hsbc', 'inbursa', 'nu', 'santander']:
        """
        Detect the bank by analyzing the footer of the document.
        
        Returns:
            str: The detected bank name if found, otherwise raises a ValueError.
        """
        df_extracted_words = self.reader.extract_words()
        document_height = self.reader.get_height() # Get height to determine the footer threshold
        
        footer_percentage = 0.15
        footer_threshold = document_height * footer_percentage # Calculate the footer threshold using 15% of the document height

        df_footer = df_extracted_words[df_extracted_words['bottom'] > document_height - footer_threshold] # Filter the rows that are in the footer

        # Convert all footer text to lowercase for case-insensitive searches
        footer_text = df_footer['text'].apply(lambda x: x.lower())
        
        # Iterate through all known banks to search for matches
        for bank in BANKS:
            # Create a boolean mask that searches for the bank name as a complete word
            # \b = word boundary to avoid partial matches
            # re.escape() escapes special characters in the bank name
            # regex=True enables the use of regular expressions
            mask = footer_text.str.contains(f"\\b{re.escape(bank)}\\b", regex=True)
            
            # If at least one match of the bank is found in the footer
            if mask.any():
                return bank
        
        # Special case for Nu credit, because the document dosen't have a footer either CLABE
        if search_phrase_in_df(df_extracted_words, ['nu', 'méxico', 'financiera,'], type_return='bool'):
            return 'nu'
    
        return None
        
    def detect_bank_by_code(self) -> Literal['amex', 'banorte', 'bbva', 'citibanamex', 'hsbc', 'inbursa', 'nu', 'santander']:
        """
        Detect the bank by analyzing the CLABE code in the document.
        
        Returns:
            str: The detected bank name if found, otherwise None.
        """
        df_extracted_words = self.reader.extract_words()
    
        clabe_keyword = r'\bclabe\b'
        
        clabe_pattern = r'(\d{3})(\d{7,15})?'
        
        # Create a boolean Series (mask) that searches for the CLABE keyword in the text column
        mask = df_extracted_words['text'].str.contains(clabe_keyword, regex=True, case=False)
        
        if mask.any():
            # Get the indices of the rows where the CLABE keyword is found
            clabe_indices = df_extracted_words.index[mask].tolist()
            
            for idx in clabe_indices:
                # Determine the range of the nearest text to the CLABE keyword
                start_idx = max(0, idx - 5)
                end_idx = min(len(df_extracted_words), idx + 20)
                
                # Extract text in that range and remove spaces
                nearby_text = df_extracted_words.iloc[start_idx:end_idx]['text'].astype(str)
                nearby_text = nearby_text.str.replace(r'\s+', '', regex=True) # Remove spaces
                
                for text in nearby_text:
                    # Find all matches of the CLABE pattern in the text
                    clabe_matches = re.findall(clabe_pattern, text)
                    
                    if clabe_matches:
                        for bank_code, _ in clabe_matches:
                            if bank_code in BANKS_CODES:
                                return BANKS_CODES[bank_code]
                
        return None
    
    @cache
    def detect_bank(self) -> Literal['amex', 'banorte', 'bbva', 'citibanamex', 'hsbc', 'inbursa', 'nu', 'santander']:
        """
        Detect the bank by analyzing the CLABE code or the footer of the document.
        
        Returns:
            str: The detected bank name if found, otherwise None.
        """
        bank = self.detect_bank_by_code()
        
        # If no bank is found by CLABE code, try to detect it in the footer
        if not bank:
            bank = self.detect_bank_in_footer()
            
        return bank

    @cache
    def detect_statement_type(self) -> Literal['debit', 'credit']:
        """
        Detect the statement type by analyzing the credit condition phrase in the document.
        
        Returns:
            str: The detected statement type if found, otherwise 'debit'.
        """
        df_extracted_words = self.reader.extract_words()
        credit_condition_phrase = ['límite', 'de', 'crédito']

        # Convert the text column to lowercase and remove colons
        text_column = df_extracted_words['text']
        processed_text = text_column.str.lower().str.replace(':', '', regex=False)

        # If the credit condition phrase is found, return 'credit'
        if search_phrase_in_df(processed_text, credit_condition_phrase, type_return='bool'):
            return 'credit'

        # Otherwise, return 'debit'
        return 'debit'
    
    def detect_new_credit_format(self, statement_properties: dict) -> bool:
        """
        Detects if the statement is in the new credit format.
        
        Returns:
            bool: True if the statement is in the new credit format, False otherwise.
        """
        if self.detect_statement_type() == 'debit':
            return False
        
        extracted_words = self.reader.extract_words()
        start_phrase = statement_properties['start_phrase']
        end_phrase = statement_properties['end_phrase']
        
        start_phrase_found = search_phrase_in_df(extracted_words, start_phrase, type_return='bool')
        end_phrase_found = search_phrase_in_df(extracted_words, end_phrase, type_return='bool')
        
        return start_phrase_found and end_phrase_found
        
    @cache
    def get_statement_properties(self) -> dict:
        """
        Get the statement properties for a given bank and statement type.
        
        Returns:
            dict: The statement properties for the given bank and statement type.
        """
        bank = self.detect_bank()
        statement_type = self.detect_statement_type()

        match (bank, statement_type):
            case ('amex', 'credit'):
                if self.detect_new_credit_format(AMEX_CREDIT_PROPERTIES):
                    return {} # TODO: Get new credit format properties
                else:
                    return AMEX_CREDIT_PROPERTIES

            case ('banamex', 'debit'):
                return BANAMEX_DEBIT_PROPERTIES

            case ('banamex', 'credit'):
                if self.detect_new_credit_format(BANAMEX_CREDIT_PROPERTIES):
                    return BANAMEX_NEW_CREDIT_FORMAT_PROPERTIES
                else:
                    return BANAMEX_CREDIT_PROPERTIES

            case ('banorte', 'debit'):
                return BANORTE_DEBIT_PROPERTIES

            case ('banorte', 'credit'):
                if self.detect_new_credit_format(BANORTE_CREDIT_PROPERTIES):
                    return BANAMEX_NEW_CREDIT_FORMAT_PROPERTIES
                else:
                    return BANORTE_CREDIT_PROPERTIES

            case ('bbva', 'debit'):
                return BBVA_DEBIT_PROPERTIES

            case ('bbva', 'credit'):
                if self.detect_new_credit_format(BBVA_CREDIT_PROPERTIES):
                    return BBVA_NEW_CREDIT_FORMAT_PROPERTIES
                else: 
                    return BBVA_CREDIT_PROPERTIES

            case ('hsbc', 'debit'):
                return HSBC_DEBIT_PROPERTIES

            case ('hsbc', 'credit'):
                if self.detect_new_credit_format(HSBC_CREDIT_PROPERTIES):
                    return {} # TODO: Get new credit format properties
                else:
                    return HSBC_CREDIT_PROPERTIES

            case ('inbursa', 'debit'):
                return INBURSA_DEBIT_PROPERTIES

            case ('inbursa', 'credit'):
                if self.detect_new_credit_format(INBURSA_CREDIT_PROPERTIES):
                    return {} # TODO: Get new credit format properties
                else:
                    return INBURSA_CREDIT_PROPERTIES

            case ('nu', 'debit'):
                return NU_DEBIT_PROPERTIES

            case ('nu', 'credit'):
                return NU_CREDIT_PROPERTIES

            case ('santander', 'debit'):
                return SANTANDER_DEBIT_PROPERTIES

            case ('santander', 'credit'):
                if self.detect_new_credit_format(SANTANDER_CREDIT_PROPERTIES):
                    return {} # TODO: Get new credit format properties
                else:
                    return SANTANDER_CREDIT_PROPERTIES

            case _ :
                return None