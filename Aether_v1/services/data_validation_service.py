import pandas as pd
import numpy as np
from logging import getLogger
from models.bank_properties import Metadata, StatementType
from models.tables import TransactionsTable

logger = getLogger(__name__)

class DataValidationService:
    """
    This class is used to validate the transactions data to prevent duplicates and other errors.
    """
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
        
        transactions_df['date'] = pd.to_datetime(transactions_df['date'])

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
