from core import TransactionProcessor, TransactionExtractor
import pandas as pd
from typing import List, Dict, Tuple
import re

class SantanderCreditTransactionExtractor(TransactionExtractor):
    def classify_words_from_page(self, pages: List[Tuple[float, float, str]], years: List[int], months: List[str]) -> Dict[str, List[Tuple[float, float, int, str]]]:
        classified_words = {'dates': [], 'descriptions': [], 'amounts': []}
        inverted_month_patterns = {v: k for k, v in self.month_patterns.items()}
        print(months)
        print(years)
        
        for i, page in enumerate(pages):
            for word in page:
                x, y, text = word
                
                if 90 <= x < 110:
                    match = re.match(r'(\d{1,2})\s(\w{3})', text)
                    if match:
                        day, month = match.groups()
                        month_number = int(inverted_month_patterns[month])
                        if month in self.month_patterns.values():
                            if len(years) == 1:
                                year = years[0]
                                if 'ENE' in months and 'DIC' in months:
                                    if month_number - 6 <= 0:
                                        date = f'{year}-{month_number}-{day}'
                                    else:
                                        date = f'{year - 1}-{month_number}-{day}'
                                else: 
                                    date = f'{year}-{month_number}-{day}'
                            elif len(years) == 2: # This should be just for the Dic - Jan period
                                year1, year2 = years
                                if month_number == 1:
                                    date = f'{year2}-{month_number}-{day}'
                                else:
                                    date = f'{year1}-{month_number}-{day}'
                        
                            classified_words['dates'].append((x, y, i, date)) # x coord, y coord, i page number, text
                        else: pass
                
                elif 185 <= x < 700:
                    classified_words['descriptions'].append((x, y, i, text)) # x coord, y coord, i page number, text
                    
                elif 1000 <= x <= 1250:
                    if ' ' in text:
                        number_parts = re.split(r' ', text)
                        if len(number_parts[-1]) == 2:
                            int_part = ''.join(number_parts[:-1])
                            decimal_part = number_parts[-1]
                            
                            text = int_part + '.' + decimal_part
                        else:
                            text = ''.join(number_parts)
                        
                    number_parts = re.split(r',', text)
                    
                    if len(number_parts[-1]) == 2:
                        int_part = ''.join(number_parts[:-1])
                        decimal_part = number_parts[-1]
                        
                        amount = int_part + '.' + decimal_part
                    else:
                        amount = ''.join(number_parts)
                    
                    try:
                        amount = float(amount)
                        classified_words['amounts'].append((x, y, i, amount)) # x coord, y coord, i page number, text
                    except:
                        pass
                    
        return classified_words
        
    def detect_year_from_pdf(self, pages: List[Tuple[float, float, str]]) -> List[int]:
        detected_years = []
        for page in pages:
            for word in page:
                text = word[2]
                
                match_1 = re.match(r'(\d{2})/(\d{2})/(\d{4})', text)
                if match_1: 
                    dates_list = text.split(' ')
                    for date in dates_list:
                        match_2 = re.match(r'(\d{2})/(\d{2})/(\d{4})', date)
                        if match_2:
                            year = match_2.group(3)
                            if year not in detected_years:
                                detected_years.append(int(year))
                    
        
        return sorted(list(set(detected_years)))
        
    def extract_month_from_pdf(self, pages: List[Tuple[float, float, str]]) -> List[str]:
        detected_months = []
        
        for page in pages:
            for word in page:
                text = word[2]
                
                match = re.match(r'(\d{1,2})\s(\w{3})', text)
                if match:
                    month = match.group(2)
                    if month not in detected_months and month in self.month_patterns.values():
                        detected_months.append(month)
                
        return detected_months
    
    def extract_transactions(self, classified_words: Dict[str, List[Tuple[float, float, int, str]]]) -> List[Dict[str, str]]:
        transactions = []
        current_transaction = {}
        
        number_of_dates = len(classified_words['dates'])
        
        for i, date in enumerate(classified_words['dates']):
            x_date, y_date, page_date, text_date = date
            
            if number_of_dates > i + 1:
                y_next_date = classified_words['dates'][i + 1][1]
                
                if y_next_date < y_date:
                    y_next_date = y_date + 20
            else:
                y_next_date = y_date + 20
                
            if current_transaction:
                if 'pago' in current_transaction['Description'].lower():
                    current_transaction['Type'] = 'Abono'
                    transactions.append(current_transaction)
                else:
                    current_transaction['Type'] = 'Cargo'
                    try:
                        current_transaction['Amount'] = current_transaction['Amount']*-1
                        transactions.append(current_transaction)
                    except:
                        pass
                    
                current_transaction = {}
            
            current_transaction['Date'] = text_date
            current_transaction['Description'] = ''
            
            for description in classified_words['descriptions']:
                x_description, y_description, page_description, text_description = description
                
                if page_date == page_description:
                    if y_date - 5 <= y_description < y_next_date:
                        current_transaction['Description'] += text_description + ' '
                elif page_date < page_description:
                    break
            for amount in classified_words['amounts']:
                x_amount, y_amount, page_amount, amount_n = amount
                
                if page_date == page_amount:
                    if y_date - 5 <= y_amount < y_next_date:
                        current_transaction['Amount'] = amount_n
                        break
        
        if current_transaction:
            if 'pago' in current_transaction['Description'].lower():
                    current_transaction['Type'] = 'Abono'
            else:
                current_transaction['Type'] = 'Cargo'
                try:
                    current_transaction['Amount'] = current_transaction['Amount']*-1
                    transactions.append(current_transaction)
                except:
                    pass
            
        return transactions
    
class SantanderCreditTransactionProcessor(TransactionProcessor):
    def process_transactions(self) -> pd.DataFrame:
        pages = self.reader.extract_words_with_coordinates_with_ocr()
        
        self.month_abbreviations = self.extractor.extract_month_from_pdf(pages)
        years = self.extractor.detect_year_from_pdf(pages)
        
        classified_words = self.extractor.classify_words_from_page(pages, years, self.month_abbreviations)
        transactions = self.extractor.extract_transactions(classified_words)
        
        df = pd.DataFrame(transactions)
        df['Date'] = pd.to_datetime(df['Date'])
        
        return df