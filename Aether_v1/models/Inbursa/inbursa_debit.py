from core import TransactionProcessor, TransactionExtractor
import pandas as pd
from typing import List, Dict, Tuple
import re

class InbursaDebitTransactionExtractor(TransactionExtractor):
    # Constants for classifying words based on their x-axis positions in the PDF.
    # These thresholds determine whether a word is classified as a date, description, or amount.
    DATE_X: int = 11

    DESCRIPTION_X: int = 42

    EXPENSES_AMOUNT_X: int = 350
    INCOMES_AMOUNT_X: int = 425
    BALANCE_AMOUNT_X: int = 500
    AMOUNT_X_MAX: int = 570

    def classify_words_from_page(self, pages: List[List[Tuple[float, float, str]]], years: List[int], months: List[str]) -> Dict[str, List[Tuple[float, float, int, str]]]:
        classified_words = {'dates': [], 'descriptions': [], 'amounts': []}
        inverted_month_patterns = {v: k for k, v in self.month_patterns.items()}

        for page_num, page in enumerate(pages):
            for i, word in enumerate(page):
                x, y, text = word
                text = text.strip()

                try:
                    next_word = page[i + 1][2].strip()
                except:
                    next_word = None

                if self.DATE_X <= x < self.DESCRIPTION_X:
                    if text in months:
                        day = next_word
                        month = text
                        month_number = inverted_month_patterns[month]

                        if len(years) == 1:
                            year = years[0]
                            if 'ENE' in months and 'DIC' in months: # DIC - ENE period
                                # If the month is between ENE and JUN
                                if month_number - 6 <= 0:
                                    date = f'{year}-{month_number}-{day}'

                                # If the month is between JUL and DIC
                                else:
                                    date = f'{year - 1}-{month_number}-{day}'
                            else:
                                date = f'{year}-{month_number}-{day}'
                        elif len(years) == 2: # This should be just for DIC - ENE period
                            year1, year2 = years
                            # If the month is between ENE and JUN
                            if month_number - 6 <= 0:
                                date = f'{year2}-{month_number}-{day}'

                            # If the month is between JUL and DIC
                            else:
                                date = f'{year1}-{month_number}-{day}'

                        classified_words['dates'].append((x, y, page_num, date))

                elif self.DESCRIPTION_X <= x < self.EXPENSES_AMOUNT_X:
                    classified_words['descriptions'].append((x, y, page_num, text))

                elif self.EXPENSES_AMOUNT_X <= x < self.INCOMES_AMOUNT_X:
                    text = text.replace(',','')
                    amount_type = 'Cargo'

                    try:
                        amount = float(text) * -1 # Expenses are negative float
                        classified_words['amounts'].append((x, y, page_num, amount, amount_type))
                    except: pass

                elif self.INCOMES_AMOUNT_X <= x < self.BALANCE_AMOUNT_X:
                    text = text.replace(',','')
                    amount_type = 'Abono'

                    try:
                        amount = float(text)
                        classified_words['amounts'].append((x, y, page_num, amount, amount_type))
                    except: pass

                elif self.BALANCE_AMOUNT_X <= x < self.AMOUNT_X_MAX:
                    text = text.replace(',','')
                    amount_type = 'Saldo'

                    try:
                        amount = float(text)
                        classified_words['amounts'].append((x, y, page_num, amount, amount_type))
                    except: pass

        return classified_words

    def detect_year_from_pdf(self, pages: List[List[Tuple[float, float, str]]]) -> List[int]:
        detected_years = []

        for page in pages:
            for i, word in enumerate(page):
                text = word[2].strip()

                if text.upper() == 'PERIODO':
                    period = ''
                    period_words_number = 9
                    for word in page[i + 1 : i + period_words_number]:
                        if re.match(r'20\d{2}', word[2]):
                            detected_years.append(int(word[2]))

                    return sorted(list(set(detected_years)))

    def extract_month_from_pdf(self, pages: List[List[Tuple[float, float, str]]]) -> List[str]:
        detected_months = []

        for page in pages:
            for word in page:
                x, _, text = word

                if self.DATE_X <= x < self.DESCRIPTION_X:
                    if text in self.month_patterns.values() and text not in detected_months:
                        detected_months.append(text)

        return detected_months

    def extract_transactions(self, classified_words: Dict[str, List[Tuple[float, float, int, str]]]) -> List[Dict[str, str]]:
        transactions = []
        current_transaction = {}

        number_of_dates = len(classified_words['dates'])
        avarage_distance_to_next_date: int = 20

        for i, date in enumerate(classified_words['dates']):
            x_date, y_date, page_date, text_date = date

            if number_of_dates > i + 1:
                y_next_date = classified_words['dates'][i + 1][1]

                if y_next_date < y_date:
                    y_next_date = y_date + avarage_distance_to_next_date

            else:
                y_next_date = y_date + avarage_distance_to_next_date

            if current_transaction:
                transactions.append(current_transaction)
                current_transaction = {}

            current_transaction['Date'] = text_date
            current_transaction['Description'] = ''

            for description in classified_words['descriptions']:
                x_description, y_description, page_description, text_description = description

                if page_date == page_description:
                    if y_date <= y_description < y_next_date:
                        current_transaction['Description'] += text_description + ' '

            for amount in classified_words['amounts']:
                x_amount, y_amount, page_amount, value, amount_type = amount

                if page_date == page_amount:
                    if y_date <= y_amount < y_next_date:
                        current_transaction['Amount'] = value
                        current_transaction['Type'] = amount_type
                        break

        if current_transaction:
            transactions.append(current_transaction)

        return transactions

class InbursaDebitTransactionProcessor(TransactionProcessor):
    def process_transactions(self) -> pd.DataFrame:
        pages = self.reader.extract_words_with_coordinates()

        years = self.extractor.detect_year_from_pdf(pages)
        self.month_abbreviations = self.extractor.extract_month_from_pdf(pages)

        classified_words = self.extractor.classify_words_from_page(pages, years, self.month_abbreviations)
        transactions = self.extractor.extract_transactions(classified_words)

        df = pd.DataFrame(transactions)
        df['Date'] = pd.to_datetime(df['Date'])

        return df
