from core import TransactionProcessor, TransactionExtractor
from utils import eliminate_ocr_errors_for_amounts
import pandas as pd
from typing import List, Dict, Tuple
import re

class SantanderDebitTransactionExtractor(TransactionExtractor):
    # Constants for classifying words based on their x-axis positions in the PDF.
    # These thresholds determine whether a word is classified as a date, description, or amount.
    DATE_X_MIN: int = 63
    DATE_X_MAX: int = 100
    
    DESCRIPTION_X_MIN: int = 220
    DESCRIPTION_X_MAX: int = 600
    
    INCOMES_AMOUNT_X: int = 750
    EXPENSES_AMOUNT_X: int = 875
    BALANCE_AMOUNT_X: int = 1100
    AMOUNT_X_MAX: int = 1300
    
    def classify_words_from_page(self, pages: List[Tuple[float, float, str]], months: List[str]) -> Dict[str, List[Tuple[float, float, int, str]]]:
        classified_words = {'dates': [], 'descriptions': [], 'amounts': []}
        inverted_month_patterns = {v: k for k, v in self.month_patterns.items()}
        
        for i, page in enumerate(pages):
            for word in page:
                x, y, text = word
                
                if self.DATE_X_MIN <= x <= self.DATE_X_MAX:
                    match = re.match(r'(\d{2})-(\w{3})-(\d{4})', text)
                    if match:
                        day, month, year = match.groups()
                        if month in months:
                            month_number = int(inverted_month_patterns[month])
                            
                            date = f'{year}-{month_number}-{day}'
                                
                            classified_words['dates'].append((x, y, i, date)) # x coord, y coord, i page number, text
                            
                            description = text.replace(match.group(0), '').strip()
                            classified_words['descriptions'].append((x, y, i, description)) # x coord, y coord, i page number, text
                
                elif self.DESCRIPTION_X_MIN <= x <= self.DESCRIPTION_X_MAX:
                    classified_words['descriptions'].append((x, y, i, text)) # x coord, y coord, i page number, text
                    
                elif self.INCOMES_AMOUNT_X <= x < self.EXPENSES_AMOUNT_X or self.BALANCE_AMOUNT_X <= x < self.AMOUNT_X_MAX:
                    amount = eliminate_ocr_errors_for_amounts(text)
                    
                    try:
                        amount = float(amount)
                        classified_words['amounts'].append((x, y, i, amount)) # x coord, y coord, i page number, text
                    except: pass
                    
                elif self.EXPENSES_AMOUNT_X <= x < self.BALANCE_AMOUNT_X:
                    amount = eliminate_ocr_errors_for_amounts(text)
                    
                    try:
                        amount = float(amount)*-1
                        classified_words['amounts'].append((x, y, i, amount)) # x coord, y coord, i page number, text
                    except: pass
        
        return classified_words
        
    def detect_year_from_pdf(self, pages: List[Tuple[float, float, str]]) -> List[int]:
        detected_years = []
        for page in pages:
            for word in page:
                text = word[2]
                match = re.match(r'(\d{2})-(\w{3})-(\d{4})', text)
                if match and match.group(2) in self.month_patterns.values():
                    year = match.group(3)
                    if year not in detected_years:
                        detected_years.append(int(year))
        
        return sorted(list(set(detected_years)))
    
    def extract_month_from_pdf(self, pages: List[Tuple[float, float, str]]) -> List[str]:
        detected_months = []
        for page in pages:
            for word in page:
                text = word[2]
                match = re.match(r'(\d{2})-(\w{3})-(\d{4})', text)
                if match:
                    month = match.group(2)
                    if month not in detected_months and month in self.month_patterns.values():
                        detected_months.append(month)
        
        return detected_months
    
    def extract_transactions(self, classified_words: Dict[str, List[Tuple[float, float, int, str]]]) -> List[Dict[str, str]]:
        transactions = []
        current_transaction = {}
        
        number_of_dates = len(classified_words['dates'])
        avarage_distance_to_next_date: int = 25
        
        for i, date in enumerate(classified_words['dates']):
            x_date, y_date, page_date, text_date = date

            if number_of_dates > i + 1:
                y_next_date = classified_words['dates'][i + 1][1]
                
                if y_next_date < y_date:
                    y_next_date = y_date + avarage_distance_to_next_date
            else:
                y_next_date = y_date + avarage_distance_to_next_date
                
            if current_transaction:
                if current_transaction['Amount'] < 0:
                    current_transaction['Type'] = 'Cargo'
                else:
                    current_transaction['Type'] = 'Abono'
                        
                transactions.append(current_transaction)
                current_transaction = {}
                
            current_transaction['Date'] = text_date
            current_transaction['Description'] = ''
            
            for description in classified_words['descriptions']:
                x_description, y_description, page_description, text_description = description
                
                if page_date == page_description:
                    if y_date - 5 <= y_description < y_next_date:
                        current_transaction['Description'] += text_description + ' '
                    elif y_description >= y_next_date:
                        break
                        
            for amount in classified_words['amounts']:
                x_amount, y_amount, page_amount, amount_n = amount
                
                if page_date == page_amount:
                    if y_date - 5 <= y_amount < y_next_date and not 'Amount' in current_transaction:
                        current_transaction['Amount'] = amount_n
                        break
            
        if current_transaction:
            if current_transaction['Amount'] < 0:
                current_transaction['Type'] = 'Cargo'
            else:
                current_transaction['Type'] = 'Abono'
                
            transactions.append(current_transaction)
        
        return transactions
    
class SantanderDebitTransactionProcessor(TransactionProcessor):
    def process_transactions(self) -> pd.DataFrame:
        pages = self.reader.extract_words_with_coordinates_with_ocr()
        
        self.month_abbreviations = self.extractor.extract_month_from_pdf(pages)
        
        classified_words = self.extractor.classify_words_from_page(pages, self.month_abbreviations)
        transactions = self.extractor.extract_transactions(classified_words)
        
        df = pd.DataFrame(transactions)
        df['Date'] = pd.to_datetime(df['Date'])
        
        return df