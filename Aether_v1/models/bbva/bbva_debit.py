from datetime import datetime
import re
import pandas as pd
from utils.helper_functions import get_min_month
from core import TransactionProcessor, TransactionExtractor
from typing import List, Dict
from itertools import combinations

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
        self.year = self.year or self.detect_year_from_pdf(lines)
        month_regexes = [re.compile(rf'\s*(\d{{2}}/{month})') for month in detected_months]
        reverse_month_patterns = {v: k for k, v in self.month_patterns.items()}
        abono_patterns = ["pago de nomina", "venta fondos", "spei recibido", "depósito"]
        lines = lines[:-2] # Delate footer
        for line in lines:
            if line.strip() == '':
                lines.pop(lines.index(line))

            if re.search(r'\d{2}/[A-Z]{3}', line.strip()):
                index = lines.index(line)+1
                if re.search(r'\d{2}/[A-Z]{3}', lines[index].strip()):
                    lines.pop(index)

            if line.strip() == 'Periodo':
                first_day = lines[lines.index(line)+1].split('/')[0].split(' ')[1]
            elif line.strip() == 'Saldo Anterior':
                initial_amount = float(lines[lines.index(line) + 1].strip().replace(',',''))
                earliest_month = reverse_month_patterns.get(get_min_month(detected_months))
                initial_balance = {'Date': f"{self.year}-{datetime.strptime(earliest_month, '%B').month:02}-{first_day}", 'Description': 'Saldo inicial', 'Amount': initial_amount, 'Balance': initial_amount}
                transactions.append(initial_balance)

            for month_regex in month_regexes:
                date_match = month_regex.match(line)
                if date_match:
                    if current_transaction:
                        self.classify_and_append_transaction(current_transaction, transactions, abono_patterns)
                        current_transaction = {}

                    if 'Date' not in current_transaction:
                        date_parts = date_match.group(1).split('/')
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
                if re.match(r'\d{2}/[A-Z]{3}', line.strip()):
                    pass
                elif 'Description' not in current_transaction:
                    current_transaction['Description'] = line.strip()
                elif 'Amount' not in current_transaction and re.match(r'^\d{1,3}(,\d{3})*\.\d{2}$', line.strip()):
                    current_transaction['Amount'] = float(line.strip().replace(',',''))
                elif 'Balance' not in current_transaction and 'Amount' in current_transaction and re.match(r'^\d{1,3}(,\d{3})*\.\d{2}$', line.strip()):
                    current_transaction['Balance'] = float(line.strip().replace(',',''))
                elif 'Description' and 'Amount' in current_transaction and not re.match(r'^-?\d{1,3}(,\d{3})*\.\d{2}$', line.strip()):
                    if ' / ' in current_transaction['Description']:
                        pass
                    elif 'RFC' in line.strip() or 'Referencia' in line.strip():
                        pass
                    else:
                        current_transaction['Description'] += ' / ' + line.strip()

        if current_transaction:
            self.classify_and_append_transaction(current_transaction, transactions, abono_patterns)


        return transactions

    def classify_and_append_transaction(self, current_transaction: Dict[str, str], transactions: List[Dict[str, str]], abono_patterns: List[str]) -> None:
        """
        Classifies a transaction as 'Cargo' or 'Abono' based on patterns and appends it to the transactions list.

        Parameters:
        - current_transaction (Dict[str, str]): The current transaction being processed.
        - transactions (List[Dict[str, str]]): The list of all transactions.
        - abono_patterns (List[str]): List of patterns indicating Abonos (income).
        - cargo_patterns (List[str]): List of patterns indicating Cargos (expenses).
        """
        if current_transaction and 'Amount' in current_transaction and 'Description' in current_transaction:
            description = current_transaction['Description'].lower()
            if any(pattern in description for pattern in abono_patterns):
                current_transaction['Type'] = 'Abono'
            else:
                current_transaction['Type'] = 'Cargo'
                current_transaction['Amount'] = -current_transaction['Amount']
            transactions.append(current_transaction)


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

        return self.check_balance_consistency(pd.DataFrame(transactions))

    def check_balance_consistency(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Checks and adjusts the consistency of balances in transaction data.

        Parameters:
        - df (pd.DataFrame): DataFrame containing sorted transaction data with 'Amount' and 'Balance' columns.

        Returns:
        - pd.DataFrame: DataFrame with adjusted transactions where inconsistencies are resolved.
        """
        df = df.copy()  # Avoid modifying the original DataFrame
        df["RunningSum"] = None  # Column to store the running sum
        df["Correction"] = None  # Column to log corrections

        running_sum = 0  # Initialize the running sum

        for i in range(len(df)):
            # Update the running sum
            running_sum += df.loc[i, "Amount"]
            df.loc[i, "RunningSum"] = running_sum

            # Check if the current row has a Balance
            if pd.notna(df.loc[i, "Balance"]):
                target_balance = df.loc[i, "Balance"]

                # If running sum matches the balance, continue
                if abs(running_sum - target_balance) <= 1e-2:
                    continue
                adjustment_range = df.loc[:i].index[
                                (df.loc[:i, "Balance"].isna()) &
                                (df.loc[:i, "Description"].str.contains("pago cuenta", case=False, na=False))
                            ].tolist() + [i]
                # Test all combinations of sign changes
                for r in range(1, len(adjustment_range) + 1):
                    for combination in combinations(adjustment_range, r):
                        test_sum = running_sum
                        for idx in combination:
                            test_sum -= 2 * df.loc[idx, "Amount"]  # Flip the sign
                        if abs(test_sum - target_balance) <= 1e-2:
                            # Apply the corrections
                            for idx in combination:
                                df.loc[idx, "Amount"] = -df.loc[idx, "Amount"]

                                current_type = df.loc[idx, "Type"]
                                if current_type == "Cargo":
                                    df.loc[idx, "Type"] = "Abono"
                                elif current_type == "Abono":
                                    df.loc[idx, "Type"] = "Cargo"

                                df.loc[idx, "Correction"] = f"Flipped sign to match balance {target_balance}"
                            running_sum = target_balance  # Update the running sum
                            break
                    else:
                        continue
                    break
            df["RunningSum"] = df["Amount"].cumsum()

        return df
