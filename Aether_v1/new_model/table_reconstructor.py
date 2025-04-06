from core import TableReconstructor
import pandas as pd

class TransactionTableReconstructor(TableReconstructor):
    def get_columns_row(self) -> float:
        colums_row = " ".join(self.statement_propertys['columns_row'])
        return self.grouped_rows[self.grouped_rows['text'].str.contains(colums_row, na= False)].iloc[0]
    
    @property
    def column_positions(self) -> dict:
        x0_list = self.header_row['x0']
        x1_list = self.header_row['x1']
        
        date_column = self.statement_propertys['date_column']
        description_column = self.statement_propertys['description_column']
        columns = self.statement_propertys['columns']
        
        positions = {}
        
        for i, col in enumerate(columns):
            if col == date_column:
                positions[col] = (0, x1_list[i])
            elif col == description_column:
                positions[col] = (x1_list[i - 1]+ 10, x0_list[i + 1]- 20) # Adjusted for description column
            else:
                positions[col] = (x0_list[i] - 10, x1_list[i])
        
        return positions
    
    def classify_columns(self, row) -> pd.Series:
        columns = {col: "" for col in self.column_positions.keys()}
        
        words = row['words']

        for i, (text, x0, x1) in enumerate(words):
            for col, (start_x, end_x) in self.column_positions.items():
                if start_x <= x0 <= end_x:
                    columns[col] += text + " "  # Append word to column

        return pd.Series(columns)
    
    def get_structured_table(self) -> pd.DataFrame:
        columns_row = self.get_columns_row()
        df_structured = self.grouped_rows[self.grouped_rows["row_group"] > columns_row["row_group"]].apply(self.classify_columns, axis=1)
        df_structured = df_structured.map(lambda x: x.strip())
        
        merged_rows = []
        current_row = None
        
        description_column = self.statement_propertys['description_column']
        date_column = self.statement_propertys['date_column']
        date_pattern = self.statement_propertys['date_pattern']

        for _, row in df_structured.iterrows():
            if row[date_column]!='':  # New transaction row
                if current_row is not None:
                    merged_rows.append(current_row)  # Save the last completed row
                current_row = row.copy()  # Start a new row
            else:  # Continuation row
                current_row[description_column] += " " + row[description_column]  # Merge description

        if current_row is not None:
            merged_rows.append(current_row)  # Append last row

        df_merged = pd.DataFrame(merged_rows)
        
        return df_merged[df_merged[date_column].str.match(date_pattern, na=False)].reset_index(drop=True)