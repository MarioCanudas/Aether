import re
from core import TransactionProcessor, TransactionExtractor
from typing import List, Dict
import pandas as pd

class NuBankTransactionExtractor(TransactionExtractor):
    def extract_month_from_pdf(self, lines: List[str]) -> List[str]:
        """ Implements the month extraction logic for NuBank, detecting multiple months """
        detected_months = []
        for line in lines:
            # Search for month names or abbreviations in the text
            for month in self.month_patterns.values():
                if month in line and month not in detected_months:
                    detected_months.append(month)
        return detected_months

    def extract_transactions(self, lines: List[str]) -> List[Dict[str, str]]:
        transactions = []
        current_transaction = {}

        # Detect all months from the PDF content
        detected_months = self.extract_month_from_pdf(lines)
        if not detected_months:
            return []

        # Compile regex patterns for all detected months
        month_regexes = [re.compile(rf'\s*(\d{{2}} {month})') for month in detected_months]

        for line in lines:
            # Check if the line contains a date with any of the detected months
            for month_regex in month_regexes:
                date_match = month_regex.match(line)
                if date_match:
                    if current_transaction:
                        transactions.append(current_transaction)
                        current_transaction = {}

                    current_transaction['Date'] = date_match.group(1)
                    break  # Stop checking once a match is found for a month

            if current_transaction:
                # Continue building the current transaction
                if re.match(r"\d{2}\s[A-Z]{3}", line.strip()):
                    pass
                elif 'Category' not in current_transaction:
                    current_transaction['Category'] = line.strip()
                elif 'Description' not in current_transaction:
                    current_transaction['Description'] = line.strip()
                elif 'Amount' not in current_transaction and re.match(r'\$[\d,]+\.\d{2}', line.strip()):
                    current_transaction['Amount'] = line.strip()

        if current_transaction:
            transactions.append(current_transaction)

        return transactions

class NuBankTransactionProcessor(TransactionProcessor):
    def process_transactions(self) -> pd.DataFrame:
        pages = self.reader.extract_text_by_page()
        transactions = []
        for page in pages:
            lines = page.split('\n')
            transactions += self.extractor.extract_transactions(lines)
        return pd.DataFrame(transactions)
