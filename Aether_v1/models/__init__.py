# models/__init__.py

from .document_reader import PDFReader
from .bank_detector import DefaultBankDetector

from .bbva import BBVACreditTransactionExtractor, BBVACreditTransactionProcessor, BBVADebitTransactionExtractor, BBVADebitTransactionProcessor
from .nu import NuBankCreditTransactionExtractor, NuBankCreditTransactionProcessor, NuBankDebitTransactionExtractor, NuBankDebitTransactionProcessor
from .citibanamex import CitibanamexCreditTransactionExtractor, CitibanamexCreditTransactionProcessor
from .amex import AmexCreditTransactionExtractor, AmexCreditTransactionProcessor
from .banorte import BanorteCreditTransactionExtractor, BanorteCreditTransactionProcessor, BanorteDebitTransactionExtractor, BanorteDebitTransactionProcessor
from .santander import SantanderCreditTransactionExtractor, SantanderCreditTransactionProcessor, SantanderDebitTransactionExtractor, SantanderDebitTransactionProcessor
from .hsbc import HSBCCreditTransactionExtractor, HSBCCreditTransactionProcessor
from .Inbursa import InbursaCreditTransactionExtractor, InbursaCreditTransactionProcessor, InbursaDebitTransactionExtractor, InbursaDebitTransactionProcessor
## from .general import GeneralCreditTransactionExtractor, GeneralCreditTransactionProcessor

__all__ = ['PDFReader', 'DefaultBankDetector','NuBankCreditTransactionExtractor', 'NuBankCreditTransactionProcessor',
    'NuBankDebitTransactionExtractor', 'NuBankDebitTransactionProcessor',
    'BBVACreditTransactionExtractor', 'BBVACreditTransactionProcessor',
    'BBVADebitTransactionExtractor', 'BBVADebitTransactionProcessor',
    'CitibanamexCreditTransactionExtractor', 'CitibanamexCreditTransactionProcessor',
    'AmexCreditTransactionExtractor', 'AmexCreditTransactionProcessor',
    'BanorteCreditTransactionExtractor', 'BanorteCreditTransactionProcessor',
    'BanorteDebitTransactionExtractor', 'BanorteDebitTransactionProcessor',
    'SantanderCreditTransactionExtractor', 'SantanderCreditTransactionProcessor',
    'SantanderDebitTransactionExtractor', 'SantanderDebitTransactionProcessor',
    'HSBCCreditTransactionExtractor', 'HSBCCreditTransactionProcessor',
    'InbursaCreditTransactionExtractor', 'InbursaCreditTransactionProcessor',
    'InbursaDebitTransactionExtractor', 'InbursaDebitTransactionProcessor']
