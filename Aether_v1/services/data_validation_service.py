import pandas as pd
from typing import Dict, Any
from .database_service import DatabaseService

class DataValidationService:
    """
    This class is used to validate the transactions data to prevent duplicates and other errors.
    """
    @staticmethod
    def check_if_transaction_exists_in_db(db_service: DatabaseService, transaction: Dict[str, Any]) -> bool:
        query = """
        SELECT EXISTS(
            SELECT 1 FROM transactions
            WHERE filename = :filename
            AND date = :date 
            AND amount = :amount 
            AND description = :description
        )       
        """
        
        check_values = ['filename', 'date', 'amount', 'description']
        params = {col: transaction[col] for col in check_values}
        params['date'] = params['date'].strftime('%Y-%m-%d') if hasattr(params['date'], 'strftime') else params['date']
        
        return db_service.custom_query(query, params, value_format='scalar')
    
    @staticmethod
    def check_if_monthly_result_exists_in_db(db_service: DatabaseService, monthly_result: Dict[str, Any]) -> bool:
        query = """
        SELECT EXISTS(
            SELECT 1 FROM monthly_results
            WHERE year_month = :year_month
        )
        """
        
        params = {'year_month': monthly_result['year_month']}
        
        return db_service.custom_query(query, params, value_format='scalar')
    
    @staticmethod
    def delete_double_transactions(transactions: pd.DataFrame) -> pd.DataFrame:
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
        transactions_cleaned = transactions.copy()

        credit_transactions = transactions_cleaned[
            (transactions_cleaned['statement_type'] == 'credit') &
            (transactions_cleaned['type'] == 'Abono')
        ]
        debit_transactions = transactions_cleaned[
            (transactions_cleaned['statement_type'] == 'debit') &
            (transactions_cleaned['type'] == 'Cargo')
        ]

        indices_to_remove = []

        for index, credit in credit_transactions.iterrows():
            matching_debit = debit_transactions[
                (debit_transactions['amount'] == -credit['amount']) &
                (debit_transactions['date'] <= credit['date'])
            ]

            if not matching_debit.empty:
                # Find the last matching debit based on date
                last_matching_debit = matching_debit.sort_values(by='date').iloc[-1]
                # Add indices of credit and the last matching debit to the list
                indices_to_remove.extend([index, last_matching_debit.name])

        return transactions_cleaned.drop(indices_to_remove)