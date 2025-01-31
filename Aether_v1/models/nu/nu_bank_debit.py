from datetime import datetime
import re
from core import TransactionProcessor, TransactionExtractor
from typing import List, Dict
import pandas as pd

class NuBankDebitTransactionExtractor(TransactionExtractor):
    def classify_words_from_page(self):
        pass
    
    def extract_month_from_pdf(self, lines: List[str]) -> List[str]:
        '''Implements the month extraction logic for NuBank's debit cards statements, detecting multiple months'''
        detected_months = []
        for line in lines:
            for month in self.month_patterns.values():
                if re.search(rf'\b{month}\b', line) and month not in detected_months:
                    detected_months.append(month)
        return detected_months

    def extract_transactions(self, lines: List[str]) -> List[Dict[str, str]]:
        '''Extracts transactions from the lines of a NuBank debit card statement'''
        transactions = []
        current_transaction = {}

        self.year = self.year or self.detect_year_from_pdf(lines)

        # Detect all months from the PDF content
        detected_months = self.extract_month_from_pdf(lines)
        reverse_month_patterns = {v: k for k, v in self.month_patterns.items()}

        if not detected_months:
            if '1 de' in lines[-2]:
                for line in lines:
                    if 'Periodo:' in line.strip():
                        first_day = line.strip().split(' ')[2].strip()
                        detected_month = reverse_month_patterns.get(line.strip().split(' ')[5].strip().upper())
                    elif 'Saldo inicial' == line.strip():
                        initial_amount = float(lines[lines.index(line) + 1].strip().replace(',', '').replace('$', ''))
                        initial_balance = {'Date': f"{self.year}-{datetime.strptime(detected_month, '%B').month:02}-{first_day}", 'Description': 'Saldo inicial', 'Amount': initial_amount}
                        transactions.append(initial_balance)
                    elif 'Dinero generado este mes' == line.strip():
                        generate_amount = float(lines[lines.index(line) + 1].strip().replace(',', '').replace('$', ''))
                        generate_balance = {'Date': f"{self.year}-{datetime.strptime(detected_month, '%B').month:02}-{first_day}", 'Description': 'Dinero generado este mes', 'Amount': generate_amount}
                        transactions.append(generate_balance)
                        break
            return transactions

        # Compile regex patterns for all detected months
        if detected_months:
            month_regexes = [re.compile(rf'\s*(\d{{2}} {month}) \d{{4}}') for month in detected_months]

        for line in lines:
            if line.strip() == 'Detalle de movimientos de tus cajitas':
                break
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

                    break  # Stop checking once a match is found for a month

            if current_transaction:
                # Continue building the current transaction
                if re.match(r'\d{2}\s[A-Z]{3}\s\d{4}', line.strip()):
                    pass
                elif 'Description' not in current_transaction:
                    current_transaction['Description'] = re.sub(r'\s+', ' ', line.strip())
                elif 'Amount' not in current_transaction and re.match(r'[+-]?\$[\d,]+\.\d{2}', line.strip()):
                    current_transaction['Amount'] = float(line.strip().replace(',','').replace('$', ''))
                    if current_transaction['Amount'] < 0:
                        current_transaction['Type'] = 'Cargo'
                    else:
                        current_transaction['Type'] = 'Abono'

        if current_transaction:
            transactions.append(current_transaction)

        return transactions

class NuBankDebitTransactionProcessor(TransactionProcessor):
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
