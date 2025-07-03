import pandas as pd
from io import BytesIO
import os
from typing import Literal
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
    def __init__(self):
        self.doc_processor = None
        self.table_processor = None
        self.data_processor = None
        
    def set_document_processor(self, file: str | BytesIO) -> None:
        """
        Set the document processor for the data processing service.

        Args:
            file (str | BytesIO): The path to the PDF file or a BytesIO object.
        """
        if isinstance(file, str) or isinstance(file, BytesIO):
            self.doc_processor = DocumentProcessingFacade(file)
        else:
            raise ValueError("File must be a string or a BytesIO object")
        
    def set_table_processor(self, corrected_extracted_words: pd.DataFrame, statement_properties: dict) -> None: 
        """
        Set the table processor for the data processing service.

        Args:
            corrected_extracted_words (pd.DataFrame): The corrected extracted words.
            statement_properties (dict): The statement properties.
        """
        if self.doc_processor is None:
            raise ValueError("Document processor must be set before table processing")
        elif corrected_extracted_words.empty or statement_properties is None:
            raise ValueError("Corrected extracted words and statement properties must be set before table processing")
        else:
            self.table_processor = TableProcessingFacade(corrected_extracted_words, statement_properties)
        
    def set_data_processor(self, corrected_extracted_words: pd.DataFrame, reconstructed_table: pd.DataFrame, statement_properties: dict) -> None:
        """
        Set the data processor for the data processing service.

        Args:
            corrected_extracted_words (pd.DataFrame): The corrected extracted words.
            reconstructed_table (pd.DataFrame): The reconstructed table.
            statement_properties (dict): The statement properties.
        """
        if self.doc_processor is None or self.table_processor is None:
            raise ValueError("Document and table processors must be set before data processing")
        elif corrected_extracted_words.empty or reconstructed_table.empty or statement_properties is None:
            raise ValueError("Corrected extracted words, reconstructed table, and statement properties must be set before data processing")
        else:
            self.data_processor = DataProcessingFacade(corrected_extracted_words, reconstructed_table, statement_properties)
        
    def get_transactions_from_pdf(self, temp_file: str | BytesIO) -> pd.DataFrame:
        """
        Extract transactions from a PDF document.

        Args:
            temp_file (str | BytesIO): The path to the PDF file or a BytesIO object.

        Returns:
            pd.DataFrame: A DataFrame containing the extracted transactions from the document.
        """
        self.set_document_processor(temp_file)
        
        statement_properties = self.doc_processor.get_statement_properties()
        corrected_extracted_words = self.doc_processor.get_corrected_extracted_words()
        
        self.set_table_processor(corrected_extracted_words, statement_properties)
        reconstructed_table = self.table_processor.reconstruct_table()
        
        self.set_data_processor(corrected_extracted_words, reconstructed_table, statement_properties)
        df_transactions = self.data_processor.get_normalized_table()
        
        df_transactions['bank'] = statement_properties['bank']
        df_transactions['statement_type'] = statement_properties['statement_type']
        
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
    
    @staticmethod
    def combine_transactions(all_transactions: list[pd.DataFrame]) -> pd.DataFrame:
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
    
    @staticmethod
    def delete_double_transactions(data: pd.DataFrame) -> pd.DataFrame:
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

    @staticmethod
    def calculate_savings_and_validate_balances(data: pd.DataFrame) -> pd.DataFrame:
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
    
    @staticmethod
    def process_daily_data_by_category(data: pd.DataFrame, category: Literal['Abono', 'Cargo']) -> pd.Series:
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