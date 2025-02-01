import pandas as pd
import os
from typing import Literal
from config import DATA_FOLDER

class TableManager:
    def __init__(self, table_name: Literal['user', 'bank', 'card', 'category', 'transaction', 'document', 'financialgoal', 'budget']):
        self.table_name = table_name
        self.path_csv_file = os.path.join(DATA_FOLDER, f'{table_name}.csv')
        
    def load_data(self) -> pd.DataFrame:
        """
        Load the data of the table by the table name given in the constructor
        
        Returns:
            pd.DataFrame: Data of the table
            
        Raises:
            FileNotFoundError: If the file is not found
        """
        if not os.path.exists(self.path_csv_file):
            raise FileNotFoundError(f'File {self.path_csv_file} not found')
        else:
            return pd.read_csv(self.path_csv_file, encoding='latin1', index_col= None)
        
    def validate_foreign_column(self, column: str) -> bool:
        """
        Validate if a column is a foreign key in the table.
        
        Args:
            column (str): Column to validate
        
        Returns:
            bool: True if the column is a foreign key, False otherwise
        """
        df = self.load_data()
        
        return column in df.columns
        
    def validate_foreign_key(self, column_key: str, key: str) -> bool:
        """
        Validate if a key is a foreign key in the table.

        Args:
            key (str): Valuse to validate
            column_key (str): Column where the key is located.

        Returns:
            bool: True if the key is valid, False otherwise.
        """
        df = self.load_data()
        
        if self.validate_foreign_column(column_key):
            return key in df[column_key].values
        else:
            KeyError(f'Column: {column_key} not found in table {self.table_name}')
        
    def filter_data(self, *column :str) -> pd.DataFrame:
        """
        Filter the data of the table by the columns given in the arguments
        
        Args:
            *column (str): Columns to filter the data
        
        Returns:
            pd.DataFrame: Filtered data by the given columns
            
        Raises:
            KeyError: If the column is not in the table
        """
        df = self.load_data()
        
        if type(column) == str and column in df.columns:
            return df[[column]]
        elif type(column) == list and all([col in df.columns for col in column]):
            return df[column]
        else:
            raise TypeError('The column must be a string or a list of strings')
    
    def acces_to_value(self, key: str, column_key: str, column_value: str) -> any:
        """
        Get the specific value of a column with the key of the row
        
        Args:
            key (str): Key to get the value
            column_key (str): Column where the key is located
            column_value (str): Column where the value is located
            
        Returns:
            any: Value of the column_value
            
        Raises:
            KeyError: If the column_key is not in the table
        """
        df = self.load_data()
        
        if column_key not in df.columns:
            raise KeyError(f'Column: {column_key} not foun in table {self.table_name}')
        elif column_value not in df.columns:
            raise KeyError(f'Column: {column_value} not foun in table {self.table_name}')
        elif key not in df[column_key].values:
            raise KeyError(f'Key: {key} not foun in column {column_key} of table {self.table_name}')
        else:
            return df.loc[df[column_key] == key, column_value].values[0]
        
    def unique_values(self, column: str) -> list:
        """
        Get the unique values of a column
        
        Args:
            column (str): Column to get the unique values
        
        Returns:
            list: Unique values of the column
            
        Raises:
            KeyError: If the column is not in the table
        """
        df = self.load_data()
        
        if column not in df.columns:
            raise KeyError(f'Column: {column} not foun in table {self.table_name}')
        else:
            return df[column].unique().tolist()
        
    def add_row(self, row: dict) -> pd.DataFrame:
        """
        Add a row to the table, **withaout save the changes**.
        
        Args:
            row (dict): Row to add to the table
            
        Returns:
            pd.DataFrame: Data with the new row added
            
        Raises:
            ValueError: If the columns of the row are invalid
            
        """
        df = self.load_data().copy()
        
        missing_columns = [col for col in df.columns if col not in row]
        extra_columns = [col for col in row if col not in df.columns]
        
        if missing_columns or extra_columns:
            raise ValueError(f'Invalid columns: missing {missing_columns} and extra {extra_columns}')
        
        new_row = pd.DataFrame([row])
        new_df = pd.concat([df, new_row], ignore_index= True)
        
        return new_df
        
    def save_data(self, df: pd.DataFrame) -> None:
        """
        Save the changes data in the csv file
        
        Args:
            df (pd.DataFrame): Data with the change to save, because all the changes must be made in a copy of the original data.
        
        Raises:
            FileNotFoundError: If the file is not found
        """
        if not os.path.exists(self.path_csv_file):
            raise FileNotFoundError(f'File {self.path_csv_file} not found')
        else:
            df.to_csv(self.path_csv_file, index= False, encoding= 'latin1')
        
    def refresh_data(self) -> pd.DataFrame:
        """
        Refresh the data of the table, for see the changes
        
        Returns:
            pd.DataFrame: Updated data of the table
        
        Raises:
            FileNotFoundError: If the file is not found
        """
        if not os.path.exists(self.path_csv_file):
            raise FileNotFoundError(f'File {self.path_csv_file} not found')
        else:
            return self.load_data()
        