# models/bbva/__init__.py

from .bbva_credit import BBVACreditTransactionExtractor, BBVACreditTransactionProcessor
from .bbva_debit import BBVADebitTransactionExtractor, BBVADebitTransactionProcessor

__all__ = [
    'BBVACreditTransactionExtractor', 'BBVACreditTransactionProcessor',
    'BBVADebitTransactionExtractor','BBVADebitTransactionProcessor'
    ]
