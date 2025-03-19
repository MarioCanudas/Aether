from core import TransactionProcessor, TransactionExtractor
import pandas as pd
from typing import List, Dict, Tuple
import re

class HSBCCreditTransactionExtractor(TransactionExtractor):
    # Constants for classifying words based on their x-axis positions in the PDF.
    # These thresholds determine whether a word is classified as a date, description, or amount.
    DATE_X_MIN: int = 38
    DATE_X_MAX: int = 75

    DESCRIPTION_X: int = 100

    AMOUNT_X_MIN: int = 450
    AMOUNT_X_MAX: int = 575

    def classify_words_from_page(self, pages: List[List[Tuple[float, float, str]]], years: List[int], months: List[str]) -> Dict[str, List[Tuple[float, float, int, str]]]:
        inverted_month_patterns = {v: k for k, v in self.month_patterns.items()}
        classified_words = {'dates': [], 'descriptions': [], 'amounts': []}

        for num_page, page in enumerate(pages):
            for i, word in enumerate(page):
                x, y, text = word

                try:
                    next_word = page[i + 1][2]
                except: next_word = ''

                if self.DATE_X_MIN <= x <= self.DATE_X_MAX:
                    if text.isnumeric() and next_word in months:
                        month_number = int(inverted_month_patterns[next_word])

                        if len(years) == 1:
                            year = years[0]
                            if 'ENE' in months and 'DIC' in months:
                                if month_number - 6 <= 0:
                                    date = f'{year}-{month_number}-{text}'
                                else:
                                    date = f'{year - 1}-{month_number}-{text}'
                            else:
                                date = f'{year}-{month_number}-{text}'
                        elif len(years) == 2:
                            year1, year2 = years
                            if month_number == 1:
                                date = f'{year2}-{month_number}-{text}'
                            elif month_number == 12:
                                date = f'{year1}-{month_number}-{text}'

                        classified_words['dates'].append((x, y, num_page, date))

                elif self.DESCRIPTION_X <= x < self.AMOUNT_X_MIN:
                    classified_words['descriptions'].append((x, y, num_page, text))

                elif self.AMOUNT_X_MIN <= x <= self.AMOUNT_X_MAX:
                    text = text.replace(',', '')
                    try:
                        amount = float(text)
                        classified_words['amounts'].append((x, y, num_page, amount))
                    except: pass

        return classified_words

    def detect_year_from_pdf(self, pages: List[List[Tuple[float, float, str]]]) -> List[int]:
        detected_years = []

        for page in pages:
            for i, word in enumerate(page):
                text = word[2]
                if 'FECHA' == text.upper():
                    if 'DE CORTE' == f'{page[i + 1][2]} {page[i + 2][2]}'.upper():
                        date = f'{page[i + 3][2]}-{page[i + 4][2]}-{page[i + 5][2]}'
                        match = re.match(r'(\d{2})-([A-Z]{3})-(\d{4})', date)
                        if match:
                            if match.group(3) not in detected_years:
                                detected_years.append(int(match.group(3)))

        return sorted(detected_years)

    def extract_month_from_pdf(self, pages: List[List[Tuple[float, float, str]]]) -> List[str]:
        detected_months = []

        for page in pages:
            for word in page:
                text = word[2].strip()
                if text in self.month_patterns.values() and text not in detected_months:
                    detected_months.append(text)

        return detected_months

    def extract_transactions(self, classified_words: Dict[str, List[Tuple[float, float, int, str]]]) -> List[Dict[str, str]]:
        transactions = []
        current_transaction = {}

        number_of_dates = len(classified_words['dates'])
        avarage_distance_to_next_date: int = 10

        for i, date in enumerate(classified_words['dates']):
            x_date, y_date, page_date, text_date = date

            if number_of_dates > i + 1:
                y_next_date = classified_words['dates'][i + 1][1]

                if y_next_date < y_date:
                    y_next_date = y_date + avarage_distance_to_next_date
            else:
                y_next_date = y_date + avarage_distance_to_next_date

            if current_transaction:
                if ' GRACIAS' in current_transaction['Description'].upper():
                    current_transaction['Type'] = 'Abono'
                else:
                    current_transaction['Type'] = 'Cargo'
                    try:
                        current_transaction['Amount'] = current_transaction['Amount']*-1
                    except: pass

                transactions.append(current_transaction)
                current_transaction = {}

            current_transaction['Date'] = text_date
            current_transaction['Description'] = ''

            for description in classified_words['descriptions']:
                x_description, y_description, page_description, text_description = description

                if page_description == page_date:
                    if y_date <= y_description < y_next_date:
                        current_transaction['Description'] += f'{text_description} '
                elif page_description > page_date:
                    break

            for amount in classified_words['amounts']:
                x_amount, y_amount, page_amount, num_amount = amount

                if page_amount == page_date:
                    if y_date <= y_amount < y_next_date:
                        current_transaction['Amount'] = num_amount
                        break

        if current_transaction:
            if ' GRACIAS' in current_transaction['Description'].upper():
                current_transaction['Type'] = 'Abono'
            else:
                current_transaction['Type'] = 'Cargo'
                try:
                    current_transaction['Amount'] = current_transaction['Amount']*-1
                except: pass

            transactions.append(current_transaction)

        return transactions

class HSBCCreditTransactionProcessor(TransactionProcessor):
    def process_transactions(self) -> pd.DataFrame:
        pages = self.reader.extract_words_with_coordinates()

        self.month_abbreviations = self.extractor.extract_month_from_pdf(pages)
        years = self.extractor.detect_year_from_pdf(pages)

        classified_words = self.extractor.classify_words_from_page(pages, years, self.month_abbreviations)
        transactions = self.extractor.extract_transactions(classified_words)

        df = pd.DataFrame(transactions)
        df['Date'] = pd.to_datetime(df['Date'])

        return df
