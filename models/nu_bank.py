import re
from core import TransactionProcessor, TransactionExtractor
from typing import List, Dict
import pandas as pd

class NuBankTransactionExtractor(TransactionExtractor):
    def extract_transactions(self, lines: List[str], month: str) -> List[Dict[str, str]]:
        transactions = []
        current_transaction = {}

        month_pattern = self.month_patterns.get(month.lower(), month)

        for line in lines:
            # Check for a date with the specified month, indicating the start of a transaction
            date_match = re.match(rf'\s*(\d{{2}} {month_pattern})', line)
            if date_match:
                if current_transaction:
                    transactions.append(current_transaction)
                    current_transaction = {}

                current_transaction['Date'] = date_match.group(1)
            elif current_transaction:
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
