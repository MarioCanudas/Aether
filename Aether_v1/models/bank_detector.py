from core import BankDetector
from typing import Literal, List
import re
import pandas as pd
from config import BANKS, STATEMENTS_TYPES
from .propertys_catalog import (
    AMEX_CREDIT_PROPERTYS,
    BANAMEX_DEBIT_PROPERTYS, BANAMEX_CREDIT_PROPERTYS,
    BANORTE_DEBIT_PROPERTYS, BANORTE_CREDIT_PROPERTYS,
    BBVA_DEBIT_PROPERTYS, BBVA_CREDIT_PROPERTYS,
    HSBC_DEBIT_PROPERTYS, HSBC_CREDIT_PROPERTYS,
    INBURSA_DEBIT_PROPERTYS, INBURSA_CREDIT_PROPERTYS,
    NU_DEBIT_PROPERTYS, NU_CREDIT_PROPERTYS,
    SANTANDER_DEBIT_PROPERTYS, SANTANDER_CREDIT_PROPERTYS
)


class DefaultBankDetector(BankDetector):
    def identify_bank_in_footer(self, df_footer: pd.DataFrame, banks_names: List[str]) -> str:
        for bank_name in banks_names:
            pattern = re.escape(bank_name.lower())
            for text in df_footer['text'].str.lower():
                if isinstance(text, str) and re.search(f"^{pattern.lower()}$", text.lower()):
                    return bank_name

        return None

    def detect_bank(self) -> Literal['amex', 'banorte', 'bbva', 'citibanamex', 'hsbc', 'inbursa', 'nu', 'santander']:
        footer_percentage = 0.05
        footer_threshold = self.extracted_words['page_height'].mean() * footer_percentage

        df_footer = self.extracted_words[self.extracted_words['bottom'] > self.extracted_words['page_height'].mean() - footer_threshold]

        detected_bank = self.identify_bank_in_footer(df_footer, BANKS)

        if detected_bank:
            return detected_bank
        else:
            raise ValueError('No bank was identified')

    def detect_statement_type(self) -> Literal['debit', 'credit']:
        credit_condition_phrase = ['límite', 'de', 'crédito']

        for i in range(len(self.extracted_words) - len(credit_condition_phrase)):
            if list(self.extracted_words['text'].iloc[i : i + len(credit_condition_phrase)].str.lower()) == credit_condition_phrase:
                return 'credit'

        return 'debit'

    @property
    def statement_propertys(self):
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
