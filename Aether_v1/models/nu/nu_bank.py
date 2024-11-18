import re
from core import TransactionProcessor, TransactionExtractor
from typing import List, Dict
import pandas as pd
from datetime import datetime


class NuBankCreditTransactionExtractor(TransactionExtractor):
    def extract_month_from_pdf(self, lines: List[str]) -> List[str]:
        """ Implements the month extraction logic for NuBank, detecting multiple months """
        detected_months = []
        for line in lines:
            # Search for month names or abbreviations in the text
            for month in self.month_patterns.values():
                if re.search(rf'\b{month}\b', line) and month not in detected_months:
                    detected_months.append(month)
        return detected_months

    def extract_transactions(self, lines: List[str]) -> List[Dict[str, str]]:
        transactions = []
        current_transaction = {}

        self.year = self.year or self.detect_year_from_pdf(lines)
        print(self.year)
        # Detect all months from the PDF content
        detected_months = self.extract_month_from_pdf(lines)
        if not detected_months:
            return []

        # Compile regex patterns for all detected months
        month_regexes = [re.compile(rf'\s*(\d{{2}} {month})') for month in detected_months]

        reverse_month_patterns = {v: k for k, v in self.month_patterns.items()}

        for line in lines:
            # Check if the line contains a date with any of the detected months
            for month_regex in month_regexes:
                date_match = month_regex.match(line)

                if date_match:
                    if current_transaction:
                        transactions.append(current_transaction)
                        current_transaction = {}

                    date_parts = date_match.group(1).split(' ')
                    if '' in date_parts:
                        date_parts.remove('')

                    day = date_parts[0].zfill(2)
                    month_abbreviation = date_parts[1].upper()
                    month = reverse_month_patterns.get(month_abbreviation)
                    if not month:
                        raise ValueError(f"Could not find month mapping for abbreviation: {month_abbreviation}")

                    current_transaction['Date'] = f"{self.year}-{datetime.strptime(month, '%B').month:02}-{day}"
                    break

            if current_transaction:
                # Continue building the current transaction
                if re.match(r"\d{2}\s[A-Z]{3}", line.strip()):
                    pass
                elif 'Category' not in current_transaction:
                    current_transaction['Category'] = line.strip()
                elif 'Description' not in current_transaction:
                    current_transaction['Description'] = line.strip()
                elif 'Amount' not in current_transaction and re.match(r'\$[\d,]+\.\d{2}', line.strip()):
                    current_transaction['Amount'] = float(line.strip().replace(',', '').replace('$', ''))

        if current_transaction:
            transactions.append(current_transaction)

        return transactions


class NuBankCreditTransactionProcessor(TransactionProcessor):
    def process_transactions(self) -> pd.DataFrame:
        pages = self.reader.extract_text_by_page()
        transactions = []
        detected_months = []
        for page in pages:
            lines = page.split('\n')
            detected_months += self.extractor.extract_month_from_pdf(lines)
            transactions += self.extractor.extract_transactions(lines)

        self.month_abbreviations = sorted(set(detected_months))

        return pd.DataFrame(transactions)
