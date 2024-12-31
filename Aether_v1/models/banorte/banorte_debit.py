from core import TransactionProcessor, TransactionExtractor
import pandas as pd
from typing import List, Dict, Tuple
import re

class BanorteDebitTransactionExtractor(TransactionExtractor):
    # Constants for classifying words based on their x-axis positions in the PDF.
    # These thresholds determine whether a word is classified as a date, description, or amount.
    DATE_X_MIN: int = 50
    DATE_X_MAX: int = 70
    
    DESCRIPTION_X_MIN: int = 85
    DESCRIPTION_X_MAX: int = 320
    
    INCOMES_AMOUNT_X: int = 350
    EXPENSES_AMOUNT_X: int = 425
    BALANCE_AMOUNT_X: int = 500
    AMOUNT_X_MAX: int = 600
    
    def classify_words_from_page(self, pages: List[Tuple[float, float, str]]) -> Dict[str, List[Tuple[float, float, int, str]]]:
        inverted_month_patterns = {v: k for k, v in self.month_patterns.items()}
        classified_words = {'dates': [], 'descriptions': [], 'amounts': []}
        
        for i, page in enumerate(pages):
            for word in page:
                x, y, text = word
                
                if self.DATE_X_MIN <= x <= self.DATE_X_MAX:
                    match = re.match(r"(\d{2})-(\w{3})-(\d{2})", text)
                    if match:
                        month = inverted_month_patterns[match.group(2)]
                        date = f'20{match.group(3)}-{month}-{match.group(1)}'
                        classified_words['dates'].append((x, y, i, date)) # x coord, y coord, i page number, text
                elif self.DESCRIPTION_X_MIN <= x < self.DESCRIPTION_X_MAX:
                    if text == ',' or text == '-':
                        pass
                    else:
                        classified_words['descriptions'].append((x, y, i, text)) # x coord, y coord, i page number, text
                elif self.INCOMES_AMOUNT_X <= x < self.EXPENSES_AMOUNT_X or self.BALANCE_AMOUNT_X <= x < self.AMOUNT_X_MAX:
                    text = text.replace(',', '')
                    try:
                        amount = float(text)
                        classified_words['amounts'].append((x, y, i, amount)) # x coord, y coord, i page number, text
                    except:
                        pass
                elif self.EXPENSES_AMOUNT_X <= x < self.BALANCE_AMOUNT_X:
                    text = text.replace(',', '')
                    try:
                        amount = float(text)*-1
                        classified_words['amounts'].append((x, y, i, amount)) # x coord, y coord, i page number, text
                    except:
                        pass
                    
        return classified_words
                        
    def extract_month_from_pdf(self, classified_words: Dict[str, List[Tuple[float, float, int, str]]]) -> List[str]:
        detected_months = []
        
        for dates in classified_words['dates']:
            date = dates[3]
    
            month = self.month_patterns[str(date.split('-')[1])]
            
            if month not in detected_months:
                detected_months.append(month)
                
        return detected_months
    
    def detect_year_from_pdf(self, classified_words: Dict[str, List[Tuple[float, float, int, str]]]) -> List[int]:
        detected_years = []
        
        for dates in classified_words['dates']:
            date = dates[3]
            
            year = date.split('-')[0]
            if year not in detected_years:
                detected_years.append(int(year))
                
        return sorted(list(set(detected_years)))
    
    def extract_transactions(self, classified_words: Dict[str, List[Tuple[float, float, int, str]]]) -> List[Dict[str, str]]:
        transactions = []
        current_transaction = {}
        
        number_of_dates = len(classified_words['dates'])
        all_dates = []
        avarage_distance_to_next_date: int = 15
        
        for date in classified_words['dates']:
            all_dates.append(date[3])
        
        for i, date in enumerate(classified_words['dates']):
            x_date, y_date, page_date, text_date = date
            
            if number_of_dates > i + 1:
                y_next_date = classified_words['dates'][i + 1][1]
                
                if y_next_date < y_date:
                    y_next_date = y_date + avarage_distance_to_next_date
            else :
                y_next_date = y_date + avarage_distance_to_next_date
                
            if current_transaction:
                if 'trasp' in current_transaction['Description'].lower() or 'fondo' in current_transaction['Description'].lower():
                    current_transaction['Origin'] = 'Fondos'
                else: 
                    current_transaction['Origin'] = 'Cuenta'
                    
                if current_transaction['Amount'] < 0:
                    current_transaction['Type'] = 'Cargo'
                else:
                    if 'saldo' in current_transaction['Description'].lower():
                        if all_dates.index(current_transaction['Date']) <= 3:
                            current_transaction['Origin'] = 'Cuenta'
                        else: 
                            current_transaction['Origin'] = 'Fondos'
                        current_transaction['Type'] = 'Saldo'
                    else:
                            
                        current_transaction['Type'] = 'Abono'
                        
                transactions.append(current_transaction)
                current_transaction = {}
                
            current_transaction['Date'] = text_date
            current_transaction['Description'] = ''
            
            for description in classified_words['descriptions']:
                x_description, y_description, page_description, text_description = description
                
                if len(current_transaction['Description']) > 250:
                    break
                else:
                    if page_date == page_description:
                        if y_date <= y_description < y_next_date:
                            current_transaction['Description'] += text_description + ' '
                            
            for amount in classified_words['amounts']:
                x_amount, y_amount, page_amount, amount_n = amount
                
                if page_date == page_amount:
                    if y_date <= y_amount < y_next_date and not 'Amount' in current_transaction:
                        current_transaction['Amount'] = amount_n
                        break
        
        if current_transaction:
            if 'trasp' in current_transaction['Description'].lower() or 'fondo' in current_transaction['Description'].lower():
                current_transaction['Origin'] = 'Fondos'
            else: 
                current_transaction['Origin'] = 'Cuenta'
                
            if current_transaction['Amount'] < 0:
                current_transaction['Type'] = 'Cargo'
            else:
                if 'saldo' in current_transaction['Description'].lower():
                    current_transaction['Type'] = 'Saldo'
                else: 
                    current_transaction['Type'] = 'Abono'
                    
            transactions.append(current_transaction)
        
        return transactions
            
    
class BanorteDebitTransactionProcessor(TransactionProcessor):
    def process_transactions(self) -> pd.DataFrame:
        pages = self.reader.extract_words_with_coordinates()
        classified_words = self.extractor.classify_words_from_page(pages)
        
        self.month_abbreviations = self.extractor.extract_month_from_pdf(classified_words)
        transactions = self.extractor.extract_transactions(classified_words)
        
        df = pd.DataFrame(transactions)
        df['Date'] = pd.to_datetime(df['Date'])
            
        return df
        