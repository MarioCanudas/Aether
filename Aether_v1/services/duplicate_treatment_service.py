from psycopg2.extensions import connection
from dateutil import relativedelta
from functools import cache
from typing import Optional, Set, Tuple, List, Dict, Any
from models.dates import Period
from models.transactions import Transaction, DuplicateTransactionType
from .database.transactions import TransactionsDBService
from models.tables import AllTransactionsTable

class DuplicateTreatmentService:
    """
    This service is used to detect and treat duplicate transactions.
    """
    def get_potential_duplicates(self, conn: connection, user_id: int, period: Optional[Period] = None) -> List[Optional[Transaction]]:
        transactions_db = TransactionsDBService(conn)
        
        potential_duplicates = transactions_db.get_transactions(
            user_id= user_id,
            period= period,
            duplicate_potential_state= DuplicateTransactionType.POTENTIAL,
        )
        
        return potential_duplicates
    
    @staticmethod
    def get_transactions_period(transactions: List[Transaction]) -> Period:
        dates = [transaction.date for transaction in transactions]
        
        return Period(start_date= min(dates), end_date= max(dates))    
    
    @staticmethod
    def _is_exact_duplicate(transaction: Transaction, existing_keys: Set[Tuple[Any, ...]]) -> bool:
        ... 
        
    @staticmethod
    def _is_potential_duplicate(transaction: Transaction, existing_keys: Set[Tuple[Any, ...]]) -> bool:
        ...
        
    def detect_duplicates(
            self, 
            conn: connection, 
            user_id: int, 
            transactions: List[Transaction] | Transaction
        ) -> Dict[Transaction, DuplicateTransactionType] | DuplicateTransactionType:
        if isinstance(transactions, Transaction):
            transactions = [transactions]
        if not transactions:
            raise ValueError('No transactions provided')
        
        transactions_db = TransactionsDBService(conn)
        period = self.get_transactions_period(transactions)
        
        existing_keys = transactions_db.get_existing_keys(user_id= user_id, period= period)
        
        duplicates = {}
        
        for transaction in transactions:
            if self._is_exact_duplicate(transaction, existing_keys):
                duplicates[transaction] = DuplicateTransactionType.EXACT
            elif self._is_potential_duplicate(transaction, existing_keys):
                duplicates[transaction] = DuplicateTransactionType.POTENTIAL
            else:
                duplicates[transaction] = DuplicateTransactionType.NULL
                
        return duplicates if len(transactions) > 1 else duplicates[transactions[0]]
        
    @cache
    def get_similar_transactions(self, conn: connection, transaction: Transaction, ids: Optional[bool] = False) -> List[Transaction]:
        if not transaction.duplicate_potential_state:
            return None
        
        transactions_db = TransactionsDBService(conn)
        
        period = Period(start_date= transaction.date - relativedelta(days= 5), end_date= transaction.date + relativedelta(days= 5))
        transactions = transactions_db.get_transactions(user_id= transaction.user_id, period= period, duplicate_potential_state= True)
        
        similar_transactions: List[Transaction] = []
        for t in transactions:
            if self._is_potential_duplicate(transaction, t.to_tuple(key= True)):
                similar_transactions.append(t)
        
        return similar_transactions
        
    def eliminate_duplicates(self, conn: connection, transaction: Transaction) -> None:
        similar_transactions = self.get_similar_transactions(conn, transaction)
        
        transactions_db = TransactionsDBService(conn)
        transactions_db.delete_transactions(similar_transactions)
        
    def eliminate_credit_and_debit_duplicates(self, transactions: AllTransactionsTable) -> Tuple[List[Transaction], List[Transaction]]:
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
            Tuple[List[Transaction], List[Transaction]]: A tuple containing the duplicated and not duplicated transactions.
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
                
        duplicated = transactions_cleaned.iloc[indices_to_remove]
        not_duplicated = transactions_cleaned.drop(indices_to_remove)
        
        return [Transaction(**t) for t in duplicated], [Transaction(**t) for t in not_duplicated]
