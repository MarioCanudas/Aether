import re
import pandas as pd
from typing import Literal
from ..core.interfaces import SpecialDataFiltering

class SpecialDataFiltering(SpecialDataFiltering):
    BANKS_WITH_SPECIAL_DATA = {'nu'}
    
    def filter_nu_transactions(self) -> pd.DataFrame:
        normalized_table = self.normalized_table.copy()
        key_words = ['retiro de cajita', 'depósito en cajita']
        
        pattern = '|'.join(map(re.escape, key_words))
        
        mask = ~normalized_table['description'].str.lower().str.contains(pattern, case=False, regex=True)
        
        return normalized_table[mask]

    def filter_special_data(
            self, 
            bank: Literal['amex', 'banorte', 'bbva', 'citibanamex', 'hsbc', 'inbursa', 'nu', 'santander'], 
            statement_type: Literal['credit', 'debit']
        ) -> pd.DataFrame:
        match (bank, statement_type):
            case ('nu', 'debit'):
                return self.filter_nu_transactions()
            case _:
                return self.normalized_table