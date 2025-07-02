import pandas as pd
import re
from functools import cache
from _core import TextProcessor

class DefaultTextProcessor(TextProcessor):
    @cache
    def correct_text(self) -> pd.DataFrame:
        """
        Corrects the extracted words DataFrame by fixing text parsing issues.
        
        Common issues this method fixes:
        1. Dates and adjacent words that were incorrectly merged during OCR or are separated by a space
        2. Currency amounts with separated signs (+ or -) 
        
        Returns:
            pd.DataFrame: Corrected DataFrame with properly separated text elements
        """
        # Get a copy of the extracted words to avoid modifying the original
        extracted_words = self.extracted_words
        corrected_extracted_words = self.extracted_words.copy()
        
        # Define regex patterns for matching amounts and dates
        amount_pattern = r'^\$?(0|[1-9]\d{0,2}(?:,\d{3})*)\.\d{2}$'  # Matches currency amounts like $1,234.56
        date_pattern = self.statement_properties['date_pattern']  # Bank-specific date pattern
        
        # Iterate through each row to identify and correct parsing issues
        for i, row in extracted_words.iterrows():
            text = str(row['text']).strip()
            next_text = str(extracted_words.loc[i + 1, 'text']).strip() if i + 1 < len(extracted_words) else None
            next_next_text = str(extracted_words.loc[i + 2, 'text']).strip() if i + 2 < len(extracted_words) else None
            
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
                    corrected_extracted_words.loc[i, 'text'] = date_str
                    
                    # Prepend the extra word to the next row's text
                    if i + 1 < len(extracted_words):
                        corrected_extracted_words.loc[i + 1, 'text'] = word + ' ' + next_text
                except: 
                    continue  # Skip if there's an error (e.g., word is empty)
                
            elif next_date_match:
                complete_date = f'{text} {next_text}'
                
                corrected_extracted_words.loc[i, 'text'] = complete_date
                corrected_extracted_words.loc[i, 'x1'] = extracted_words.loc[i + 1, 'x1']
                idx_to_drop.append(i + 1)
                
            elif next_next_date_match:
                complete_date = f'{text} {next_text} {next_next_text}'
                
                corrected_extracted_words.loc[i, 'text'] = complete_date
                corrected_extracted_words.loc[i, 'x1'] = extracted_words.loc[i + 2, 'x1']
                idx_to_drop.append(i + 1)
                idx_to_drop.append(i + 2)
                
            # Handle amount correction: combine separated signs with amounts
            elif amount_match:
                previous_text = extracted_words.loc[i - 1, 'text']
                # If the previous cell contains a standalone + or - sign
                if previous_text == '+' or previous_text == '-':
                    # Combine the sign with the current amount
                    corrected_extracted_words.loc[i, 'text'] = previous_text + text
                    idx_to_drop.append(i - 1)
                    
        if idx_to_drop:
            corrected_extracted_words = corrected_extracted_words.drop(idx_to_drop)
                
        return corrected_extracted_words
    
    