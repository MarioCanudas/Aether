from typing import Optional, List, Dict, Set, Tuple, Any, Literal
from decimal import Decimal
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from models.amounts import TransactionType
from models.bank_properties import BankName, StatementType
from models.dates import Period
from models.financial import FinancialAmountsSums
from models.records import TransactionRecord
from models.views_data import AnalysisAmountsPerPeriod
from .base_db import BaseDBService

class TransactionsDBService(BaseDBService):
    # Table information
    table_name = 'transactions'
    allowed_columns = {'transaction_id', 'user_id', 'category_id', 'card_id', 'date', 'description', 'amount', 'type', 'bank', 'statement_type', 'filename'}
    
    # Column names
    id_col = 'transaction_id'
    user_id = 'user_id'
    category_id = 'category_id'
    card_id = 'card_id'
    date = 'date'
    description = 'description'
    amount = 'amount'
    type = 'type'
    bank = 'bank'
    statement_type = 'statement_type'
    filename = 'filename'
    
    def get_transactions(
            self, 
            user_id: int, 
            columns: Optional[List[str]] = None,
            period: Optional[Period] = None,
            banks: Optional[List[BankName]] = None,
            statement_type: Optional[StatementType] = None,
            amount_types: Optional[List[TransactionType]] = None,
            show_categories_names: Optional[bool] = False,
            show_cards_names: Optional[bool] = False,
            order_col: Optional[str] = 'date',
            order: Literal['asc', 'desc'] = 'desc',
            limit: Optional[int] = None,
            **conditions: Any
        ) -> List[TransactionRecord]:
        
        if columns:
            columns = self._validate_columns(columns)
            columns = [f't.{col}' for col in columns]
            columns.append('name AS category') if show_categories_names else None
            columns.append('card_name AS card_name') if show_cards_names else None
            
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
        
        params = {'user_id': user_id}
        
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
            order_col = self._validate_columns([order_col])[0]
            query += f" ORDER BY {order_col} {order}"
        elif (order_col and not order) or (not order_col and order):
            raise ValueError("Order column and order must be provided together")
            
        if limit:
            query += f" LIMIT %(limit)s"
            params['limit'] = limit
            
        return self.execute_query(query, params= params, fetch= 'all', dict_cursor= True)
        
    
    def add_records(self, records: List[Dict[str, Any]]) -> None:
        if not records:
            return
        
        self._ensure_partitions_for_records(records)
        
        for record in records:
            record[self.date] = record[self.date].strftime('%Y-%m-%d') if hasattr(record[self.date], 'strftime') else record[self.date]
        
        with self.transaction():
            record_columns = list(records[0].keys())
            
            query = f"""
                INSERT INTO {self.table_name} ({', '.join(record_columns)})
                VALUES ({', '.join(f'%({col})s' for col in record_columns)})
            """
            
            self.execute_query(query, params= records, batch= True)
        
    def get_transactions_period(self, user_id: int) -> Period:
        query = f"""
            SELECT MIN({self.date}) as start_date, MAX({self.date}) as end_date
            FROM {self.table_name}
            WHERE {self.user_id} = %(user_id)s
        """
        
        result = self.execute_query(query, params= {'user_id': user_id}, fetch= 'one', dict_cursor= True)
        
        return Period(start_date= result['start_date'], end_date= result['end_date'])
    
    def get_existing_keys(self, all_params: Dict[str, Any], query_values: List[str]) -> Set[Tuple[Any, ...]]:
        query = f"""
            SELECT {self.date}, {self.description}, {self.amount}, {self.bank}::text, {self.statement_type}::text
            FROM {self.table_name}
            WHERE {self.user_id} = %(user_id)s
            AND ({self.date}, {self.description}, {self.amount}, {self.bank}::text, {self.statement_type}::text) IN (
                VALUES {', '.join(query_values)}
            )
        """
        
        result = self.execute_query(query, params= all_params, fetch= 'all')
        
        return set(result)
    
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
            partition_exists = cursor.fetchone()[0]
            
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

    def _ensure_partitions_for_records(self, records: List[dict]) -> None:
        """
        Ensure that partitions exist for all dates in the records.
        Only applies to transactions table.
        
        Args:
            records (List[dict]): List of records to insert
        """
        # Get unique dates from records
        unique_dates = set()
        for record in records:
            if 'date' in record:
                date_str = record['date']
                if hasattr(date_str, 'strftime'):
                    date_str = date_str.strftime('%Y-%m-%d')
                unique_dates.add(date_str)
        
        # Ensure partitions exist for each unique date
        for date_str in unique_dates:
            self._ensure_partition_exists(date_str)
            
    def update_transactions(self, modified_transactions: List[TransactionRecord]) -> None:
        if not modified_transactions:
            return
            
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
                WHERE {self.id_col} = %({self.id_col})s
            """
            
            self.execute_query(query, params=modified_transactions, batch=True)
        
    def delete_records(self, deleted_transactions: List[TransactionRecord]) -> None:
        if not deleted_transactions:
            return
        
        ids = [int(transaction['transaction_id']) for transaction in deleted_transactions]
        
        params = {f'id_{i}': id for i, id in enumerate(ids)}
        
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

        return FinancialAmountsSums(
            income=result['avg_monthly_income'],
            withdrawal=result['avg_monthly_expenses'],
            savings=result['avg_monthly_savings']
        )
        
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
        
        return FinancialAmountsSums(
            income= result['specific_period_income'],
            withdrawal= result['specific_period_withdrawal'],
            savings= None
        )
        
    def get_first_initial_balance(self, user_id: int) -> Dict[str, Any]:
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
        
        return self.execute_query(query, params= params, fetch= 'one', dict_cursor= True)
    
    async def get_max_amounts(self, user_id: int) -> Dict[str, AnalysisAmountsPerPeriod]:
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
        
        return {
            'Abono' : AnalysisAmountsPerPeriod(
                all_time= result['max_income_all_time'],
                current_month= result['max_income_current_month'],
                last_month= result['max_income_last_month'],
                avarage= 0
            ),
            'Cargo' : AnalysisAmountsPerPeriod(
                all_time= result['max_expense_all_time'],
                current_month= result['max_expense_current_month'],
                last_month= result['max_expense_last_month'],
                avarage= 0
            )
        }
        
    async def get_max_amount_in_specific_period(self, user_id: int, specific_period: Period) -> Dict[str, Decimal]:
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
        
        return {
            'Abono' : result['max_income_specific_period'],
            'Cargo' : result['max_expense_specific_period'],
        }
    
    async def get_frecuencys(self, user_id: int) -> Dict[str, AnalysisAmountsPerPeriod]:
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

        return {
            'Abono': AnalysisAmountsPerPeriod(
                all_time=result['freq_income_all_time'],
                current_month=result['freq_income_current_month'],
                last_month=result['freq_income_last_month'],
                avarage=0
            ),
            'Cargo': AnalysisAmountsPerPeriod(
                all_time=result['freq_expense_all_time'],
                current_month=result['freq_expense_current_month'],
                last_month=result['freq_expense_last_month'],
                avarage=0
            )
        }
        
    async def get_frecuency_in_specific_period(self, user_id: int, specific_period: Period) -> Dict[str, int]:
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

        return {
            'Abono': result['freq_income_specific_period'],
            'Cargo': result['freq_expense_specific_period'],
        }