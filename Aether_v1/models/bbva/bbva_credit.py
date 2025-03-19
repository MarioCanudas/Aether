import re
import pandas as pd
from core import TransactionProcessor, TransactionExtractor
from typing import List, Dict, Tuple

class BBVACreditTransactionExtractor(TransactionExtractor):
    def extract_month_from_pdf(self, lines: List[str]) -> List[Tuple[str, str]]:
        '''Implements the month extraction logic for BBVA's credit cards statements, detecting multiple months'''
        detected_months = []
        for line in lines:
            if line.strip() == 'Fecha de Corte' or line.strip() == 'Fecha Límite de Pago':
                lines.pop(lines.index(line) + 1)

            for number, abbreviation in self.month_patterns.items():
                if re.fullmatch(rf'\b\d{{2}}/{number}/\d{{2}}\b', line.strip()):
                    detected_months.append((number, abbreviation))

        return detected_months

    def extract_transactions(self, lines: List[str]) -> List[Dict[str, str]]:
        """
        Extracts transactions from BBVA credit card statements.

        Parameters:
        - lines (List[str]): Extracted text lines from the PDF.

        Returns:
        - List[Dict[str, str]]: List of extracted transactions with 'Date', 'Description', and 'Amount'.
        """
        transactions = []
        current_transaction = {}

        # Preprocess lines: Clean whitespace and filter out unnecessary lines
        cleaned_lines = [line.strip() for line in lines if line.strip()]

        # Detect months in the document
        detected_months = self.extract_month_from_pdf(cleaned_lines)
        if not detected_months:
            return []  # No valid months detected, return empty

        # Compile regex for detected months
        month_regexes = [re.compile(rf"\b\d{{2}}/{month[0]}/\d{{2}}\b") for month in detected_months]

        # Process each line
        for line in cleaned_lines:
            # Match line with a date pattern
            for month_regex in month_regexes:
                if month_regex.match(line):
                    # Save the current transaction if it exists
                    if current_transaction:
                        transactions.append(current_transaction)
                        current_transaction = {}

                    # Extract and format the date
                    day, month, year = line.split('/')
                    current_transaction['Date'] = f"20{year}-{month}-{day}"
                    break  # Exit the loop after matching a date

            # Process the current transaction's details
            if current_transaction:
                # Match descriptions and amounts
                if 'Description' not in current_transaction:
                    current_transaction['Description'] = line
                elif 'Amount' not in current_transaction and re.match(r'^\d{1,3}(,\d{3})*\.\d{2}-?$', line):
                    current_transaction['Amount'] = (
                        float(line.replace(',', '').replace('-', '')) * (1 if '-' in line else -1)
                    )
                    if current_transaction['Amount'] > 0:
                        current_transaction['Type'] = 'Abono'
                    else:
                        current_transaction['Type'] = 'Cargo'
                else:
                    # If it's additional description text, append it
                    current_transaction['Description'] += f" / {line}"

        # Append the last transaction if it exists
        if current_transaction:
            transactions.append(current_transaction)

        # Filter out invalid transactions (e.g., incomplete or unwanted entries)
        transactions = [
            txn for txn in transactions if 'Date' in txn and 'Description' in txn and 'Amount' in txn
        ]

        return transactions


class BBVACreditTransactionProcessor(TransactionProcessor):
    def process_transactions(self) -> pd.DataFrame:
        pages = self.reader.extract_text_by_page()
        print(pages)
        transactions = []
        detected_months = []
        for page in pages:
            lines = page.split('\n')
            detected_months += self.extractor.extract_month_from_pdf(lines)
            transactions += self.extractor.extract_transactions(lines)
        self.month_abbreviations = []
        for month in sorted(set(detected_months)):
            self.month_abbreviations.append(month[1])

        return pd.DataFrame(transactions)
