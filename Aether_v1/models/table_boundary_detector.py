from core import TableBoundaryDetector
from functools import cached_property
import pandas as pd
import re
from utils import search_phrase_in_df

class TransactionTableBoundaryDetector(TableBoundaryDetector):
    @cached_property
    def df_corrected(self):
        """
        Corrects the extracted words DataFrame by fixing text parsing issues.
        
        Common issues this method fixes:
        1. Dates and adjacent words that were incorrectly merged during OCR or are separated by a space
        2. Currency amounts with separated signs (+ or -) 
        
        Returns:
            pd.DataFrame: Corrected DataFrame with properly separated text elements
        """
        # Get a copy of the extracted words to avoid modifying the original
        df = self.bank_detector.get_extracted_words().copy()
        statement_properties = self.bank_detector.get_statement_properties()
        
        # Define regex patterns for matching amounts and dates
        amount_pattern = r'^\$?(0|[1-9]\d{0,2}(?:,\d{3})*)\.\d{2}$'  # Matches currency amounts like $1,234.56
        date_pattern = statement_properties['date_pattern']  # Bank-specific date pattern
        
        # Iterate through each row to identify and correct parsing issues
        for i, row in df.iterrows():
            text = str(row['text']).strip()
            next_text = str(df.loc[i + 1, 'text']).strip() if i + 1 < len(df) else None
            next_next_text = str(df.loc[i + 2, 'text']).strip() if i + 2 < len(df) else None
            
            # Check if current text matches date or amount patterns
            date_match = re.match(date_pattern, text)
            next_date_match = re.match(date_pattern, f'{text} {next_text}') if next_text else None
            next_next_date_match = re.match(date_pattern, f'{text} {next_text} {next_next_text}') if next_next_text else None
            amount_match = re.match(amount_pattern, text)
            
            idx_to_drop = []
            
            # Handle date correction: split dates that have extra text attached
            if date_match:
                date_str = date_match.group(0)  # Extract just the date part
                word = text[len(date_str):]      # Get the remaining text after the date
                
                try: 
                    # Ensure proper spacing between date and following word
                    if not word[0] == ' ':
                        word = ' ' + word
                        
                    # Update current row to contain only the date
                    df.loc[i, 'text'] = date_str
                    
                    # Prepend the extra word to the next row's text
                    if i + 1 < len(df):
                        df.loc[i + 1, 'text'] = word + ' ' + df.loc[i + 1, 'text']
                except: 
                    continue  # Skip if there's an error (e.g., word is empty)
                
            elif next_date_match:
                complete_date = f'{text} {next_text}'
                
                df.loc[i, 'text'] = complete_date
                df.loc[i, 'x1'] = df.loc[i + 1, 'x1']
                idx_to_drop.append(i + 1)
                
            elif next_next_date_match:
                complete_date = f'{text} {next_text} {next_next_text}'
                
                df.loc[i, 'text'] = complete_date
                df.loc[i, 'x1'] = df.loc[i + 2, 'x1']
                idx_to_drop.append(i + 1)
                idx_to_drop.append(i + 2)
                
            # Handle amount correction: combine separated signs with amounts
            elif amount_match:
                previous_text = df.loc[i - 1, 'text']
                # If the previous cell contains a standalone + or - sign
                if previous_text == '+' or previous_text == '-':
                    # Combine the sign with the current amount
                    df.loc[i, 'text'] = previous_text + text
                    idx_to_drop.append(i - 1)
                    
        if idx_to_drop:
            df = df.drop(idx_to_drop)
                
        return df   
        
    @cached_property
    def start_idx(self) -> int:
        df = self.df_corrected
        statement_properties = self.bank_detector.get_statement_properties()
        start_phrase = statement_properties['start_phrase']
        
        try:
            return search_phrase_in_df(df, start_phrase, type_return='idx') + len(start_phrase)
        except:
            return None
    
    @cached_property
    def end_idx(self) -> int:        
        start_idx = self.start_idx
        
        if start_idx is None:
            return None
        
        df = self.df_corrected
        statement_properties = self.bank_detector.get_statement_properties()
        end_phrase = statement_properties['end_phrase']
        
        return search_phrase_in_df(df, end_phrase, type_return='idx') + len(end_phrase)
    
    def get_filtered_table_words(self) -> pd.DataFrame:
        df = self.df_corrected
        start_idx = self.start_idx
        end_idx = self.end_idx
        
        if start_idx and end_idx and start_idx < end_idx:
            # Filter the DataFrame to include only the rows between the start and end indices
            return df.iloc[start_idx : end_idx].reset_index(drop=True)
        else:
            return pd.DataFrame(columns= df)  # Empty DataFrame if no match