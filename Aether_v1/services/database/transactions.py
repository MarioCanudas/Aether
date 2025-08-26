import datetime
from typing import Optional, Literal, List, Dict, Set, Tuple, Any
from models.bank_properties import BankName
from models.dates import Period
from models.records import TransactionRecord
from .base_db import BaseDBService

class TransactionsDBService(BaseDBService):
    # Table information
    table_name = 'transactions'
    allowed_columns = {'transaction_id', 'user_id', 'category_id', 'date', 'description', 'amount', 'type', 'bank', 'statement_type', 'filename'}
    
    # Column names
    id_col = 'transaction_id'
    user_id = 'user_id'
    category_id = 'category_id'
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
            period: Optional[Tuple[datetime.date, datetime.date]] = None,
            banks: Optional[List[str]] = None,
            statement_type: Optional[Literal['debit', 'credit']] = None,
            amount_type: Optional[List[Literal['Abono', 'Cargo', 'Saldo inicial']]] = None,
            show_categories_names: Optional[bool] = False,
            **conditions: Any
        ) -> List[TransactionRecord]:
        
        if columns:
            columns = self._validate_columns(columns)
            columns = [f't.{col}' for col in columns]
            columns.append('name AS category') if show_categories_names else None
            
            query = f"""
                SELECT {', '.join(columns)} FROM {self.table_name} AS t
            """
        else:
            query = f"""
                SELECT * FROM {self.table_name} AS t
        """
            
        if show_categories_names:
            query += f" LEFT JOIN categories ON t.{self.category_id} = categories.{self.category_id}"
        
        query += f" WHERE t.{self.user_id} = %(user_id)s"
        
        params = {'user_id': user_id}
        
        if period:
            start_date, end_date = period
            query += f" AND date BETWEEN %(start_date)s AND %(end_date)s"
            params.update({
                'start_date': start_date.strftime('%Y-%m-%d') if hasattr(start_date, 'strftime') else start_date,
                'end_date': end_date.strftime('%Y-%m-%d') if hasattr(end_date, 'strftime') else end_date
            })
            
        if banks:
            query += f" AND bank IN ({', '.join([f'%(bank_{i})s' for i in range(len(banks))])})"
            allowed_banks = [bank.value for bank in BankName]
            for i, bank in enumerate(banks):
                if bank not in allowed_banks:
                    raise ValueError(f"Invalid bank: {bank}")
                
                params[f'bank_{i}'] = bank
                
        if statement_type:
            query += f" AND statement_type = %(statement_type)s"
            
        if amount_type:
            query += f" AND type IN ({', '.join([f'%(type_{i})s' for i in range(len(amount_type))])})"
            for i, amount_type in enumerate(amount_type):
                params[f'type_{i}'] = amount_type
                
        if conditions:
            validated_conditions = self._validate_conditions(conditions)
            query += " AND "
            query += " AND ".join([f"{col} = %({col})s" for col in validated_conditions.keys()])
            params.update(validated_conditions)
            
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
            from datetime import datetime
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