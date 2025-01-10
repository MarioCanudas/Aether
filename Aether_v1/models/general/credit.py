from core import TransactionProcessor, TransactionExtractor
import pandas as pd
from typing import List, Dict, Tuple, Literal
import re

class GeneralCreditTransactionExtractor(TransactionExtractor):
    def x_axis_values(self, pages: List[List[Tuple[float, float, str]]], bank : List[Literal['Amex', 'BBVA', 'Banorte', 'Citibanamex', 'Hsbc', 'Inbursa', 'Nu', 'Santander']]) -> List[Tuple[float, float]]:
        x_values = []
        
        all_x_values = []
        
        for page in pages:
            for i, word in enumerate(page):
                x, y, text = word
                text = text.strip()
                previous_word = page[i - 1][2].strip()
                
                if bank == 'BBVA' or bank == 'Citibanamex':
                    signs = ['+', '-']
                    
                    if re.match(r'\$\d+(,\d{3})*(\.\d{2})?', text):
                        if previous_word in signs:
                            text = f'{previous_word}{text}'
                            
                            page[i] = (x, y, text)
                        else: continue
                
                date_match = re.match(r'(\d{2})-([A-Za-z]{3})-(\d{4})', text)
                amount_match = re.match(r'[+-]( ?)\$\d+(,\d{3})*(\.\d{2})?', text)
                
                if date_match:
                    if  not re.match(r'(\d{2})-([A-Za-z]{3})-(\d{4})', previous_word):
                        all_x_values.append({'Date_x': x, 'Amount_x': None})
                    else: continue
                        
                elif amount_match:
                    all_x_values.append({'Date_x': None, 'Amount_x': x})
        
        df = pd.DataFrame(all_x_values)
        
        # Delate outliers in the x axis, using the IQR method
        for column in df.columns:
            Q1 = df[column].quantile(0.25)
            Q3 = df[column].quantile(0.75)
            IQR = Q3 - Q1
            
            iqr_multiplier = 1.25
            
            lower_bound = Q1 - (iqr_multiplier * IQR)
            upper_bound = Q3 + (iqr_multiplier * IQR)
            
            df_filtred = df[(df[column] >= lower_bound) & (df[column] <= upper_bound)]
            
            x_mode_value = df_filtred[column].mode()[0]
            x_values.append(float(x_mode_value))
            
        return sorted(x_values)
    
    # 
    X_THRESHOLD_DATE = 5
    X_THRESHOLD_AMOUNT = 50
    
    def classify_words_from_page(self, pages: List[List[Tuple[float, float, str]]], x_values: Tuple[float, float]) -> Dict[str, List[Tuple[float, float, int, str]]]:
        inverted_month_patterns = {v: k for k, v in self.month_patterns.items()}
        
        print(x_values)
        DATE_X, AMOUNT_X = x_values
        
        
        classified_words = {'dates': [], 'descriptions': [], 'amounts': []}
        
        for num_page, page in enumerate(pages):
            for word in page:
                x, y, text = word
                
                x = round(x, 3) # Round the x-axis value to avoid errors in word classification
                y = round(y, 3) # Round the y-axis value to avoid errors in transactions extraction
                
                if abs(DATE_X - x) < self.X_THRESHOLD_DATE:
                    
                    date_match = re.match(r'(\d{2})-([A-Za-z]{3})-(\d{4})', text)
                    
                    if date_match:
                        day, month, year = date_match.groups()
                        month = month.upper()
                        
                        month_number = inverted_month_patterns[month]
                        
                        date = f'{year}-{month_number}-{day}'
                        
                        classified_words['dates'].append((x, y, num_page, date)) 
                
                elif DATE_X + self.X_THRESHOLD_DATE < x < AMOUNT_X - self.X_THRESHOLD_AMOUNT:
                    classified_words['descriptions'].append((x, y, num_page, text)) # Round the y-axis value to avoid errors in transactions extraction
                    
                elif abs(AMOUNT_X - x) < self.X_THRESHOLD_AMOUNT:
                    text = text.replace(',','').replace('$','').replace('+', '').replace(' ', '')
                    
                    try:
                        amount = float(text)*-1
                        classified_words['amounts'].append((x, y, num_page, amount)) # Round the y-axis value to avoid errors in transactions extraction
                    except: pass
        
        return classified_words
    
    def detect_year_from_pdf(self, pages: List[List[Tuple[float, float, str]]], x_values: List[float]) -> List[int]:
        detected_years = []
        DATE_X = x_values[0]
        
        for page in pages:
            for word in page:
                x, _, text = word
                
                match = re.match(r'(\d{2})-([A-Za-z]{3})-(\d{4})', text)
                
                if match and abs(x - DATE_X) < self.X_THRESHOLD_DATE:
                    year = int(match.group(3))
                    
                    if year not in detected_years:
                        detected_years.append(year)
        
        return detected_years
    
    def extract_month_from_pdf(self, pages: List[List[Tuple[float, float, str]]], x_values: List[float]) -> List[str]:
        detected_months = []
        DATE_X = x_values[0]
        
        for page in pages:
            for word in page:
                x, _, text = word
                
                match = re.match(r'(\d{2})-([A-Za-z]{3})-(\d{4})', text)
                
                if match and abs(x - DATE_X) < self.X_THRESHOLD_DATE:
                    month = match.group(2).upper()
                    
                    if month not in detected_months:
                        detected_months.append(month)
        
        return detected_months
    
    def extract_transactions(self, classified_words: Dict[str, List[Tuple[float, float, int, str]]]) -> List[Dict[str, str]]:
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
            
            else:
                y_next_date = y_date + avarage_distance_to_next_date
                
            if current_transaction:
                
                try:
                    if current_transaction['Amount'] < 0:
                        current_transaction['Type'] = 'Cargo'
                    else:
                        current_transaction['Type'] = 'Abono'
                        
                    transactions.append(current_transaction)
                except: print(current_transaction)
                
                current_transaction = {}
            
            current_transaction['Date'] = text_date
            current_transaction['Description'] = ''
            
            for description in classified_words['descriptions']:
                x_description, y_description, page_description, text_description = description
                
                if page_date == page_description:
                    if y_date <= y_description < y_next_date:
                        current_transaction['Description'] += text_description + ' '
                    
            for amount in classified_words['amounts']:
                x_amount, y_amount, page_amount, num_amount = amount
                
                
                if page_date == page_amount:
                    if y_date <= y_amount < y_next_date:
                        current_transaction['Amount'] = num_amount
                        break
                
        if current_transaction:
            try:
                if current_transaction['Amount'] < 0:
                    current_transaction['Type'] = 'Cargo'
                else:
                    current_transaction['Type'] = 'Abono'
                    
                transactions.append(current_transaction)
            except: print(current_transaction)
        
        return transactions
    
class GeneralCreditTransactionProcessor(TransactionProcessor):
    def process_transactions(self, bank : List[Literal['Amex', 'BBVA', 'Banorte', 'Citibanamex', 'Hsbc', 'Inbursa', 'Nu', 'Santander']]):
        pages = self.reader.extract_words_with_coordinates_with_ocr() if bank == 'Santander' else self.reader.extract_words_with_coordinates()
        
        x_values = self.extractor.x_axis_values(pages, bank)
        self.month_abbreviations = self.extractor.extract_month_from_pdf(pages, x_values)
        
        clasified_words = self.extractor.classify_words_from_page(pages, x_values)
        transaction = self.extractor.extract_transactions(clasified_words)
        
        df = pd.DataFrame(transaction)
        df['Date'] = pd.to_datetime(df['Date'])
        
        return df
    