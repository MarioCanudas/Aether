import os
from models import (
    NuBankCreditTransactionExtractor, NuBankCreditTransactionProcessor,
    NuBankDebitTransactionExtractor, NuBankDebitTransactionProcessor,
    BBVADebitTransactionExtractor, BBVADebitTransactionProcessor,
    BBVACreditTransactionExtractor, BBVACreditTransactionProcessor,
    CitibanamexCreditTransactionExtractor, CitibanamexCreditTransactionProcessor,
    AmexCreditTransactionExtractor, AmexCreditTransactionProcessor,
    PDFReader
    )
from config import INPUTS_FOLDER, OUTPUTS_FOLDER, DEFAULT_BANK, DEFAULT_STATEMENT_TYPE, MONTH_PATTERNS_ENG, MONTH_PATTERNS_SPA, NUMERIC_MONTH_PATTERNS

import os

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
    elif bank_name == 'Citibanamex' and statement_type == 'credit':
        extractor = CitibanamexCreditTransactionExtractor(month_patterns)
        return CitibanamexCreditTransactionProcessor(PDFReader(pdf_path), extractor)
    elif bank_name == 'BBVA' and statement_type == 'debit':
        extractor = BBVADebitTransactionExtractor(month_patterns)
        return BBVADebitTransactionProcessor(PDFReader(pdf_path), extractor)
    elif bank_name == 'Amex' and statement_type == 'credit':
        extractor = AmexCreditTransactionExtractor(month_patterns)
        return AmexCreditTransactionProcessor(PDFReader(pdf_path), extractor)
    else:
        raise ValueError(f"Unsupported bank or statement type: {bank_name} - {statement_type}")

if __name__ == "__main__":
    # Example usage with dynamic paths from the config
    bank_name = 'Amex'
    statement_type = DEFAULT_STATEMENT_TYPE
    input_file = os.path.join(INPUTS_FOLDER, 'test_files/amex_credit_statement.pdf')

    # Process the transactions
    try:
        processor = get_bank_processor(bank_name, statement_type, input_file, MONTH_PATTERNS_SPA)
        transactions_df = processor.process_transactions()

        # Extract unique months from the processor for file naming
        month_str = "_".join(sorted(set(processor.month_abbreviations)))  # Combine unique months into a string

        # Generate output file name dynamically based on detected months
        output_file = os.path.join(OUTPUTS_FOLDER, f'transactions_{bank_name}_{statement_type}_{month_str}.csv')

        # Save the DataFrame to CSV
        transactions_df.to_csv(output_file, index=False)
        print(f"Transactions saved to {output_file}")
    except ValueError as e:
        print(f"Error: {e}")
