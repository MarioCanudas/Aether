from core import TableReconstructor
import pandas as pd
import re
from functools import cached_property

def is_amount(value: str) -> bool:
    # Ignore the empty strings
    if value == '':
        return True
    
    amount_pattern = r'^[+-]?\$?[+-]?(0|[1-9]\d{0,2}(?:,\d{3})*)\.\d{2}[-+]?$'

    return bool(re.match(amount_pattern, value.strip()))

class TransactionTableReconstructor(TableReconstructor):
    @cached_property
    def column_positions(self) -> dict:
        x0_list = self.column_delimitation['x0']
        x1_list = self.column_delimitation['x1']
        
        statement_properties = self.bank_detector.get_statement_properties()
        date_column = statement_properties['date_column']
        description_column = statement_properties['description_column']
        amounts_columns = statement_properties['amount_column']
        columns = statement_properties['columns']
        
        positions = {}
        
        for i, col in enumerate(columns):
            if col == date_column:
                positions[col] = (0, x1_list[i] + 10) if statement_properties['date_treshold_adjust'] else (0, x1_list[i])
            elif col == description_column:
                positions[col] = (x1_list[i - 1] + 1, x0_list[i + 1]- 25) # Adjusted for description column
            elif col in amounts_columns:
                positions[col] =   (x1_list[i - 1] + 10, x1_list[i] + 10) if statement_properties['amount_treshold_adjust'] else (x0_list[i] - 15, x1_list[i])
            else:
                positions[col] = (x0_list[i] - 10, x1_list[i])
        
        return positions

    def classify_columns(self, row) -> pd.Series:
        columns = {col: "" for col in self.column_positions.keys()}

        statement_properties = self.bank_detector.get_statement_properties()
        date_column = statement_properties['date_column']
        amount_columns = statement_properties['amount_column']
        description_column = statement_properties['description_column']

        date_pattern = statement_properties['date_pattern']

        words = row['words']

        for text, x0, x1 in words:
            for col, (start_x, end_x) in self.column_positions.items():
                if start_x <= x0 <= end_x:
                    if col in amount_columns and is_amount(text):
                        columns[col] += text + " "
                        break
                    elif col in amount_columns and not is_amount(text):
                        columns[description_column] += text + " "
                        break
                    else:
                        columns[col] += text + " "  # Append word to column
                        break
                    

        return pd.Series(columns)
    
    def get_structured_table(self) -> pd.DataFrame:
        df_classified = self.grouped_rows.apply(self.classify_columns, axis=1)
        df_classified = df_classified.map(lambda x: x.strip())
        
        return df_classified.reset_index(drop=True)
    
    def reconstruct_table(self) -> pd.DataFrame:
        df_structured = self.get_structured_table()
        
        merged_rows = []
        current_row = None
        
        statement_properties = self.bank_detector.get_statement_properties()
        description_column = statement_properties['description_column']
        date_column = statement_properties['date_column']
        amount_columns = statement_properties['amount_column']
        date_pattern = statement_properties['date_pattern']

        for _, row in df_structured.iterrows():
            if row[date_column]!='':  # New transaction row
                if current_row is not None:
                    merged_rows.append(current_row)  # Save the last completed row
                current_row = row.copy()  # Start a new row
            elif current_row is not None:  # Continuation row
                for col in amount_columns:
                    if row[col] != '' and current_row[col] == '':
                        current_row[col] = row[col]
                    else:
                        continue
            else:  # Continuation row
                try:
                    current_row[description_column] += " " + row[description_column]  # Merge description
                except: 
                    continue

        if current_row is not None:
            merged_rows.append(current_row)  # Append last row

        df_merged = pd.DataFrame(merged_rows)
        
        return df_merged[df_merged[date_column].str.match(date_pattern, na=False)].reset_index(drop=True)