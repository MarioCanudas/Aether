import re
from core import TransactionProcessor, TransactionExtractor
from typing import List, Dict
import pandas as pd

class NuBankTransactionExtractor(TransactionExtractor):
    def extract_transactions(self, lines: List[str], months: List[str]) -> List[Dict[str, str]]:
        transactions = []
        current_transaction = {}

        # Compile regex patterns for each month
        month_regexes = [re.compile(rf'\s*(\d{{2}} {self.month_patterns[month.lower()]})') for month in months]

        for line in lines:
            # Check if the line contains a date with any of the specified months
            for month_regex in month_regexes:
                date_match = month_regex.match(line)
                if date_match:
                    if current_transaction:
                        transactions.append(current_transaction)
                        current_transaction = {}

                    current_transaction['Date'] = date_match.group(1)
                    break  # Found the date, no need to check other month patterns

            if current_transaction:
                # Continue building the current transaction
                if 'Category' not in current_transaction:
                    current_transaction['Category'] = line.strip()
                elif 'Description' not in current_transaction:
                    current_transaction['Description'] = line.strip()
                elif 'Amount' not in current_transaction and re.match(r'\$[\d,]+\.\d{2}', line.strip()):
                    current_transaction['Amount'] = line.strip()

        if current_transaction:
            transactions.append(current_transaction)

        return transactions

class NuBankTransactionProcessor(TransactionProcessor):
    def process_transactions(self, month: str) -> pd.DataFrame:
        pages = self.reader.extract_text_by_page()
        transactions = []
        for page in pages:
            lines = page.split('\n')
            transactions += self.extractor.extract_transactions(lines, month)
        return pd.DataFrame(transactions)
