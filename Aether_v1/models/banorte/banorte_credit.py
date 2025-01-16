from core import TransactionProcessor, TransactionExtractor
import pandas as pd
from typing import List, Dict, Tuple
import re

class BanorteCreditTransactionExtractor(TransactionExtractor):
    # Constants for classifying words based on their x-axis positions in the PDF.
    # These thresholds determine whether a word is classified as a date, description, or amount.
    DATE_X_MIN: int = 32
    DATE_X_MAX: int = 50
    
    DESCRIPTION_X_MIN: int = 60
    DESCRIPTION_X_MAX: int = 250
    
    AMOUNT_X_MIN: int = 450
    AMOUNT_X_MAX: int = 550
    
    def classify_words_from_page(self, pages: List[Tuple[float, float, str]], years: List[int], months: List[str]) -> Dict[str, List[Tuple[float, float, int, str]]]:
        classified_words = {'dates': [], 'descriptions': [], 'amounts': []}
    
        for i, page in enumerate(pages):
            for word in page:
                x, y, text = word
                
                if self.DATE_X_MIN <= x <= self.DATE_X_MAX:
                    match = re.match(r"(\d{1,2})/(\d{2})", text)
                    if match:
                        if len(years) == 1:
                            year = years[0]
                            if 'ENE' in months or 'DIC' in months:
                                if match.group(2) == '01':
                                    date = f'{year}-{match.group(2)}-{match.group(1)}'
                                elif match.group(2) == '12':
                                    date = f'{int(year) - 1}-{match.group(2)}-{match.group(1)}'
                                else:
                                    date = f'{year}-{match.group(2)}-{match.group(1)}'
                            else:
                                date = f'{year}-{match.group(2)}-{match.group(1)}'
                        elif len(years) == 2: # This should be just for the Dic - Jan period
                            year1, year2 = years
                            
                            if match.group(2) == '01':
                                date = f'{year2}-{match.group(2)}-{match.group(1)}'
                            else:
                                date = f'{year1}-{match.group(2)}-{match.group(1)}'
                            
                        classified_words['dates'].append((x, y, i, date)) # x coord, y coord, i page number, text
                
                elif self.DESCRIPTION_X_MIN <= x <= self.DESCRIPTION_X_MAX:
                    classified_words['descriptions'].append((x, y, i, text)) # x coord, y coord, i page number, text
                    
                elif self.AMOUNT_X_MIN <= x <= self.AMOUNT_X_MAX:
                    text = text.replace(',', '').replace('$', '')
                    
                    if '-' in text:
                        text = text.replace('-', '')
                    else:
                        text = f'-{text}'
                        
                    try:
                        amount = float(text)
                        classified_words['amounts'].append((x, y, i, amount)) # x coord, y coord, i page number, text
                    except:
                        pass
                    
        return classified_words
    
    def detect_year_from_pdf(self, pages: List[Tuple[float, float, str]]) -> List[int]:
        
        detected_years = []
        
        for page in pages:
            for i,word in enumerate(page):
                text = word[2]
                
                try: 
                    if text.lower() == 'periodo':
                        year = page[i + 6][2]
                        if year.isnumeric() and year not in detected_years and len(year) <= 4:
                            detected_years.append(year)
                    elif text.lower() == 'corte':
                        year = page[i + 3][2]
                        if year.isnumeric() and year not in detected_years and len(year) <= 4:
                            detected_years.append(year)
                except:
                    pass
                        
            if len(detected_years) == 2:
                break
                    
        return sorted(list(set(detected_years)))
            
    def extract_month_from_pdf(self, pages: List[Tuple[float, float, str]]) -> List[str]:
        detected_months = []
        
        for page in pages:
            for word in page:
                text = word[2]
                x = word[0]
                
                match = re.match(r"(\d{1,2})/(\d{2})", text)
                if match and 32 <= x <= 50:
                    month = match.group(2)
                    if month in self.month_patterns.keys() and month not in detected_months:
                        month = self.month_patterns[month]
                        detected_months.append(month)
                    
        return list(set(detected_months))
    
    def extract_transactions(self, pages: List[Tuple[float, float, str]], months: List[str]) -> List[Dict[str, str]]:
        years = self.detect_year_from_pdf(pages)
        classified_words = self.classify_words_from_page(pages, years, months)
        
        transactions = []
        current_transaction = {}
        
        number_of_dates = len(classified_words['dates']) 
        avarage_distance_to_next_date: int = 15
        
        for i, date in enumerate(classified_words['dates']):
            x_date, y_date, page_date, text_date = date
            
            if number_of_dates > i + 1:
                y_next_date = classified_words['dates'][i + 1][1]
                
                if y_next_date < y_date:
                    y_next_date = y_date + avarage_distance_to_next_date
            else :
                y_next_date = y_date + avarage_distance_to_next_date
            
            try:
                if current_transaction:
                    if current_transaction['Amount'] < 0:
                        current_transaction['Type'] = 'Cargo'
                    else:
                        current_transaction['Type'] = 'Abono'
                    
                    transactions.append(current_transaction)
                    current_transaction = {}
            except:
                current_transaction = {}
                
            current_transaction['Date'] = text_date
            current_transaction['Description'] = ''
            for description in classified_words['descriptions']:
                x_description, y_description, page_description, text_description = description
                
                if len(current_transaction['Description']) > 250:
                    break
                
                if page_date == page_description:
                    if y_date <= y_description < y_next_date:
                        current_transaction['Description'] += text_description + ' '
                        
            for amount in classified_words['amounts']:
                x_amount, y_amount, page_amount, amount_n = amount
                
                if page_date == page_amount:
                    if y_date <= y_amount < y_next_date:
                        current_transaction['Amount'] = amount_n
                        break
                    
        if current_transaction:
            try:
                if current_transaction:
                    if current_transaction['Amount'] < 0:
                        current_transaction['Type'] = 'Cargo'
                    else:
                        current_transaction['Type'] = 'Abono'
                    
                    transactions.append(current_transaction)
            except:
                pass
                    
        return transactions
        
    
class BanorteCreditTransactionProcessor(TransactionProcessor):
    def process_transactions(self) -> pd.DataFrame:
        pages = self.reader.extract_words_with_coordinates()
        
        self.month_abbreviations = self.extractor.extract_month_from_pdf(pages)
        transactions = self.extractor.extract_transactions(pages, self.month_abbreviations)
        
        df = pd.DataFrame(transactions)
        df['Date'] = pd.to_datetime(df['Date'])
        df = df.sort_values(by='Date')
            
        return df