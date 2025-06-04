from core import DataExporter
import pandas as pd 

class CsvExporter(DataExporter):
    def export_to_csv(self, file_path):
        """
        Exports the normalized transaction table to a CSV file.

        Args:
            file_path (str): Path to the output CSV file.
        """
        self.df_table.to_csv(file_path, index=False)
        print(f"Data exported to {file_path} successfully.")