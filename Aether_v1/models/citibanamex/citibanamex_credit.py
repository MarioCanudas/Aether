import re
import pandas as pd
from core import TransactionProcessor, TransactionExtractor
from typing import List, Dict
from datetime import datetime


class CitibanamexCreditTransactionExtractor(TransactionExtractor):
    def extract_month_from_pdf(self, lines: List[str]) -> List[str]:
        detected_months = []
        for line in lines:
            if line.strip() == 'Detalle de Pagos Interbancarios realizados a través del SPEI':
                break
            for month in self.month_patterns.values():
                if re.search(rf"^{month}\b", line.strip().upper()):
                    detected_months.append(month)
        return detected_months

    def extract_transactions(self, lines: List[str]) -> List[Dict[str, str]]:
        transactions = []
        current_transaction = {}

        detected_months = self.extract_month_from_pdf(lines)
        # Detect the year from the lines
        self.year = self.year or self.detect_year_from_pdf(lines)
        if not detected_months:
            return []

        month_regexes = [re.compile(rf'^{month.lower().capitalize()}\s+\d{{1,2}}') for month in detected_months]

        reverse_month_patterns = {v: k for k, v in self.month_patterns.items()}

        for line in lines:
            if line.strip() == 'Detalle de Pagos Interbancarios realizados a través del SPEI':
                break
            if re.match(r'^\d{1,3}(,\d{3})*\.\d{2}-$', line.strip()):
                line = '-' + (line.strip().replace('-',''))
            for month_regex in month_regexes:
                date_match = month_regex.search(line.strip())
                if date_match:
                    if current_transaction:
                        transactions.append(current_transaction)
                        current_transaction = {}

                    date_parts = line.strip().split(' ')
                    if '' in date_parts:
                        date_parts.remove('')

                    day = date_parts[1].zfill(2)
                    month_abbreviation = date_parts[0].upper()
                    month = reverse_month_patterns.get(month_abbreviation)
                    if not month:
                        raise ValueError(f"Could not find month mapping for abbreviation: {month_abbreviation}")

                    current_transaction['Date'] = f"{self.year}-{datetime.strptime(month, '%B').month:02}-{day}"
                    break

            if current_transaction:
                if re.match(r"^[A-Za-z]{3}\s+\d{1,2}", line.strip()):
                    pass
                elif 'Description' not in current_transaction:
                    current_transaction['Description'] = re.sub(r'\s{2,}.*', '', line.strip()) # Description /
                elif 'Amount' not in current_transaction and re.match(r'^-?\d{1,3}(,\d{3})*\.\d{2}$', line.strip()):
                    current_transaction['Amount'] = float(line.strip().replace(',',''))

        if current_transaction:
            transactions.append(current_transaction)

        return transactions

class CitibanamexCreditTransactionProcessor(TransactionProcessor):
    def process_transactions(self):
        pages = self.reader.extract_text_by_page()
        transactions = []
        detected_months = []
        for page in pages:
            lines = page.split('\n')
            detected_months += self.extractor.extract_month_from_pdf(lines)
            transactions += self.extractor.extract_transactions(lines)

        self.month_abbreviations = sorted(set(detected_months))

        return pd.DataFrame(transactions)
