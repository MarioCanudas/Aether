import os
from models import NuBankTransactionExtractor, NuBankTransactionProcessor, PDFReader
from config import INPUTS_FOLDER, OUTPUTS_FOLDER, DEFAULT_BANK, MONTH_PATTERNS

def get_bank_processor(bank_name, pdf_path, month_patterns):
    if bank_name == 'Nu':
        extractor = NuBankTransactionExtractor(month_patterns)
        return NuBankTransactionProcessor(PDFReader(pdf_path), extractor)
    else:
        raise ValueError(f"Unsupported bank: {bank_name}")

if __name__ == "__main__":
    # Example usage with dynamic paths from the config
    bank_name = DEFAULT_BANK
    input_file = os.path.join(INPUTS_FOLDER, 'test_files/nu_bank_statement.pdf')

    # Process the transactions
    processor = get_bank_processor(bank_name, input_file, MONTH_PATTERNS)
    transactions_df = processor.process_transactions()

    # Detect months from the PDF and generate the dynamic output file name
    detected_months = processor.extractor.extract_month_from_pdf(processor.reader.extract_text_by_page())[0].split('\n')
    month_str = "_".join(sorted(set(detected_months)))  # Combine unique months into a string

    # Generate output file name dynamically based on detected months
    output_file = os.path.join(OUTPUTS_FOLDER, f'transactions_{bank_name}_{month_str}.csv')

    # Save the DataFrame to CSV
    transactions_df.to_csv(output_file, index=False)

    print(f"Transactions saved to {output_file}")
