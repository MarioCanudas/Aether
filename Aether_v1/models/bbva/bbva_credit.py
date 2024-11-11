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

            for number, abbreviation in self.month_patterns.items(): # Should be NUMERIC_MONTH_PATTERN
                if re.fullmatch(rf'\b\d{{2}}/{number}/\d{{2}}\b', line.strip()):
                    detected_months.append((number, abbreviation))

        return detected_months

    def extract_transactions(self, lines: List[str]) -> List[Dict[str, str]]:
        ''''Implements the transaction extraction logic for BBVA's credit cards statements'''
        transactions = []
        current_transaction = {}

        detected_months = self.extract_month_from_pdf(lines)
        if not detected_months:
            return []

        month_regexes = [re.compile(rf'\b\d{{2}}/{month[0]}/\d{{2}}\b') for month in detected_months]

        lines = lines[:-3] # Delate footer

        for line in lines:
            if line.strip() == 'Fecha de Corte' or line.strip() == 'Fecha Límite de Pago':
                lines.pop(lines.index(line) + 1)

            if re.match(r"\d{2}/\d{2}/\d{2}", line.strip()):
                lines.pop(lines.index(line)+1)

            for month_regex in month_regexes:
                date_match = month_regex.match(line)
                if date_match:
                    if current_transaction:
                        transactions.append(current_transaction)
                        current_transaction = {}

                    day, month = line.strip().split('/')[0:2]
                    current_transaction['Date'] = f'{day} {self.month_patterns.get(month)}'
                    break  # Stop checking once a match is found for a month

            if current_transaction:
                if re.match(r"\d{2}/\d{2}/\d{2}", line.strip()):
                    pass
                elif 'Description' not in current_transaction:
                    current_transaction['Description'] = line.strip()
                elif 'Amount' not in current_transaction and re.match(r'^\d{1,3}(,\d{3})*\.\d{2}-?$', line.strip()):
                    current_transaction['Amount'] = float(line.strip().replace(',','')) if re.match(r'^\d{1,3}(,\d{3})*\.\d{2}$', line.strip()) else float('-'+line.strip().replace(',','').replace('-',''))
                elif 'Description' in current_transaction and 'Amount' in current_transaction and not re.match(r'^\d{1,3}(,\d{3})*\.\d{2}-?$', line.strip()):
                    if ' / ' in current_transaction['Description'] or re.search(r"(\w+):\$?\s*(\d{1,3}(,\d{3})*\.\d{2})?", line.strip()):
                        pass
                    elif re.match(r"^\$? \d{1,3}(,\d{3})*\.\d{2}$", line.strip()) or 'R.F.C.' in line.strip():
                        pass
                    elif re.match(r'^\w+(?:\s+\w+)*$', line.strip()) or re.match(r'^\w+(?:\s+\w+)*\s+\d{4}\s+\d{4}\s+\d{4}\s+\d{4}$', line.strip()):
                        pass
                    else:
                        current_transaction['Description'] += ' / ' + line.strip()

        if current_transaction:
            transactions.append(current_transaction) if current_transaction['Description'] != 'PUNTOS BBVA' else None

        return transactions

class BBVACreditTransactionProcessor(TransactionProcessor):
    def process_transactions(self) -> pd.DataFrame:
        pages = self.reader.extract_text_by_page()
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
