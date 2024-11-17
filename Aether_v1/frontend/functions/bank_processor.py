
from models import (
    NuBankCreditTransactionExtractor, NuBankCreditTransactionProcessor,
    NuBankDebitTransactionExtractor, NuBankDebitTransactionProcessor,
    BBVADebitTransactionExtractor, BBVADebitTransactionProcessor,
    BBVACreditTransactionExtractor, BBVACreditTransactionProcessor,
    CitibanamexCreditTransactionExtractor, CitibanamexCreditTransactionProcessor,
    PDFReader
    )

def get_bank_processor(bank_name, statement_type, pdf_path, month_patterns):
    """
    Returns the appropriate processor based on the bank name and statement type.

    Parameters:
    - bank_name: str - The name of the bank (e.g., 'Nu', 'BBVA')
    - statement_type: str - The type of statement ('credit' or 'debit')
    - pdf_path: str - The file path of the PDF statement
    - month_patterns: dict - A dictionary of month patterns for extraction

    Returns:
    - An instance of the relevant TransactionProcessor for the specified bank and statement type
    """
    if bank_name == 'Nu' and statement_type == 'credit':
        extractor = NuBankCreditTransactionExtractor(month_patterns)
        return NuBankCreditTransactionProcessor(PDFReader(pdf_path), extractor)
    elif bank_name == 'Nu' and statement_type == 'debit':
        extractor = NuBankDebitTransactionExtractor(month_patterns)
        return NuBankDebitTransactionProcessor(PDFReader(pdf_path), extractor)
    elif bank_name == 'BBVA' and statement_type == 'credit':
        extractor = BBVACreditTransactionExtractor(month_patterns)
        return BBVACreditTransactionProcessor(PDFReader(pdf_path), extractor)
    elif bank_name == 'BBVA' and statement_type == 'debit':
        extractor = BBVADebitTransactionExtractor(month_patterns)
        return BBVADebitTransactionProcessor(PDFReader(pdf_path), extractor)
    elif bank_name == 'Citibanamex' and statement_type == 'credit':
        extractor = CitibanamexCreditTransactionExtractor(month_patterns)
        return CitibanamexCreditTransactionProcessor(PDFReader(pdf_path), extractor)
    else:
        raise ValueError(f"Unsupported bank or statement type: {bank_name} - {statement_type}")
