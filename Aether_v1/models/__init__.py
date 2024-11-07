# models/__init__.py

from .document_reader import PDFReader
from .nu_bank import NuBankCreditTransactionExtractor, NuBankCreditTransactionProcessor
from .nu_bank_debit import NuBankDebitTransactionExtractor, NuBankDebitTransactionProcessor
from .bbva_credit import BBVACreditTransactionExtractor, BBVACreditTransactionProcessor
from .bbva_debit import BBVADebitTransactionExtractor, BBVADebitTransactionProcessor

__all__ = [
    'PDFReader', 
    'NuBankCreditTransactionExtractor', 'NuBankCreditTransactionProcessor',
    'NuBankDebitTransactionExtractor', 'NuBankDebitTransactionProcessor',
    'BBVACreditTransactionExtractor', 'BBVACreditTransactionProcessor',
    'BBVADebitTransactionExtractor','BBVADebitTransactionProcessor'
    ]
