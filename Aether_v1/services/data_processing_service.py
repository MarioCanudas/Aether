import pandas as pd
from io import BytesIO
import os
from typing import Literal
from models import (
    PDFReader, 
    DefaultBankDetector, 
    TransactionTableBoundaryDetector, 
    TransactionRowSegmenter, 
    TransactionTableReconstructor, 
    TransactionTableNormalizer
)

class DataProcessingService:
    def __init__(self):
        self.bank_detector = None
        self.boundary_detector = None
        self.row_segmenter = None
        self.reconstructor = None
        self.normalizer = None
        
    def get_bank_detector(self, temp_file: str | BytesIO) -> DefaultBankDetector:
        """
        Get the bank detector for a given PDF file.

        Args:
            temp_file (str | BytesIO): The path to the PDF file or a BytesIO object.

        Returns:
            DefaultBankDetector: The bank detector for the given PDF file.
        """
        return DefaultBankDetector(PDFReader(temp_file))
        
    def get_transactions_from_pdf(self, temp_file: str | BytesIO) -> pd.DataFrame:
        """
        Extract transactions from a PDF document.

        Args:
            temp_file (str | BytesIO): The path to the PDF file or a BytesIO object.

        Returns:
            pd.DataFrame: A DataFrame containing the extracted transactions from the document.
        """
        bank_detector = self.get_bank_detector(temp_file)
        reader = bank_detector.document_reader
        
        boundary_detector = TransactionTableBoundaryDetector(bank_detector)
        if boundary_detector.start_idx is None or boundary_detector.end_idx is None:
            bank_detector = DefaultBankDetector(reader, new_credit_format=True)
            boundary_detector = TransactionTableBoundaryDetector(bank_detector)
        df_table = boundary_detector.get_filtered_table_words()
        
        row_segmenter = TransactionRowSegmenter(df_table, bank_detector)
        column_delimitation = row_segmenter.delimit_column_positions()
        grouped_rows = row_segmenter.group_rows()

        table_reconstructor = TransactionTableReconstructor(grouped_rows, column_delimitation, bank_detector)
        df_structured = table_reconstructor.reconstruct_table()

        table_normalizer = TransactionTableNormalizer(df_structured, bank_detector)
        df_transactions = table_normalizer.normalize_table()
        
        bank_name = bank_detector.detect_bank()
        statement_type = bank_detector.detect_statement_type()
        
        df_transactions['bank'] = bank_name
        df_transactions['statement_type'] = statement_type
        
        return df_transactions
    
    def process_uploaded_file(self, uploaded_file: BytesIO, all_transactions: list[pd.DataFrame]) -> pd.DataFrame:
        """
        Process an uploaded file and return a DataFrame containing the extracted transactions.

        Args:
            uploaded_file (BytesIO): The uploaded file to process.
            all_transactions (list[pd.DataFrame]): A list of DataFrames containing all previously processed transactions.
        """
        # Check if file was already processed (using name as identifier)
        if any(uploaded_file.name == df['filename'].iloc[0] for df in all_transactions if not df.empty):
            return pd.DataFrame()
        # Save uploaded file to a temporary path for processing
        temp_file_path = os.path.join("frontend", f"temp_uploaded_{uploaded_file.name}")
        with open(temp_file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        df_transactions = self.get_transactions_from_pdf(temp_file_path)
        df_transactions['filename'] = uploaded_file.name
        
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

        return df_transactions
    
    def combine_transactions(self, all_transactions: list[pd.DataFrame]) -> pd.DataFrame:
        """
        Combine a list of DataFrames containing transactions into a single DataFrame.

        Args:
            all_transactions (list[pd.DataFrame]): A list of DataFrames containing all previously processed transactions.
        """
        if all_transactions:
            
            for df in all_transactions:
                if 'Date' in df.columns:
                    df['Date'] = pd.to_datetime(df['Date'])
                
            df = pd.concat(all_transactions, ignore_index=True)
            return df.sort_values(by='Date', ascending=True)
        else:
            return pd.DataFrame()
        
    def delete_double_transactions(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Removes duplicate transactions from a financial dataset, specifically targeting credit card payments
        (abonos) and their corresponding debit transactions (cargos) to avoid double-counting.

        The function identifies:
        1. Credit transactions that are marked as "Abono" in the credit statement.
        2. Debit transactions that are marked as "Cargo" in the debit statement.
        3. Matches debit transactions to credit transactions based on:
            - Equal transaction amounts.
            - Debit transaction dates less than or equal to the corresponding credit transaction dates.
        4. Removes the credit transaction and the last matching debit transaction (based on the date).

        Args:
            data (pd.DataFrame): A DataFrame containing financial transaction data with the following expected columns:
                - 'statement_type': Type of statement ('credit' or 'debit').
                - 'Type': Type of transaction ('Abono' for payments, 'Cargo' for charges).
                - 'Amount': The transaction amount.
                - 'Date': The date of the transaction.

        Returns:
            pd.DataFrame: A cleaned DataFrame with duplicate transactions removed.

        Example:
            cleaned_data = delete_double_transactions(transaction_data)
        """
        data_cleaned = data.copy()

        credit_transactions = data_cleaned[
            (data_cleaned['statement_type'] == 'credit') &
            (data_cleaned['Type'] == 'Abono')
        ]
        debit_transactions = data_cleaned[
            (data_cleaned['statement_type'] == 'debit') &
            (data_cleaned['Type'] == 'Cargo')
        ]

        indices_to_remove = []

        for index, credit in credit_transactions.iterrows():
            matching_debit = debit_transactions[
                (debit_transactions['Amount'] == -credit['Amount']) &
                (debit_transactions['Date'] <= credit['Date'])
            ]

            if not matching_debit.empty:
                # Find the last matching debit based on date
                last_matching_debit = matching_debit.sort_values(by='Date').iloc[-1]
                # Add indices of credit and the last matching debit to the list
                indices_to_remove.extend([index, last_matching_debit.name])

        return data_cleaned.drop(indices_to_remove)

    def calculate_savings_and_validate_balances(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculates monthly savings and validates balances by ensuring the running total matches the provided balances.

        Args:
            data (pd.DataFrame): A DataFrame containing transaction data with 'Date', 'Description', 'Amount', 'Balance', and 'Type' columns.

        Returns:
            pd.DataFrame: A DataFrame with monthly savings and balance validation results.
        """
        # If the 'Balance' column is not present, add it with all values as None
        # Temporary fix for implementation of new model
        if not 'Balance' in data.columns:
            data['Balance'] = None
        
        # Ensure the 'Date' column is in datetime format
        data['Date'] = pd.to_datetime(data['Date'], format='%Y-%m-%d')

        # Add 'Year-Month' column for grouping
        data['Year-Month'] = data['Date'].dt.to_period('M')

        # Initialize a list to store results
        results = []

        # Group data by 'Year-Month'
        grouped = data.groupby('Year-Month')

        for name, group in grouped:
            # Sort by date within the group for proper calculations
            group = group.sort_values(by='Date')

            # Extract the initial balance from "Saldo inicial"
            initial_balance_row = group[group['Type'] == 'Saldo Inicial']
            initial_balance = initial_balance_row['Balance'].values[0] if not initial_balance_row.empty else None

            # Calculate total income and withdrawals
            total_income = group[group['Type'] == 'Abono']['Amount'].sum()
            total_withdrawal = group[group['Type'] == 'Cargo']['Amount'].sum()

            # Calculate savings
            savings = total_income + total_withdrawal  # Withdrawals are negative, so adding them works here

            # Validate balances
            running_sum = initial_balance if initial_balance is not None else 0
            balance_valid = True
            for _, row in group.iterrows():
                running_sum += row['Amount']
                if pd.notnull(row['Balance']) and abs(running_sum - row['Balance']) > 1e-2:
                    balance_valid = False
                    break

            # Append results
            results.append({
                'Month': name,
                'initial_balance': initial_balance,
                'total_income': total_income,
                'total_withdrawal': total_withdrawal,
                'savings': savings,
                'balance_valid': balance_valid
            })

        # Convert results to DataFrame
        results_df = pd.DataFrame(results)
        return results_df
    
    def process_daily_data_by_category(self, data: pd.DataFrame, category: Literal['Abono', 'Cargo']) -> pd.Series:
        """
        Process daily data by calculating the average income and expenses per day.

        Args:
            data (pd.DataFrame): A DataFrame containing transaction data with 'Date', 'Income', and 'Withdrawal' columns.

        Returns:
            pd.DataFrame: A DataFrame with the average income and expenses per day.
        """
        data['Date'] = pd.to_datetime(data['Date'])
        
        filtered_data = data[data['Type'] == category]
        
        filtered_data['Day'] = filtered_data['Date'].dt.day
        
        # Average income by day of the month
        avg_per_day = filtered_data.groupby('Day')['Amount'].mean().reindex(range(1, 32), fill_value=0)
        
        return avg_per_day    