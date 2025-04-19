from core import BankDetector
from typing import Literal, List
import re
import pandas as pd
from config import BANKS, BANKS_CODES, STATEMENTS_TYPES
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
    def identify_bank_in_footer(self, df_footer: pd.DataFrame, banks_names: List[str]) -> Literal['amex', 'banorte', 'bbva', 'citibanamex', 'hsbc', 'inbursa', 'nu', 'santander']:
        """
        Detect the bank by analyzing the footer of the document.
        This method checks if any of the bank names are present in the footer text.
        
        Args:
            df_footer (pd.DataFrame): DataFrame containing the footer text.
            banks_names (List[str]): List of bank names to check against.
        Returns:
            str: The detected bank name if found, otherwise None.
        """
        footer_text = df_footer['text'].apply(lambda x: x.lower())
        for bank in banks_names:
            bank_lower = bank.lower()
            mask = footer_text.str.contains(f"\\b{re.escape(bank_lower)}\\b", regex=True)
            if mask.any():
                return bank
    
        return None

    def detect_bank_in_footer(self) -> Literal['amex', 'banorte', 'bbva', 'citibanamex', 'hsbc', 'inbursa', 'nu', 'santander']:
        """
        Detect the bank by analyzing the footer of the document.
        
        Returns:
            str: The detected bank name if found, otherwise raises a ValueError.
        """
        document_height = self.document_height
        
        footer_percentage = 0.05
        footer_threshold = document_height * footer_percentage

        df_footer = self.extracted_words[self.extracted_words['bottom'] > document_height - footer_threshold]

        detected_bank = self.identify_bank_in_footer(df_footer, BANKS)

        if detected_bank:
            return detected_bank
        else:
            raise ValueError('No bank was identified')
        
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
                        for bank_code, rest_of_digits in clabe_matches:
                            if bank_code in BANKS_CODES:
                                return BANKS_CODES[bank_code]
                
        return None
    
    def detect_bank(self):
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

    @property
    def statement_propertys(self) -> dict:
        bank = self.detect_bank()
        statement_type = self.detect_statement_type()

        match (bank, statement_type):
            case ('amex', 'credit'):
                return AMEX_CREDIT_PROPERTYS

            case ('banamex', 'debit'):
                return BANAMEX_DEBIT_PROPERTYS

            case ('banamex', 'credit'):
                return BANAMEX_CREDIT_PROPERTYS

            case ('banorte', 'debit'):
                return BANORTE_DEBIT_PROPERTYS

            case ('banorte', 'credit'):
                return BANORTE_CREDIT_PROPERTYS

            case ('bbva', 'debit'):
                return BBVA_DEBIT_PROPERTYS

            case ('bbva', 'credit'):
                return BBVA_CREDIT_PROPERTYS

            case ('hsbc', 'debit'):
                return HSBC_DEBIT_PROPERTYS

            case ('hsbc', 'credit'):
                return HSBC_CREDIT_PROPERTYS

            case ('inbursa', 'debit'):
                return INBURSA_DEBIT_PROPERTYS

            case ('inbursa', 'credit'):
                return INBURSA_CREDIT_PROPERTYS

            case ('nu', 'debit'):
                return NU_DEBIT_PROPERTYS

            case ('nu', 'credit'):
                return NU_CREDIT_PROPERTYS

            case ('santander', 'debit'):
                return SANTANDER_DEBIT_PROPERTYS

            case ('santander', 'credit'):
                return SANTANDER_CREDIT_PROPERTYS

            case _ :
                return None
            
    @property
    def new_credit_satement_propertys(self) -> dict:
        bank = self.detect_bank()
        
        if bank == 'banorte':
            return BANORTE_NEW_CREDIT_FORMAT_PROPERTYS
        elif bank == 'banamex':
            return BANAMEX_NEW_CREDIT_FORMAT_PROPERTYS
        elif bank == 'bbva':
            return BBVA_NEW_CREDIT_FORMAT_PROPERTYS
        else:
            return {}
        