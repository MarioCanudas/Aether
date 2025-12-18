from typing import Any, Literal, cast
from decimal import Decimal
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from models.amounts import TransactionType
from models.bank_properties import BankName, StatementType
from models.dates import Period
from models.financial import FinancialAmountsSums
from models.transactions import Transaction
from models.views_data import AnalysisAmountsPerPeriod
from .base_db import BaseDBService

class TransactionsDBService(BaseDBService):
    # Table information
    table_name: str = 'transactions'
    allowed_columns: set[str] = {'transaction_id', 'user_id', 'category_id', 'card_id', 'date', 'description', 
                       'amount', 'type', 'bank', 'statement_type', 'filename', 
                       'duplicate_potential_state'}
    
    # Column names
    id_col: str = 'transaction_id'
    user_id: str = 'user_id'
    category_id: str = 'category_id'
    card_id: str = 'card_id'
    date: str = 'date'
    description: str = 'description'
    amount: str = 'amount'
    type: str = 'type'
    bank: str = 'bank'
    statement_type: str = 'statement_type'
    filename: str = 'filename'
    duplicate_potential_state: str = 'duplicate_potential_state'
    
    def _ensure_partition_exists(self, date_value: str) -> None:
        """
        Ensure that a partition exists for the given date in the transactions table.
        Creates the partition if it doesn't exist.
        
        Args:
            date_value (str): Date in 'YYYY-MM-DD' format
        """
        cursor = self._get_cursor()
        
        try:
            # Parse the date to get year and month
            date_obj = datetime.strptime(date_value, '%Y-%m-%d')
            year = date_obj.year
            month = date_obj.month
            
            # Create partition name
            partition_name = f"transactions_{year}_{month:02d}"
            
            # Check if partition exists
            check_query = """
                SELECT EXISTS (
                    SELECT 1 FROM pg_class 
                    WHERE relname = %s AND relispartition = true
                )
            """
            cursor.execute(check_query, (partition_name,))
            result = cursor.fetchone()
            partition_exists = result[0] if result else False
            
            if not partition_exists:
                # Create the partition
                start_date = f"{year}-{month:02d}-01"
                if month == 12:
                    end_date = f"{year + 1}-01-01"
                else:
                    end_date = f"{year}-{month + 1:02d}-01"
                
                create_partition_query = f"""
                    CREATE TABLE {partition_name} PARTITION OF transactions
                    FOR VALUES FROM ('{start_date}') TO ('{end_date}')
                """
                
                cursor.execute(create_partition_query)
                
        except Exception as e:
            raise e

    def _ensure_partitions_for_transactions(self, transactions: list[Transaction]) -> None:
        """
        Ensure that partitions exist for all dates in the records.
        Only applies to transactions table.
        
        Args:
            records (list[Transaction]): List of transactions to insert
        """
        # Get unique dates from records
        unique_dates = set()
        
        for transaction in transactions:
                date_str = transaction.date.strftime('%Y-%m-%d')
                unique_dates.add(date_str)
        
        # Ensure partitions exist for each unique date
        for date_str in unique_dates:
            self._ensure_partition_exists(date_str)
    
    def get_transactions(
            self, 
            user_id: int, 
            columns: list[str] | None = None,
            period: Period | None = None,
            banks: list[BankName] | None = None,
            statement_type: StatementType | None = None,
            amount_types: list[TransactionType] | None = None,
            show_categories_names: bool | None = False,
            show_cards_names: bool | None = False,
            order_col: str | None = 'date',
            order: Literal['asc', 'desc'] = 'desc',
            limit: int | None = None,
            transaction_model: bool | None = True,
            **conditions: Any
        ) -> list[Transaction] | list[dict[str, Any]]:
        
        if columns:
            columns = self._validate_columns(columns)
            columns = [f't.{col}' for col in columns]
            if show_categories_names:
                columns.append('name AS category')
            if show_cards_names:
                columns.append('card_name AS card_name')
            
            query = f"""
                SELECT {', '.join(columns)} FROM {self.table_name} AS t
            """
        else:
            query = f"""
                SELECT * FROM {self.table_name} AS t
        """
            
        if show_categories_names:
            query += f" LEFT JOIN categories ON t.{self.category_id} = categories.{self.category_id}"
        
        if show_cards_names:
            query += f" LEFT JOIN cards ON t.{self.card_id} = cards.{self.card_id}"
        
        query += f" WHERE t.{self.user_id} = %(user_id)s"
        
        params: dict[str, Any] = {'user_id': user_id}
        
        if period:
            start_date, end_date = period.to_tuple()
            query += f" AND date BETWEEN %(start_date)s AND %(end_date)s"
            params.update({
                'start_date': start_date.strftime('%Y-%m-%d') if hasattr(start_date, 'strftime') else start_date,
                'end_date': end_date.strftime('%Y-%m-%d') if hasattr(end_date, 'strftime') else end_date
            })
            
        if banks:
            query += f" AND bank IN ({', '.join([f'%(bank_{i})s' for i, _ in enumerate(banks)])})"
            
            for i, bank in enumerate(banks):
                params[f'bank_{i}'] = bank
                
        if statement_type:
            query += f" AND statement_type = %(statement_type)s"
            params['statement_type'] = statement_type.value
            
        if amount_types:
            query += f" AND type IN ({', '.join([f'%(type_{i})s' for i, _ in enumerate(amount_types)])})"
            for i, amount_type in enumerate(amount_types):
                params[f'type_{i}'] = amount_type.value
                
        if conditions:
            validated_conditions = self._validate_conditions(conditions)
            query += " AND "
            
            for col, value in validated_conditions.items():
                query += f"{col} IN %({col})s" if isinstance(value, tuple) else f"{col} = %({col})s"
                params[col] = value
                
            params.update(validated_conditions)
            
        if order_col and order:
            order_col_validated = self._validate_columns([order_col])[0]
            query += f" ORDER BY {order_col_validated} {order}"
        elif (order_col and not order) or (not order_col and order):
            raise ValueError("Order column and order must be provided together")
            
        if limit:
            query += f" LIMIT %(limit)s"
            params['limit'] = limit
            
        result = self.execute_query(query, params= params, fetch= 'all', dict_cursor= True)
        
        if result and isinstance(result, list):
            if transaction_model:
                transactions = [Transaction(**r) for r in result if isinstance(r, dict)]
                
                return cast(list[Transaction], transactions)
            else:
                transactions = [r for r in result if isinstance(r, dict)]
                
                return cast(list[dict[str, Any]], transactions)
        return []
    
    def get_transactions_period(self, user_id: int) -> Period:
        query = f"""
            SELECT MIN({self.date}) as start_date, MAX({self.date}) as end_date
            FROM {self.table_name}
            WHERE {self.user_id} = %(user_id)s
        """
        
        result = self.execute_query(query, params= {'user_id': user_id}, fetch= 'one', dict_cursor= True)
        
        if result and isinstance(result, dict) and result['start_date'] and result['end_date']:
            return Period(start_date= result['start_date'], end_date= result['end_date'])
        # Return a default period or raise error? Assuming DB has data or caller handles logic.
        # But Period requires dates. Let's assume today if empty, or raise.
        # Original code didn't handle None. I will assume data exists.
        # If no data, start_date/end_date are None. Period constructor might fail if types mismatch.
        # Period model fields are date. 
        # I'll return today for both if empty to be safe, or raise.
        if not result or not result['start_date']:
             return Period(start_date=date.today(), end_date=date.today())
        return Period(start_date= result['start_date'], end_date= result['end_date'])
    
    def add_records(self, transactions: list[Transaction]) -> None:
        if not transactions:
            return
        
        self._ensure_partitions_for_transactions(transactions)
        
        records = [t.dump_to_add() for t in transactions]
        
        with self.transaction():
            record_columns = list(records[0].keys())
            
            query = f"""
                INSERT INTO {self.table_name} ({', '.join(record_columns)})
                VALUES ({', '.join(f'%({col})s' for col in record_columns)})
            """
            
            self.execute_query(query, params= cast(list[dict[str, Any]], records), batch= True)
            
    def update_transactions(self, modified_transactions: list[Transaction]) -> None:
        if not modified_transactions:
            return
        
        params = [t.model_dump() for t in modified_transactions]
            
        with self.transaction():
            query = f"""
                UPDATE {self.table_name}
                SET 
                    {self.date} = %({self.date})s, 
                    {self.description} = %({self.description})s, 
                    {self.amount} = %({self.amount})s, 
                    {self.type} = %({self.type})s, 
                    {self.bank} = %({self.bank})s, 
                    {self.statement_type} = %({self.statement_type})s, 
                    {self.filename} = %({self.filename})s,
                    {self.category_id} = %({self.category_id})s
                    {self.duplicate_potential_state} = %({self.duplicate_potential_state})s
                WHERE {self.id_col} = %({self.id_col})s
            """
            
            self.execute_query(query, params= cast(list[dict[str, Any]], params), batch=True)
        
    def delete_transactions(self, transactions_to_delete: list[Transaction]) -> None:
        if not transactions_to_delete:
            return
        
        params = {f'id_{i}': t.transaction_id for i, t in enumerate(transactions_to_delete)}
        
        # Create the correct parameter placeholders
        param_keys = list(params.keys())
        placeholders = ', '.join([f'%({key})s' for key in param_keys])
        
        with self.transaction():
            query = f"""
                DELETE FROM {self.table_name}
                WHERE {self.id_col} IN ({placeholders})
            """
            
            self.execute_query(query, params=params)
        
    async def get_avg_all_time_sums(self, user_id: int) -> FinancialAmountsSums:
        query = f"""
            WITH base AS (
                SELECT
                    COALESCE(SUM(CASE WHEN {self.type} = %(income_type)s THEN {self.amount} ELSE 0 END), 0) AS total_income,
                    COALESCE(SUM(CASE WHEN {self.type} = %(expense_type)s THEN {self.amount} ELSE 0 END), 0) AS total_expenses,
                    COUNT(DISTINCT DATE_TRUNC('month', {self.date})) AS months_active
                FROM {self.table_name}
                WHERE {self.user_id} = %(user_id)s
            ),
            initial AS (
                SELECT {self.amount} AS initial_balance
                FROM {self.table_name}
                WHERE {self.user_id} = %(user_id)s
                  AND {self.type} = %(initial_type)s
                ORDER BY {self.date} ASC
                LIMIT 1
            )
            SELECT
                (b.total_income + COALESCE(i.initial_balance, 0)) / NULLIF(b.months_active, 0) AS avg_monthly_income,
                b.total_expenses / NULLIF(b.months_active, 0) AS avg_monthly_expenses,
                ((b.total_income + COALESCE(i.initial_balance, 0)) - b.total_expenses) / NULLIF(b.months_active, 0) AS avg_monthly_savings
            FROM base b
            LEFT JOIN initial i ON TRUE
        """
        params = {
            'income_type': TransactionType.INCOME.value,
            'expense_type': TransactionType.EXPENSE.value,
            'initial_type': TransactionType.INITIAL_BALANCE.value,
            'user_id': user_id,
        }
        result = self.execute_query(query, params=params, fetch='one', dict_cursor=True)

        if result and isinstance(result, dict):
            return FinancialAmountsSums(
                income=result.get('avg_monthly_income', Decimal('0.00')),
                withdrawal=result.get('avg_monthly_expenses', Decimal('0.00')),
                savings=result.get('avg_monthly_savings', Decimal('0.00'))
            )
        return FinancialAmountsSums(income=Decimal('0.00'), withdrawal=Decimal('0.00'), savings=Decimal('0.00'))
        
    async def get_specific_period_sums(self, user_id: int, specific_period: Period) -> FinancialAmountsSums:
        start_date, end_date = specific_period.to_tuple()
        
        query = f"""
            SELECT 
                COALESCE(SUM(CASE WHEN {self.type} = %(income_type)s THEN {self.amount} ELSE 0 END), 0) AS specific_period_income,
                COALESCE(SUM(CASE WHEN {self.type} = %(expense_type)s THEN {self.amount} ELSE 0 END), 0) AS specific_period_withdrawal
            FROM {self.table_name}
            WHERE {self.user_id} = %(user_id)s
            AND {self.date} BETWEEN %(start_date)s AND %(end_date)s
        """
        
        params = {
            'income_type': TransactionType.INCOME.value,
            'expense_type': TransactionType.EXPENSE.value,
            'user_id': user_id,
            'start_date': start_date,
            'end_date': end_date,
        }
        
        result = self.execute_query(query, params= params, fetch= 'one', dict_cursor= True)
        
        if result and isinstance(result, dict):
            return FinancialAmountsSums(
                income= result.get('specific_period_income', 0),
                withdrawal= result.get('specific_period_withdrawal', 0),
                savings= None
            )
        return FinancialAmountsSums(income=Decimal('0.00'), withdrawal=Decimal('0.00'), savings=None)
        
    def get_first_initial_balance(self, user_id: int) -> dict[str, Any] | None:
        query = f"""
            SELECT {self.date}, {self.amount}, {self.type}
            FROM {self.table_name}
            WHERE {self.user_id} = %(user_id)s
            AND {self.type} = %(initial_type)s
            ORDER BY {self.date} ASC
            LIMIT 1
        """
        
        params = {
            'user_id': user_id,
            'initial_type': TransactionType.INITIAL_BALANCE.value,
        }
        
        result = self.execute_query(query, params= params, fetch= 'one', dict_cursor= True)
        
        if result and isinstance(result, dict):
            return result
        else:
            return None
    
    async def get_max_amounts(self, user_id: int) -> dict[str, AnalysisAmountsPerPeriod]:
        query = f"""
            SELECT
                -- All time max/min amounts
                MAX(CASE 
                    WHEN {self.type} = %(income_type)s 
                    THEN {self.amount} ELSE 0 END) AS max_income_all_time,
                MIN(CASE 
                    WHEN {self.type} = %(expense_type)s 
                    THEN {self.amount} ELSE 0 END) AS max_expense_all_time,
                -- Current month max/min amounts
                MAX(CASE 
                    WHEN {self.type} = %(income_type)s 
                    AND {self.date} BETWEEN %(current_month_start_date)s AND %(current_month_end_date)s
                    THEN {self.amount} ELSE 0 END) AS max_income_current_month,
                MIN(CASE 
                    WHEN {self.type} = %(expense_type)s 
                    AND {self.date} BETWEEN %(current_month_start_date)s AND %(current_month_end_date)s
                    THEN {self.amount} ELSE 0 END) AS max_expense_current_month,
                -- Last month max/min amounts
                MAX(CASE 
                    WHEN {self.type} = %(income_type)s 
                    AND {self.date} BETWEEN %(last_month_start_date)s AND %(last_month_end_date)s
                    THEN {self.amount} ELSE 0 END) AS max_income_last_month,
                MIN(CASE 
                    WHEN {self.type} = %(expense_type)s 
                    AND {self.date} BETWEEN %(last_month_start_date)s AND %(last_month_end_date)s
                    THEN {self.amount} ELSE 0 END) AS max_expense_last_month
            FROM {self.table_name}
            WHERE {self.user_id} = %(user_id)s
        """
        
        today = date.today()
        last_month = Period(start_date= today.replace(day= 1) - relativedelta(months= 1), end_date= today.replace(day= 1) - relativedelta(days= 1))
        
        params = {
            'income_type': TransactionType.INCOME.value,
            'expense_type': TransactionType.EXPENSE.value,
            'user_id': user_id,
            'current_month_start_date': today.replace(day= 1),
            'current_month_end_date': today,
            'last_month_start_date': last_month.start_date,
            'last_month_end_date': last_month.end_date,
        }
        
        result = self.execute_query(query, params= params, fetch= 'one', dict_cursor= True)
        
        if result and isinstance(result, dict):
            return {
                'Abono' : AnalysisAmountsPerPeriod(
                    all_time= result['max_income_all_time'] or 0,
                    current_month= result['max_income_current_month'] or 0,
                    last_month= result['max_income_last_month'] or 0,
                    avarage= Decimal('0.00')
                ),
                'Cargo' : AnalysisAmountsPerPeriod(
                    all_time= result['max_expense_all_time'] or 0,
                    current_month= result['max_expense_current_month'] or 0,
                    last_month= result['max_expense_last_month'] or 0,
                    avarage= Decimal('0.00')
                )
            }
        return {} # Or raise
        
    async def get_max_amount_in_specific_period(self, user_id: int, specific_period: Period) -> dict[str, Decimal]:
        query = f"""
            SELECT
                MAX(CASE 
                    WHEN {self.type} = %(income_type)s 
                    AND {self.date} BETWEEN %(specific_period_start_date)s AND %(specific_period_end_date)s
                    THEN {self.amount} ELSE 0 END) AS max_income_specific_period,
                MIN(CASE 
                    WHEN {self.type} = %(expense_type)s 
                    AND {self.date} BETWEEN %(specific_period_start_date)s AND %(specific_period_end_date)s
                    THEN {self.amount} ELSE 0 END) AS max_expense_specific_period
            FROM {self.table_name}
            WHERE {self.user_id} = %(user_id)s
        """ 
        
        params = {
            'income_type': TransactionType.INCOME.value,
            'expense_type': TransactionType.EXPENSE.value,
            'user_id': user_id,
            'specific_period_start_date': specific_period.start_date,
            'specific_period_end_date': specific_period.end_date,
        }
        
        result = self.execute_query(query, params= params, fetch= 'one', dict_cursor= True)
        
        if result and isinstance(result, dict):
            return {
                'Abono' : result['max_income_specific_period'] or Decimal('0.00'),
                'Cargo' : result['max_expense_specific_period'] or Decimal('0.00'),
            }
        return {'Abono': Decimal('0.00'), 'Cargo': Decimal('0.00')}
    
    async def get_frecuencys(self, user_id: int) -> dict[str, AnalysisAmountsPerPeriod]:
        query = f"""
            SELECT
                -- All-time frequency
                COUNT(CASE WHEN {self.type} = %(income_type)s THEN 1 END) AS freq_income_all_time,
                COUNT(CASE WHEN {self.type} = %(expense_type)s THEN 1 END) AS freq_expense_all_time,
                -- Current month frequency
                COUNT(CASE 
                    WHEN {self.type} = %(income_type)s 
                    AND {self.date} BETWEEN %(current_month_start_date)s AND %(current_month_end_date)s
                THEN 1 END) AS freq_income_current_month,
                COUNT(CASE 
                    WHEN {self.type} = %(expense_type)s 
                    AND {self.date} BETWEEN %(current_month_start_date)s AND %(current_month_end_date)s
                THEN 1 END) AS freq_expense_current_month,
                -- Last month frequency
                COUNT(CASE 
                    WHEN {self.type} = %(income_type)s 
                    AND {self.date} BETWEEN %(last_month_start_date)s AND %(last_month_end_date)s
                THEN 1 END) AS freq_income_last_month,
                COUNT(CASE 
                    WHEN {self.type} = %(expense_type)s 
                    AND {self.date} BETWEEN %(last_month_start_date)s AND %(last_month_end_date)s
                THEN 1 END) AS freq_expense_last_month
            FROM {self.table_name}
            WHERE {self.user_id} = %(user_id)s
        """

        today = date.today()
        last_month = Period(
            start_date=today.replace(day=1) - relativedelta(months=1),
            end_date=today.replace(day=1) - relativedelta(days=1)
        )
        params = {
            'income_type': TransactionType.INCOME.value,
            'expense_type': TransactionType.EXPENSE.value,
            'user_id': user_id,
            'current_month_start_date': today.replace(day=1),
            'current_month_end_date': today,
            'last_month_start_date': last_month.start_date,
            'last_month_end_date': last_month.end_date,
        }

        result = self.execute_query(query, params=params, fetch='one', dict_cursor=True)

        if result and isinstance(result, dict):
            return {
                'Abono': AnalysisAmountsPerPeriod(
                    all_time=result['freq_income_all_time'],
                    current_month=result['freq_income_current_month'],
                    last_month=result['freq_income_last_month'],
                    avarage=Decimal('0.00')
                ),
                'Cargo': AnalysisAmountsPerPeriod(
                    all_time=result['freq_expense_all_time'],
                    current_month=result['freq_expense_current_month'],
                    last_month=result['freq_expense_last_month'],
                    avarage=Decimal('0.00')
                )
            }
        return {} # Or raise
        
    async def get_frecuency_in_specific_period(self, user_id: int, specific_period: Period) -> dict[str, int]:
        query = f"""
            SELECT
                COUNT(CASE 
                    WHEN {self.type} = %(income_type)s 
                    AND {self.date} BETWEEN %(specific_period_start_date)s AND %(specific_period_end_date)s
                THEN 1 END) AS freq_income_specific_period,
                COUNT(CASE 
                    WHEN {self.type} = %(expense_type)s 
                    AND {self.date} BETWEEN %(specific_period_start_date)s AND %(specific_period_end_date)s
                THEN 1 END) AS freq_expense_specific_period
            FROM {self.table_name}
            WHERE {self.user_id} = %(user_id)s
        """

        params = {
            'income_type': TransactionType.INCOME.value,
            'expense_type': TransactionType.EXPENSE.value,
            'user_id': user_id,
            'specific_period_start_date': specific_period.start_date,
            'specific_period_end_date': specific_period.end_date,
        }

        result = self.execute_query(query, params=params, fetch='one', dict_cursor=True)

        if result and isinstance(result, dict):
            return {
                'Abono': result['freq_income_specific_period'],
                'Cargo': result['freq_expense_specific_period'],
            }
        return {'Abono': 0, 'Cargo': 0}
