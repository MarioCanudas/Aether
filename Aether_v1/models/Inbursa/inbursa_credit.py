from core import TransactionProcessor, TransactionExtractor
import pandas as pd
from typing import List, Dict, Tuple
import re

class InbursaCreditTransactionExtractor(TransactionExtractor):
    DATE_X = 40
    
    DESCRIPTION_X = 75
    
    AMOUNT_X_MIN = 450
    AMOUNT_X_MAX = 550
    
    def classify_words_from_page(self, pages: List[List[Tuple[float, float, str]]], years: List[int], months: List[str]) -> Dict[str, List[Tuple[float, float, int, str]]]:
        classified_words = {'dates': [], 'descriptions': [], 'amounts': []}
        
        for page_num, page in enumerate(pages):
            for word in page:
                x, y, text = word
                
                if self.DATE_X <= x < self.DESCRIPTION_X:
                    match = re.match(r'(\d{2})/(\d{2})', text)
                    if match:
                        month_number, day = match.groups()
                        
                        if month_number in self.month_patterns.keys():
                            
                            if len(years) == 1:
                                year = years[0]
                                if 'ENE' in months and 'DIC' in months: # DIC - ENE period
                                    # If the month is between ENE and JUN
                                    if int(month_number) - 6 <= 0:                  
                                        date = f'{year}-{month_number}-{day}'
                                        
                                    # If the month is between JUL and DIC
                                    else:                                           
                                        date = f'{year - 1}-{month_number}-{day}'
                                else:
                                    date = f'{year}-{month_number}-{day}'
                            elif len(years) == 2: # This should be just for DIC - ENE period
                                year1, year2 = years
                                if int(month_number) - 6 <= 0: 
                                    date = f'{year2}-{month_number}-{day}'
                                else:
                                    date = f'{year1}-{month_number}-{day}'
                            
                            classified_words['dates'].append((x, y, page_num, date))
                
                elif self.DESCRIPTION_X <= x < self.AMOUNT_X_MIN:
                    classified_words['descriptions'].append((x, y, page_num, text))
                
                elif self.AMOUNT_X_MIN <= x < self.AMOUNT_X_MAX:
                    text = text.replace(',','').replace('$','')
                    
                    try:
                        amount = float(text)
                        classified_words['amounts'].append((x, y, page_num, amount))
                    except: pass
                        
        return classified_words
    
    def detect_year_from_pdf(self, pages: List[List[Tuple[float, float, str]]]) -> List[int]:
        detected_years = []
        
        for page in pages:
            for i, word in enumerate(page):
                text = word[2].strip()
                
                if 'CORTE' == text.upper():
                    next_word = page[i + 1][2]
                    match = re.match(r'(\d{2})/([A-Z]{3})/(\d{4})', next_word)
                    
                    if match:
                        year = int(match.group(3))
                        if year not in detected_years:
                            detected_years.append(year)
        
        return sorted(detected_years)
    
    def extract_month_from_pdf(self, pages: List[List[Tuple[float, float, str]]]) -> List[str]:
        detected_months = []
        
        for page in pages:
            for word in page:
                x = word[0]
                text = word[2].strip()
                
                match = re.match(r'(\d{2})/(\d{2})', text)
                if match and 40 <= x < 75:
                    month_number = match.group(1)
                    if month_number in self.month_patterns.keys():
                        month = self.month_patterns[month_number]
                        if month not in detected_months:
                            detected_months.append(month)
        
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
                try:
                    if current_transaction['Amount'] >= 0:
                        current_transaction['Type'] = 'Cargo'
                    else:
                        current_transaction['Type'] = 'Abono'
                        
                    current_transaction['Amount'] = current_transaction['Amount'] * -1
                    
                    transactions.append(current_transaction)
                except:
                    print(current_transaction)
                current_transaction = {}
                
            current_transaction['Date'] = text_date
            current_transaction['Description'] = ''
            
            for description in classified_words['descriptions']:
                x_desc, y_desc, page_desc, text_desc = description
                
                if page_date == page_desc:
                    if y_date <= y_desc < y_next_date:
                        current_transaction['Description'] += text_desc + ' '
            
            for amount in classified_words['amounts']:
                x_amount, y_amount, page_amount, num_amount = amount
                
                if page_date == page_amount:
                    if y_date <= y_amount < y_next_date:
                        current_transaction['Amount'] = num_amount
                        break
                    
        if current_transaction:
            try:
                if current_transaction['Amount'] >= 0:
                    current_transaction['Type'] = 'Cargo'
                else:
                    current_transaction['Type'] = 'Abono'
                    
                current_transaction['Amount'] = current_transaction['Amount'] * -1
                
                transactions.append(current_transaction)
            except:
                print(current_transaction)
        
        return transactions
    
class InbursaCreditTransactionProcessor(TransactionProcessor):
    def process_transactions(self) -> pd.DataFrame:
        pages = self.reader.extract_words_with_coordinates()
        
        years = self.extractor.detect_year_from_pdf(pages)
        self.month_abbreviations = self.extractor.extract_month_from_pdf(pages)
        
        classified_words = self.extractor.classify_words_from_page(pages, years, self.month_abbreviations)
        transactions = self.extractor.extract_transactions(classified_words)
        
        df = pd.DataFrame(transactions)
        df['Date'] = pd.to_datetime(df['Date'])
        
        return df