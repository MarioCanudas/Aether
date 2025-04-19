from core import BankDetector
from typing import Literal, List
import re
import pandas as pd
from config import BANKS, BANKS_CODES, STATEMENTS_TYPES
from functools import cached_property
from propertys_catalog import (
    AMEX_CREDIT_PROPERTYS,
    BANAMEX_DEBIT_PROPERTYS, BANAMEX_CREDIT_PROPERTYS, BANAMEX_NEW_CREDIT_FORMAT_PROPERTYS,
    BANORTE_DEBIT_PROPERTYS, BANORTE_CREDIT_PROPERTYS, BANORTE_NEW_CREDIT_FORMAT_PROPERTYS,
    BBVA_DEBIT_PROPERTYS, BBVA_CREDIT_PROPERTYS, BBVA_NEW_CREDIT_FORMAT_PROPERTYS,
    HSBC_DEBIT_PROPERTYS, HSBC_CREDIT_PROPERTYS,
    INBURSA_DEBIT_PROPERTYS, INBURSA_CREDIT_PROPERTYS,
    NU_DEBIT_PROPERTYS, NU_CREDIT_PROPERTYS,
    SANTANDER_DEBIT_PROPERTYS, SANTANDER_CREDIT_PROPERTYS
)


class DefaultBankDetector(BankDetector):
    @cached_property
    def extracted_words(self) -> pd.DataFrame:
        return self.document_reader.extract_words()

    def detect_bank_in_footer(self) -> Literal['amex', 'banorte', 'bbva', 'citibanamex', 'hsbc', 'inbursa', 'nu', 'santander']:
        """
        Detect the bank by analyzing the footer of the document.
        
        Returns:
            str: The detected bank name if found, otherwise raises a ValueError.
        """
        document_height = self.document_reader.get_height()
        
        footer_percentage = 0.05
        footer_threshold = document_height * footer_percentage

        df_footer = self.extracted_words[self.extracted_words['bottom'] > document_height - footer_threshold]

        footer_text = df_footer['text'].apply(lambda x: x.lower())
        for bank in BANKS:
            bank_lower = bank.lower()
            mask = footer_text.str.contains(f"\\b{re.escape(bank_lower)}\\b", regex=True)
            if mask.any():
                return bank
    
        return None
        
    def detect_bank_by_code(self) -> Literal['amex', 'banorte', 'bbva', 'citibanamex', 'hsbc', 'inbursa', 'nu', 'santander']:
        """
        Detect the bank by analyzing the CLABE code in the document.
        
        Returns:
            str: The detected bank name if found, otherwise None.
        """
        df_extracted_words = self.extracted_words.copy()
    
        clabe_keyword = r'\bclabe\b'
        
        clabe_pattern = r'(\d{3})(\d{7,15})?'
        
        mask = df_extracted_words['text'].str.contains(clabe_keyword, regex=True, case=False)
        
        if mask.any():
            clabe_indices = df_extracted_words.index[mask].tolist()
            
            for idx in clabe_indices:
                start_idx = max(0, idx - 5)
                end_idx = min(len(df_extracted_words), idx + 20)
                
                # Extraer texto en ese rango y eliminar espacios
                nearby_text = df_extracted_words.iloc[start_idx:end_idx]['text'].astype(str)
                nearby_text = nearby_text.str.replace(r'\s+', '', regex=True)
                
                for i, text in enumerate(nearby_text):
                    clabe_matches = re.findall(clabe_pattern, text)
                    
                    if clabe_matches:
                        for bank_code, _ in clabe_matches:
                            if bank_code in BANKS_CODES:
                                return BANKS_CODES[bank_code]
                
        return None
    
    def detect_bank(self) -> Literal['amex', 'banorte', 'bbva', 'citibanamex', 'hsbc', 'inbursa', 'nu', 'santander']:
        bank = self.detect_bank_by_code()
        
        if not bank:
            bank = self.detect_bank_in_footer()
            
        return bank

    def detect_statement_type(self) -> Literal['debit', 'credit']:
        credit_condition_phrase = ['límite', 'de', 'crédito']

        text_column = self.extracted_words['text'].copy()

        processed_text = text_column.str.lower().str.replace(':', '', regex=False)

        for i in range(len(processed_text) - len(credit_condition_phrase) + 1):
            current_phrase = list(processed_text.iloc[i : i + len(credit_condition_phrase)])

            if current_phrase == credit_condition_phrase:
                return 'credit'

        return 'debit'

    def get_statement_properties(self, new_credit_format = False) -> dict:
        bank = self.detect_bank()
        statement_type = self.detect_statement_type()

        match (bank, statement_type, new_credit_format):
            case ('amex', 'credit', False):
                return AMEX_CREDIT_PROPERTYS
            
            case ('amex', 'credit', True):
                return {}

            case ('banamex', 'debit', _):
                return BANAMEX_DEBIT_PROPERTYS

            case ('banamex', 'credit', False):
                return BANAMEX_CREDIT_PROPERTYS
            
            case ('banamex', 'credit', True):
                return BANAMEX_NEW_CREDIT_FORMAT_PROPERTYS

            case ('banorte', 'debit', _):
                return BANORTE_DEBIT_PROPERTYS

            case ('banorte', 'credit', False):
                return BANORTE_CREDIT_PROPERTYS
            
            case ('banorte', 'credit', True):
                return BANORTE_NEW_CREDIT_FORMAT_PROPERTYS

            case ('bbva', 'debit', _):
                return BBVA_DEBIT_PROPERTYS

            case ('bbva', 'credit', False):
                return BBVA_CREDIT_PROPERTYS
            
            case ('bbva', 'credit', True):
                return BBVA_NEW_CREDIT_FORMAT_PROPERTYS

            case ('hsbc', 'debit', _):
                return HSBC_DEBIT_PROPERTYS

            case ('hsbc', 'credit', False):
                return HSBC_CREDIT_PROPERTYS
            
            case ('hsbc', 'credit', True):
                return {}

            case ('inbursa', 'debit', _):
                return INBURSA_DEBIT_PROPERTYS

            case ('inbursa', 'credit', False):
                return INBURSA_CREDIT_PROPERTYS
            
            case ('inbursa', 'credit', True):
                return {}

            case ('nu', 'debit', _):
                return NU_DEBIT_PROPERTYS

            case ('nu', 'credit', _):
                return NU_CREDIT_PROPERTYS

            case ('santander', 'debit', _):
                return SANTANDER_DEBIT_PROPERTYS

            case ('santander', 'credit', False):
                return SANTANDER_CREDIT_PROPERTYS
            
            case ('santander', 'credit', True):
                return {}

            case _ :
                return None