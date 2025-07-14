import pandas as pd
from typing import Dict, Any, List, Set, Tuple
from .database_service import DatabaseService

class DataValidationService:
    """
    This class is used to validate the transactions data to prevent duplicates and other errors.
    """
    @staticmethod
    def get_existing_transaction_keys(
        db_service: DatabaseService, 
        transactions: List[Dict[str, Any]], 
        user_id: int
    ) -> Set[Tuple]:
        """
        Check which transactions exist in the database in a single query
        Returns set of unique keys (filename, date, amount, description)
        """
        if not transactions:
            return set()
        
        # Prepare parameters for batch query
        params_list = []
        for t in transactions:
            params = {
                'filename': t['filename'],
                'date': t['date'].strftime('%Y-%m-%d') if hasattr(t['date'], 'strftime') else t['date'],
                'amount': t['amount'],
                'description': t['description'],
                'user_id': user_id
            }
            params_list.append(params)
        
        # Single query to check all transactions
        query = """
        SELECT filename, date, amount, description 
        FROM transactions
        WHERE (filename, date, amount, description, user_id) IN (
            VALUES {}
        )
        """.format(
            ", ".join([f"(:filename_{i}, :date_{i}, :amount_{i}, :description_{i}, :user_id_{i})" 
                      for i in range(len(params_list))])
        )
        
        # Flatten parameters
        flat_params = {}
        for i, params in enumerate(params_list):
            for key, value in params.items():
                flat_params[f"{key}_{i}"] = value
        
        # Execute query
        existing = db_service.custom_query(query, flat_params, value_format='dict')
        
        # Return as set of tuples for fast lookup
        return {
            (e['filename'], e['date'], e['amount'], e['description'])
            for e in existing
        }
        
    @staticmethod
    def get_existing_monthly_result_keys(
        db_service: DatabaseService, 
        monthly_results: List[Dict[str, Any]], 
        user_id: int
    ) -> Set[str]:
        """
        Check which monthly results exist in the database in a single query
        Returns set of existing year_month strings
        """
        if not monthly_results:
            return set()
        
        # Extract unique year_month values
        year_months = {r['year_month'] for r in monthly_results}
        placeholders = ', '.join([f':year_month_{i}' for i in range(len(year_months))])
        
        # Single query to check all year_months
        query = f"""
        SELECT year_month 
        FROM monthly_results
        WHERE user_id = :user_id
        AND year_month IN ({placeholders})
        """
        
        params = {
            'user_id': user_id,
            **{f'year_month_{i}': year_month for i, year_month in enumerate(year_months)}
        }
        
        existing = db_service.custom_query(query, params, value_format='dict')
        
        # Return as set of year_month strings
        return {e['year_month'] for e in existing}
    
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
    
    @staticmethod
    def validate_monthly_results(monthly_results: pd.DataFrame) -> pd.DataFrame:
        """
        """
        
        monthly_results_cleaned = monthly_results.copy()
        
        # Implement balance validation, for now just set all to True
        monthly_results_cleaned['balance_valid'] = True
        
        return monthly_results_cleaned