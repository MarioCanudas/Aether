from psycopg2.extensions import connection
import asyncio
import pandas as pd
from typing import cast
from models.dates import Period
from models.transactions import Transaction, DuplicateResult
from .database.transactions import TransactionsDBService

class DuplicateTreatmentService:
    """
    This service is used to detect and treat duplicate transactions.
    """
    @staticmethod
    def get_transactions_period(transactions: list[Transaction]) -> Period:
        dates = [transaction.date for transaction in transactions]
        
        return Period(start_date= min(dates), end_date= max(dates))  
        
    @staticmethod
    async def _determine_transaction_duplicates(transaction: Transaction, existing_transactions: list[Transaction]) -> DuplicateResult:
        exact_duplicates_task: list[asyncio.Task[bool]] = []
        potential_duplicates_task: list[asyncio.Task[bool]] = []
        
        for t in existing_transactions:
            exact_duplicates_task.append(asyncio.create_task(transaction.exact_duplicate(t)))
            potential_duplicates_task.append(asyncio.create_task(transaction.potencial_duplicate(t)))
            
        exact_duplicates: list[bool] = await asyncio.gather(*exact_duplicates_task)
        potential_duplicates: list[bool] = await asyncio.gather(*potential_duplicates_task)
        
        if any(potential_duplicates):
            transaction.duplicate_potential_state = True

        exactly_duplicates_transactions: list[Transaction] = []
        potential_duplicates_transactions: list[Transaction] = []
        
        # The transaction could be and exact and potential duplicate at the same time.
        # So we need to iterate over the transaction and the boolean values to determine the type of duplicate
        # by checking first for exact and then for potential, so if the transaction is an exact and potential duplicate,
        # it will be added to the exactly_duplicates_transactions list.
        for t, exact, potential in zip(existing_transactions, exact_duplicates, potential_duplicates):
            if exact:
                exactly_duplicates_transactions.append(t)
            elif potential:
                t.duplicate_potential_state = True
                potential_duplicates_transactions.append(t)
        
        return DuplicateResult(
            transaction= transaction,
            exact_duplicates= exactly_duplicates_transactions,
            potential_duplicates= potential_duplicates_transactions
        )
        
    async def detect_duplicates(
            self, 
            conn: connection, 
            user_id: int, 
            transactions: list[Transaction] | Transaction
        ) -> list[DuplicateResult] | DuplicateResult:
        if isinstance(transactions, Transaction):
            transactions = [transactions]
        if not transactions:
            raise ValueError('No transactions provided')
        
        transactions_db = TransactionsDBService(conn)
        period = self.get_transactions_period(transactions)
        
        existing_transactions = transactions_db.get_transactions(
            user_id= user_id, 
            columns= ['user_id', 'transaction_id', 'category_id', 'date', 'amount', 'type', 'bank', 'card_id', 'statement_type'],
            period= period,
        )
        existing_transactions = cast(list[Transaction], existing_transactions)
        
        tasks: list[asyncio.Task[DuplicateResult]] = []
        
        for t in transactions:
            task = asyncio.create_task(self._determine_transaction_duplicates(t, existing_transactions))
            tasks.append(task)
            
        results: list[DuplicateResult] = await asyncio.gather(*tasks)
        
        if len(results) == 1:
            return results[0]
        else:
            return results
        
    @staticmethod
    def eliminate_credit_and_debit_duplicates(transactions: list[Transaction]) -> tuple[list[Transaction], list[Transaction]]:
        """
        Classificates the duplicate transactions from a financial dataset, specifically targeting credit card payments
        (abonos) and their corresponding debit transactions (cargos) to avoid double-counting.

        The function identifies:
        1. Credit transactions that are marked as "Abono" in the credit statement.
        2. Debit transactions that are marked as "Cargo" in the debit statement.
        3. Matches debit transactions to credit transactions based on:
            - Equal transaction amounts.
            - Debit transaction dates less than or equal to the corresponding credit transaction dates..

        Args:
            transactions (AllTransactionsTable): A table containing financial transaction data with the following expected columns:
                - 'statement_type': Type of statement ('credit' or 'debit').
                - 'type': Type of transaction ('Abono' for payments, 'Cargo' for charges).
                - 'amount': The transaction amount.
                - 'date': The date of the transaction.

        Returns:
            Tuple[List[Transaction], List[Transaction]]: A tuple containing the not duplicated and duplicated transactions.
        """
        transactions_cleaned = [t.model_dump() for t in transactions]
        df = pd.DataFrame(transactions_cleaned)

        credit_transactions = df[(df['statement_type'] == 'credit') & (df['type'] == 'Abono')]
        debit_transactions = df[(df['statement_type'] == 'debit') & (df['type'] == 'Cargo')]

        indices_to_remove = []

        for index, credit in credit_transactions.iterrows():
            matching_debit = debit_transactions[
                (debit_transactions['amount'] == -credit['amount']) &
                (debit_transactions['date'] <= credit['date'])
            ]
            
            matching_debit = cast(pd.DataFrame, matching_debit)

            if not matching_debit.empty:
                # Find the last matching debit based on date
                last_matching_debit = matching_debit.sort_values(by='date').iloc[-1]
                # Add indices of credit and the last matching debit to the list
                indices_to_remove.extend([index, last_matching_debit.name])
                
        duplicated = df.iloc[indices_to_remove]
        not_duplicated = df.drop(indices_to_remove)
        
        return (
            [Transaction(**t) for t in not_duplicated.to_dict(orient='records')],
            [Transaction(**t) for t in duplicated.to_dict(orient='records')]
        )
