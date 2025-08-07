from typing import Protocol
import pandas as pd

class DataExporter(Protocol):
    """
    Base class for exporting the normalized transaction table to a database.

    Attributes:
        df_table (pd.DataFrame): DataFrame containing the normalized transaction table.
    """

    def __init__(self, df_table: pd.DataFrame):
        self.df_table = df_table.copy()

    def export_data(self, file_path: str) -> None:
        """
        Export the normalized transaction table.

        Args:
            file_path (str): Path to export the data.
        """
        pass
    
class CsvExporter:
    def __init__(self, df_table: pd.DataFrame):
        self.df_table = df_table.copy()
        
    def export_data(self, file_path: str) -> None:
        self.df_table.to_csv(file_path, index=False)