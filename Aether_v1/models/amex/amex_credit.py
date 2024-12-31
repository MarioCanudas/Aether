from core import TransactionProcessor, TransactionExtractor
import pandas as pd
from typing import List, Dict, Tuple
import re

class AmexCreditTransactionExtractor(TransactionExtractor):
    # Constants for classifying words based on their x-axis positions in the PDF.
    # These thresholds determine whether a word is classified as a date, description, or amount.
    DATE_X_MIN: int = 14
    DATE_X_MAX: int = 37
    
    DESCRIPTION_X_MIN: int = 80
    DESCRIPTION_X_MAX: int = 425
    
    AMOUNT_X_MIN: int = 450
    AMOUNT_X_MAX: int = 550
    
    def classify_words_from_page(self, words: List[Tuple[float, float, str]]) -> Dict[str, List[str]]:
        classified_words = {'dates': [], 'descriptions': [], 'amounts': []}
        
        for i, word in enumerate(words):
            x, y, text = word
            
            if self.DATE_X_MIN <= x <= self.DATE_X_MAX:
                if text.isnumeric() and len(text) <= 2:
                    if words[i + 2][2] in self.month_patterns.keys():
                        date = text + ' de ' + words[i + 2][2]
                        
                        classified_words['dates'].append((x, y, date))
                        
            elif self.DESCRIPTION_X_MIN <= x <= self.DESCRIPTION_X_MAX:
                classified_words['descriptions'].append((x, y, text))
                
            elif self.AMOUNT_X_MIN <= x <= self.AMOUNT_X_MAX:
                text = text.replace(',', '')
                try:
                    amount = float(text)
                    if amount > 0:
                        classified_words['amounts'].append((x, y, amount))
                except:
                    pass
                        
        return classified_words
    
    def extract_month_from_pdf(self, words: List[Tuple[float, float, str]]) -> List[str]:
        page = self.classify_words_from_page(words)
        detected_months = []
        
        for date in page['dates']:
            text = date[2]
            month = text.split(' ')[2]
            if month in self.month_patterns.keys() and month not in detected_months:
                detected_months.append(month)
            
        detected_months.sort(key=lambda m: list(self.month_patterns.keys()).index(m))
        
        return detected_months
    
    def extract_years_from_pdf(self, pages: List[List[Tuple[float, float, str]]]) -> List[str]:
        detected_years = []
        for page in pages:
            for word in page:
                text = word[2]
                date_pattern = re.match(r'\b(\d{1,2})-([A-Za-z]{3})-(\d{4})\b', text)
                if date_pattern:
                    if date_pattern.group(1) not in detected_years:
                        detected_years.append(int(date_pattern.group(3)))
                        
        return sorted(list(set(detected_years)))
        
    def extract_transactions(self, words: List[Tuple[float, float, str]], years: List[int], months: List[str]) -> List[Dict[str, str]]:
        transactions = []
        current_transaction = {}
        
        classified_page = self.classify_words_from_page(words)
        
        for date in classified_page['dates']:
            y_date, text_date = date[1], date[2]
            
            if current_transaction:
                if 'pago' in current_transaction['Description'].lower() and 'gracias' in current_transaction['Description'].lower():
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
            
            for description in classified_page['descriptions']:
                y_description, text_description = description[1], description[2]
                if  0 <= y_description - y_date <= 18:
                    if len(current_transaction['Description']) < 250:
                        current_transaction['Description'] += text_description + ' '
                    else:
                        break
                
                for amount in classified_page['amounts']:
                    y_amount, amount = amount[1], amount[2]
                    if  0 <= y_amount - y_date <= 10:
                        current_transaction['Amount'] = amount
                        break
                        
        if 'Diciembre' in months and 'Enero' in months:
            for transaction in transactions:
                if len(years) == 1:
                    day, _ , month = transaction['Date'].split(' ')
                    month = list(self.month_patterns.keys()).index(month) + 1
                    year = years[0]
                
                    if 'enero' in transaction['Date'].lower():
                        transaction['Date'] = f'{year}-{month}-{day}'
                    else:
                        transaction['Date'] = f'{year - 1}-{month}-{day}'
                else:
                    day, _ , month = transaction['Date'].split(' ')
                    month = list(self.month_patterns.keys()).index(month) + 1
                    year1, year2 = years
                    
                    if 'enero' in transaction['Date'].lower():
                        transaction['Date'] = f'{year2}-{month}-{day}'
                    else:
                        transaction['Date'] = f'{year1}-{month}-{day}'
        else: 
            for transaction in transactions:
                day, _ , month = transaction['Date'].split(' ')
                month = list(self.month_patterns.keys()).index(month) + 1
                year = years[0]
                
                transaction['Date'] = f'{year}-{month}-{day}'
                    
        return transactions
        
    
class AmexCreditTransactionProcessor(TransactionProcessor):
    def process_transactions(self) -> pd.DataFrame:
        pages = self.reader.extract_words_with_coordinates()
        transactions = []
        
        detected_months = []
        
        for words in pages:  
            detected_months += self.extractor.extract_month_from_pdf(words)
            
        self.month_abbreviations = sorted(list(set(detected_months)))
        detected_years = self.extractor.extract_years_from_pdf(pages)  
        
        for words in pages:
            transactions += self.extractor.extract_transactions(words, detected_years, self.month_abbreviations)
            
        df = pd.DataFrame(transactions)
        df['Date'] = pd.to_datetime(df['Date'])
        df = df.sort_values(by='Date')
            
        return df