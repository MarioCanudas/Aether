import os
import pandas as pd
from models import NuBankTransactionExtractor, NuBankTransactionProcessor
from core import DocumentReader
from config import INPUTS_FOLDER, OUTPUTS_FOLDER, DEFAULT_BANK, MONTH_PATTERNS

def get_bank_processor(bank_name, pdf_path, month_patterns):
    if bank_name == 'Nu':
        extractor = NuBankTransactionExtractor(month_patterns)
        return NuBankTransactionProcessor(DocumentReader(pdf_path), extractor)
    else:
        raise ValueError(f"Unsupported bank: {bank_name}")

if __name__ == "__main__":
    # Example usage with dynamic paths from the config
    bank_name = DEFAULT_BANK
    input_file = os.path.join(INPUTS_FOLDER, 'nu_bank_statement.pdf')
    output_file = os.path.join(OUTPUTS_FOLDER, f'transactions_{bank_name}_may.csv')

    # Process the transactions and save them to the output folder
    processor = get_bank_processor(bank_name, input_file, MONTH_PATTERNS)
    transactions_df = processor.process_transactions('may')
    transactions_df.to_csv(output_file, index=False)

    print(f"Transactions saved to {output_file}")
