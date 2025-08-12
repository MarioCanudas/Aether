import pandas as pd
import numpy as np
from logging import getLogger
from typing import List, Set, Tuple, Any
from models.bank_properties import Metadata, StatementType
from models.tables import TransactionsTable, AllTransactionsTable, MonthlyResultsTable
from models.records import TransactionRecord, MonthlyResultRecord
from .connection_management_service import ConnectionManagementService
from .database.transactions import TransactionsDBService
from .database.monthly_results import MonthlyResultDBService

logger = getLogger(__name__)

class DataValidationService:
    """
    This class is used to validate the transactions data to prevent duplicates and other errors.
    """
    def __init__(self):
        self.connection_manager = ConnectionManagementService()
        
    def get_existing_transaction_keys(self, transactions: List[TransactionRecord], user_id: int) -> Set[Tuple[Any, ...]]:
        """
        Check which transactions exist in the database in a single query
        Returns set of unique keys (date, amount, description, bank, statement_type)
        """
        if not transactions:
            return set()
          
        if not isinstance(user_id, int):
            raise ValueError("User ID must be an integer")
            
        key_columns = ['date', 'description', 'amount', 'bank', 'statement_type']
        all_params = {'user_id': user_id}
        query_values = []
        
        for i, t in enumerate(transactions):
            query_values.append('(' + ', '.join(f'%({key}_{i})s' for key in t.keys() if key in key_columns) + ')')
            for key, value in t.items():
                if key in key_columns:
                    all_params[f'{key}_{i}'] = value
            
        with self.connection_manager.get_session_connection() as conn:
            transactions_db = TransactionsDBService(conn)
            
            return transactions_db.get_existing_keys(all_params, query_values)

    def get_existing_monthly_result_keys(self, monthly_results: List[MonthlyResultRecord], user_id: int) -> Set[str]:
        """
        Check which monthly results exist in the database in a single query
        Returns set of existing year_month strings
        """
        if not monthly_results:
            return set()
        
        # Extract unique year_month values
        all_params = {f'year_month_{i}': m['year_month'] for i, m in enumerate(monthly_results, start= 1)} 
        all_params['user_id'] = user_id
        
        with self.connection_manager.get_session_connection() as conn:
            monthly_results_db = MonthlyResultDBService(conn)
            
            return monthly_results_db.get_existing_keys(all_params)
    
    @staticmethod
    def validate_transactions(transactions: TransactionsTable, metadata: Metadata) -> TransactionsTable:
        """
        Validate the transactions based on the provided metadata.

        The metadata is expected to have the following keys:
        - 'bank': The bank of the statement.
        - 'statement_type': The type of statement (credit or debit).
        - 'period': The period of the statement.
        - 'initial_balance': The initial balance of the statement.
        - 'final_balance': The final balance of the statement.

        Args:
            transactions (TransactionsTable): The transactions to validate.
            metadata (Metadata): The metadata of the statement.

        Returns:
            TransactionsTable: The validated transactions.

        Raises:
            ValueError: If the final balance does not match the expected value based on the initial balance, incomes, and expenses.
        """
        transactions_df = transactions.df.copy()

        initial_date= pd.to_datetime(metadata.period.start_date)
        final_date = pd.to_datetime(metadata.period.end_date)

        # Filter the transactions by the period
        transactions_df = transactions_df[
            (transactions_df['date'] >= initial_date) &
            (transactions_df['date'] <= final_date)
        ]

        if metadata.statement_type == StatementType.DEBIT:
            initial_balance = metadata.balances.initial
            final_balance = metadata.balances.final

            if initial_balance is not None and final_balance is not None:
                transactions_cleaned = TransactionsTable(df=transactions_df)
                all_incomes = transactions_cleaned.get_all_incomes()
                all_expenses = transactions_cleaned.get_all_expenses()

                expected_final = initial_balance + all_incomes + all_expenses
                if not np.isclose(expected_final, final_balance, atol=1e-2):
                    raise ValueError(
                        f"Final balance ({expected_final}) does not match the initial balance ({initial_balance}) "
                        f"plus incomes ({all_incomes}) and expenses ({all_expenses}). "
                        f"Expected: {final_balance}"
                    )
            else:
                logger.warning(
                    "Warning: Balances were not validated because either the initial or final balance is missing."
                )

        return TransactionsTable(df=transactions_df)

    @staticmethod
    def delete_double_transactions(transactions: AllTransactionsTable) -> AllTransactionsTable:
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
        transactions_cleaned = transactions.df.copy()

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
                
        transactions_cleaned = transactions_cleaned.drop(indices_to_remove)

        return AllTransactionsTable(df=transactions_cleaned)
    
    @staticmethod
    def validate_monthly_results(monthly_results: MonthlyResultsTable) -> MonthlyResultsTable:
        """
        """
        return monthly_results
