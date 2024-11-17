import re
import pandas as pd
from core import TransactionProcessor, TransactionExtractor
from typing import List, Dict

class BBVADebitTransactionExtractor(TransactionExtractor):
    def extract_month_from_pdf(self, lines: List[str]) -> List[str]:
        '''Implements the month extraction logic for BBVA's debit cards statements, detecting multiple months'''
        detected_months = []
        for line in lines:
            for month in self.month_patterns.values():
                if re.search(rf'\b{month}\b', line) and month not in detected_months:
                    detected_months.append(month)
        return detected_months

    def extract_transactions(self, lines: List[str], detected_months: List[str]) -> List[Dict[str, str]]:
        '''Extracts transactions from the lines of a BBVA debit card statement'''
        transactions = []
        current_transaction = {}

        month_regexes = [re.compile(rf'\s*(\d{{2}}/{month})') for month in detected_months]

        lines = lines[:-2] # Delate footer

        for line in lines:
            if line.strip() == '':
                lines.pop(lines.index(line))

            if re.search(r'\d{2}/[A-Z]{3}', line.strip()):
                lines.pop(lines.index(line)+1)

            if line.strip() == 'Periodo':
                first_day = lines[lines.index(line)+1].split('/')[0].split(' ')[1]
            elif line.strip() == 'Saldo Anterior':
                initial_amount = lines[lines.index(line) + 1].strip()
                initial_balance = {'Date': f'{first_day} {detected_months[0]}', 'Description': 'Saldo inicial', 'Amount': initial_amount}
                transactions.append(initial_balance)

            for month_regex in month_regexes:
                date_match = month_regex.match(line)
                if date_match:
                    if current_transaction:
                        transactions.append(current_transaction)
                        current_transaction = {}

                    if 'Date' not in current_transaction:
                        current_transaction['Date'] = line.strip().replace('/', ' ')
                    break  # Stop checking once a match is found for a month

            if current_transaction:
                if re.match(r'\d{2}/[A-Z]{3}', line.strip()):
                    pass
                elif 'Description' not in current_transaction:
                    current_transaction['Description'] = line.strip()
                elif 'Amount' not in current_transaction and re.match(r'^\d{1,3}(,\d{3})*\.\d{2}$', line.strip()):
                    current_transaction['Amount'] = float(line.strip().replace(',',''))
                elif 'Description' and 'Amount' in current_transaction and not re.match(r'^-?\d{1,3}(,\d{3})*\.\d{2}$', line.strip()):
                    if ' / ' in current_transaction['Description']:
                        pass
                    elif 'RFC' in line.strip() or 'Referencia' in line.strip():
                        pass
                    else:
                        current_transaction['Description'] += ' / ' + line.strip()

        if current_transaction:
            transactions.append(current_transaction)

        return transactions

class BBVADebitTransactionProcessor(TransactionProcessor):
    def process_transactions(self) -> pd.DataFrame:
        pages = self.reader.extract_text_by_page()
        transactions = []
        detected_months = []
        for page in pages:
            detected_months += self.extractor.extract_month_from_pdf(page.split('\n'))
        self.month_abbreviations = sorted(set(detected_months))

        for page in pages:
            lines = page.split('\n')
            transactions += self.extractor.extract_transactions(lines, self.month_abbreviations)

        return pd.DataFrame(transactions)
