import re
from core import TransactionProcessor, TransactionExtractor
from typing import List, Dict
import pandas as pd

class NuBankDebitTransactionExtractor(TransactionExtractor):
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
        
        # Detect all months from the PDF content
        detected_months = self.extract_month_from_pdf(lines)
        if not detected_months:
            if '1 de' in lines[-2]:
                for line in lines:
                    if 'Periodo:' in line.strip():
                        first_day = line.strip().split(' ')[2].strip()
                        detected_month = line.strip().split(' ')[5].strip().upper()
                    elif 'Saldo inicial' == line.strip():
                        initial_amount = float(lines[lines.index(line) + 1].strip().replace(',', '').replace('$', ''))
                        initial_balance = {'Date': f'{first_day} {detected_month}', 'Description': 'Saldo inicial', 'Amount': initial_amount}
                        transactions.append(initial_balance)
                    elif 'Dinero generado este mes' == line.strip():
                        generate_amount = float(lines[lines.index(line) + 1].strip().replace(',', '').replace('$', ''))
                        generate_balance = {'Date': f'{first_day} {detected_month}', 'Description': 'Dinero generado este mes', 'Amount': generate_amount}
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
                        
                    current_transaction['Date'] = date_match.group(1)
                    break  # Stop checking once a match is found for a month
            
            if current_transaction:
                # Continue building the current transaction
                if re.match(r'\d{2}\s[A-Z]{3}\s\d{4}', line.strip()):
                    pass
                elif 'Description' not in current_transaction:
                    current_transaction['Description'] = re.sub(r'\s+', ' ', line.strip())
                elif 'Amount' not in current_transaction and re.match(r'[+-]?\$[\d,]+\.\d{2}', line.strip()):
                    current_transaction['Amount'] = float(line.strip().replace(',','').replace('$', ''))
        
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