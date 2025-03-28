from core import TableReconstructor
import pandas as pd

class TransactionTableReconstructor(TableReconstructor):
    @property
    def header_row(self) -> float:
        colums_row = " ".join(self.statement_propertys['columns'])
        return self.grouped_rows[self.grouped_rows['text'].str.contains(colums_row, na= False)].iloc[0]
    
    @property
    def column_positions(self) -> dict:
        x0_list = self.header_row['x0']
        x1_list = self.header_row['x1']
        
        columns = self.statement_propertys['columns']
        
        return {
            col : (x0_list[i] - 10, x1_list[i]) for i, col in enumerate(columns)
        }
    
    def classify_columns(self, row) -> pd.Series:
        columns = {col: "" for col in self.column_positions.keys()}

        for i, (word, x0, x1) in enumerate(zip(row["text"].split(), row["x0"], row["x1"])):
            for col, (start_x, end_x) in self.column_positions.items():
                if start_x <= x0 <= end_x:
                    columns[col] += word + " "  # Append word to column

        return pd.Series(columns)
    
    def get_structured_table(self) -> pd.DataFrame:
        df_structured = self.grouped_rows[self.grouped_rows["row_group"] > self.header_row["row_group"]].apply(self.classify_columns, axis=1)
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