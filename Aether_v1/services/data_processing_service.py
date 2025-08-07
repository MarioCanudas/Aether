import pandas as pd
from io import BytesIO
import os
from typing import Literal, List, Dict, Any
from models import DocumentProcessingFacade, TableProcessingFacade, DataProcessingFacade

class DataProcessingService:
    """
    The DataProcessingService class manages the main components required for processing bank statement PDFs. 
    The following objects are initialized in the constructor:

    - doc_processor: An instance of DocumentProcessingFacade, responsible for reading the PDF file, extracting words, 
      and analyzing document-level properties such as bank type and statement metadata.

    - table_processor: An instance of TableProcessingFacade, which uses the corrected extracted words and statement 
      properties to detect table boundaries, segment columns and rows, and reconstruct the transaction table structure.

    - data_processor: An instance of DataProcessingFacade, which takes the reconstructed table, corrected words, and 
      statement properties to extract metadata (such as period and initial balance) and normalize the transaction data 
      for further analysis.

    These objects work together to transform a raw PDF bank statement into a structured and normalized DataFrame of transactions.
    """
    @staticmethod
    def get_monthly_results(
            data: pd.DataFrame, 
            return_type: Literal['dataframe', 'records'] = 'records'
        ) -> pd.DataFrame | List[Dict[str, Any]]:
        """
        Calculates monthly savings and validates balances by ensuring the running total matches the provided balances.

        Args:
            data (pd.DataFrame): A DataFrame containing transaction data with 'Date', 'Description', 'Amount', 'Balance', and 'Type' columns.
            return_type (Literal['dataframe', 'records']): The type of return value.

        Returns:
            pd.DataFrame | List[Dict[str, Any]]: A DataFrame with monthly savings and balance validation results or a list of records.
        """
        # Ensure the 'Date' column is in datetime format
        data['date'] = pd.to_datetime(data['date'], format='%Y-%m-%d')

        # Add 'Year-Month' column for grouping
        data['year_month'] = data['date'].dt.to_period('M')

        # Initialize a list to store results
        results = []

        # Group data by 'Year-Month'
        grouped = data.groupby('year_month')

        for year_month, group in grouped:
            # Sort by date within the group for proper calculations
            group = group.sort_values(by='date')

            # Extract the initial balance from "Saldo inicial"
            initial_balance_row = group[group['type'] == 'Saldo inicial']
            initial_balance = initial_balance_row['amount'].values[0] if not initial_balance_row.empty else None

            # Calculate total income and withdrawals
            total_income = group[group['type'] == 'Abono']['amount'].sum()
            total_withdrawal = group[group['type'] == 'Cargo']['amount'].sum()

            # Calculate savings
            savings = total_income + total_withdrawal  # Withdrawals are negative, so adding them works here

            # Append results
            results.append({
                'year_month': year_month.to_timestamp(),
                'initial_balance': initial_balance if initial_balance is not None else 0,
                'total_income': total_income,
                'total_withdrawal': total_withdrawal,
                'savings': savings,
            })

        if return_type == 'dataframe':
            return pd.DataFrame(results)
        elif return_type == 'records':
            return results
        else:
            raise ValueError("Invalid return type. Must be 'dataframe' or 'records'")
    
    @staticmethod
    def process_daily_data_by_category(data: pd.DataFrame, category: Literal['Abono', 'Cargo']) -> pd.Series:
        """
        Process daily data by calculating the average income and expenses per day.

        Args:
            data (pd.DataFrame): A DataFrame containing transaction data with 'Date', 'Income', and 'Withdrawal' columns.

        Returns:
            pd.DataFrame: A DataFrame with the average income and expenses per day.
        """
        data['date'] = pd.to_datetime(data['date'])
        
        filtered_data = data[data['type'] == category]
        
        filtered_data['day'] = filtered_data['date'].dt.day
        
        # Average income by day of the month
        avg_per_day = filtered_data.groupby('day')['amount'].mean().reindex(range(1, 32), fill_value=0)
        
        return avg_per_day    