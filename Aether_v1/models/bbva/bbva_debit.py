from datetime import datetime
import re
import pandas as pd
from utils.helper_functions import get_min_month
from core import TransactionProcessor, TransactionExtractor
from typing import List, Dict, Tuple
from itertools import combinations

class BBVADebitTransactionExtractor(TransactionExtractor):
    def extract_month_from_pdf(self, words: List[Tuple[float, str]]) -> List[str]:
        '''Implements the month extraction logic for BBVA's debit cards statements, detecting multiple months'''
        detected_months = []
        for word in words:
            for month in self.month_patterns.values():
                if re.search(rf'\b{month}\b', word[1]) and month not in detected_months:
                    detected_months.append(month)
        return detected_months

    def extract_transactions(self, page: List[Tuple[float, str]], detected_months: List[str], year: int) -> List[Dict[str, str]]:
        '''Extracts transactions from the lines of a BBVA debit card statement'''
        transactions = []
        period_dates = []
        current_transaction = {}

        month_regexes = [re.compile(rf'\s*(\d{{2}}/{month})') for month in detected_months]

        for i, (x,y,text) in enumerate(page):
            if text == 'Periodo' and page[i+ 1][1] == 'DEL':
                initial_date = page[i+ 2][1].split('/')
                period_dates.append(f"{initial_date[2]}-{datetime.strptime(initial_date[1], '%m').month:02}-{initial_date[0]}")
                final_date = page[i+ 4][1].split('/')
                period_dates.append(f"{final_date[2]}-{datetime.strptime(initial_date[1], '%m').month:02}-{final_date[0]}")
            if text == 'Saldo':
                if i + 1 < len(page):
                    next_word = page[i + 1][1]

                    # Check for "Saldo Anterior" (Initial Balance)
                    if next_word == 'Anterior':
                        if i + 2 < len(page) and page[i + 2][1].replace(',', '').replace('.', '').isdigit():
                            initial_amount = float(page[i + 2][1].replace(',', ''))
                            transactions.append({
                                'Date': period_dates[0],  # Start of the period
                                'Description': 'Saldo inicial',
                                'Type': 'Saldo inicial',
                                'Amount': initial_amount
                            })

                    # Check for "Saldo Final" (Final Balance)
                    # elif next_word == 'Final':
                    #     if i + 2 < len(page) and page[i + 2][1].replace(',', '').replace('.', '').isdigit():
                    #         final_amount = float(page[i + 2][1].replace(',', ''))
                    #         transactions.append({
                    #             'Date': period_dates[1],  # End of the period
                    #             'Description': 'Saldo final',
                    #             'Type': 'Saldo final',
                    #             'Amount': final_amount
                    #         })


            for month_regex in month_regexes:
                date_match = month_regex.match(text)
                if date_match:
                    page.pop(i + 1)
                    if current_transaction:
                        transactions.append(current_transaction)
                        current_transaction = {}

                    day, month = date_match.group(1).split('/')

                    for i in self.month_patterns.items():
                        number, abbreviation = i
                        if abbreviation == month:
                            month = number
                            break

                    current_transaction['Date'] = f"{year}-{datetime.strptime(month, '%B').month:02}-{day}"
                    current_transaction['Description'] = ''
                    break

            if current_transaction:
                if re.match(r'\d{2}/[A-Z]{3}', text):
                    pass
                elif 'Amount' not in current_transaction and re.match(r'^\d{1,3}(,\d{3})*\.\d{2}$', text):
                    if 360 < x < 400:
                        current_transaction['Type'] = 'Cargo'
                        current_transaction['Amount'] = float(text.replace(',',''))*-1
                    elif 400 < x < 450:
                        current_transaction['Type'] = 'Abono'
                        current_transaction['Amount'] = float(text.replace(',',''))
                    else:
                        pass
                elif 'Amount' in current_transaction and 'Balance' not in current_transaction and re.match(r'^\d{1,3}(,\d{3})*\.\d{2}$', text):
                    if x > 450:
                        current_transaction['Balance'] = float(text.replace(',',''))
                    else:
                        pass

                else:
                    if re.match(r'^-?\d{1,3}(,\d{3})*\.\d{2}$', text):
                        pass
                    elif len(current_transaction['Description']) < 50:
                        current_transaction['Description'] += text + ' '

        if current_transaction:
            transactions.append(current_transaction)

        return transactions

class BBVADebitTransactionProcessor(TransactionProcessor):
    def process_transactions(self) -> pd.DataFrame:
        pages = self.reader.extract_words_with_coordinates()
        transactions = []
        detected_months = []
        for page in pages:
            detected_months += self.extractor.extract_month_from_pdf(page)
            for word in page:
                date = re.search(r"(\d{2})/(\d{2})/(\d{4})", word[1])
                if date:
                    self.year = int(date.group(3))
                    break
        self.month_abbreviations = sorted(set(detected_months))

        for page in pages:
            transactions += self.extractor.extract_transactions(page, self.month_abbreviations, self.year)
        transactions_data = self.check_balance_consistency(pd.DataFrame(transactions))
        return transactions_data

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
