import psycopg2
import psycopg2.extras
import pandas as pd
from typing import Optional, Dict, Any, List, Literal, Tuple, Generator
from pathlib import Path
import logging
import re
from contextlib import contextmanager
from dotenv import load_dotenv
import os

load_dotenv()

DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT')
DB_NAME = os.getenv('DB_NAME')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')

logger = logging.getLogger(__name__)

class DatabaseService:
    """
    This class is used to connect to the database and execute queries.
    It uses the sqlite3 library to connect to the database.
    
    Attributes:
        db_file: The path to the database file.
        conn: The connection to the database.
        cursor: The cursor to the database.
        _transaction_level: Current transaction nesting level.
        _savepoints: Stack of savepoint names for nested transactions.
        
    Methods:
        connect: Connect to the database.
        disconnect: Disconnect from the database.
        begin_transaction: Start a new transaction or savepoint.
        commit_transaction: Commit current transaction or release savepoint.
        rollback_transaction: Rollback current transaction or revert to savepoint.
        transaction: Context manager for automatic transaction handling.
        batch_operations: Execute multiple operations in a single transaction.
    """
    ALLOWED_TABLES = {'users', 'categories', 'transactions', 'monthly_results', 'goals'}
    ALLOWED_COLUMNS = {
        'users': {'id', 'username', 'password_hash', 'created_at', 'last_login', 'updated_at'},
        'categories': {'id', 'user_id', 'name', 'group', 'description'},
        'transactions': {'id', 'user_id', 'category_id', 'date', 'description', 'amount', 'type', 'bank', 'statement_type', 'filename'},
        'monthly_results': {'id', 'user_id', 'year_month', 'initial_balance', 'total_income', 'total_withdrawal', 'savings', 'last_calculated_at'},
        'goals': {'id', 'user_id', 'type', 'category_id', 'amount', 'added_amount', 'name', 'created_at', 'start_date', 'end_date', 'achived'},
    }
    
    def __init__(self):
        self.conn: Optional[psycopg2.extensions.connection] = None
        self.cursor: Optional[psycopg2.extensions.cursor] = None
        self._transaction_level = 0  # Track nested transaction levels
        self._savepoints = []  # Stack of savepoint names for nested transactions
        
    def connect(self) -> None:
        """
        Connect to the database.
        """
        try:
            self.conn = psycopg2.connect(
                host=DB_HOST,
                port=DB_PORT,
                dbname=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD,
                connect_timeout=10
            )
            self.cursor = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            logger.info(f"Connected to PostgreSQL database: {DB_HOST}/{DB_NAME}")
        except Exception as e:
            logger.error(f"Error connecting to PostgreSQL: {e}")
            raise
        
    def disconnect(self) -> None:
        """
        Disconnect from the database.
        Automatically rolls back any pending transactions before disconnecting.
        """
        # Rollback any pending transactions before disconnecting
        if self._transaction_level > 0:
            logger.warning(f"Disconnecting with {self._transaction_level} active transactions - rolling back all")
            while self._transaction_level > 0:
                self.rollback_transaction()
        
        if self.cursor:
            self.cursor.close()
            self.cursor = None
            logger.debug("Cursor closed")
            
        if self.conn:
            self.conn.close()
            self.conn = None
            logger.info("Database connection closed")
    
    # ========== TRANSACTION MANAGEMENT METHODS ==========
    
    def begin_transaction(self) -> None:
        """
        Start a new transaction or create a savepoint if a transaction is already active.
        Supports nested transactions through SQLite savepoints.
        
        Raises:
            Exception: If not connected to the database.
        """
        if not self.conn:
            logger.error("Not connected to the database")
            raise Exception("Not connected to the database")
        
        self._transaction_level += 1
        
        if self._transaction_level == 1:
            # First transaction - BEGIN is implicit with autocommit=False
            self.cursor.execute("BEGIN;")
            logger.debug("Transaction started")
        else:
            # Nested transaction - create savepoint
            savepoint_name = f"sp_{self._transaction_level}"
            self.cursor.execute(f"SAVEPOINT {savepoint_name}")
            self._savepoints.append(savepoint_name)
            logger.debug(f"Savepoint created: {savepoint_name}")
    
    def commit_transaction(self) -> None:
        """
        Commit the current transaction or release the most recent savepoint.
        
        Raises:
            Exception: If not connected to the database.
        """
        if not self.conn:
            logger.error("Not connected to the database")
            raise Exception("Not connected to the database")
        
        if self._transaction_level == 0:
            logger.warning("No active transaction to commit")
            return
        
        if self._transaction_level == 1:
            # Last transaction - perform actual commit
            self.conn.commit()
            logger.debug("Transaction committed")
        else:
            # Release savepoint
            savepoint_name = self._savepoints.pop()
            self.cursor.execute(f"RELEASE SAVEPOINT {savepoint_name}")
            logger.debug(f"Savepoint released: {savepoint_name}")
        
        self._transaction_level -= 1
    
    def rollback_transaction(self) -> None:
        """
        Rollback the current transaction or revert to the most recent savepoint.
        
        Raises:
            Exception: If not connected to the database.
        """
        if not self.conn:
            logger.error("Not connected to the database")
            raise Exception("Not connected to the database")
        
        if self._transaction_level == 0:
            logger.warning("No active transaction to rollback")
            return
        
        if self._transaction_level == 1:
            # Last transaction - perform actual rollback
            self.conn.rollback()
            logger.debug("Transaction rolled back")
        else:
            # Revert to savepoint
            savepoint_name = self._savepoints.pop()
            self.cursor.execute(f"ROLLBACK TO SAVEPOINT {savepoint_name}")
            logger.debug(f"Rolled back to savepoint: {savepoint_name}")
        
        self._transaction_level -= 1
    
    @contextmanager
    def transaction(self) -> Generator[None, None, None]:
        """
        Context manager for automatic transaction handling.
        Automatically commits on success or rolls back on any exception.
        
        Example:
            with db_service.transaction():
                db_service.insert_record('users', {'username': 'test'})
                db_service.insert_record('transactions', {...})
                # If any operation fails, everything is automatically rolled back
        
        Yields:
            None
        """
        self.begin_transaction()
        try:
            yield
            self.commit_transaction()
            logger.info(f"Transaction completed successfully at level {self._transaction_level + 1}")
        except Exception as e:
            self.rollback_transaction()
            logger.error(f"Transaction failed at level {self._transaction_level + 1}, rolled back: {e}")
            raise
    
    def is_in_transaction(self) -> bool:
        """
        Check if there is an active transaction.
        
        Returns:
            bool: True if there is an active transaction, False otherwise.
        """
        return self._transaction_level > 0
    
    def get_transaction_level(self) -> int:
        """
        Get the current transaction nesting level.
        
        Returns:
            int: Transaction level (0 = no transaction, 1+ = nested transactions).
        """
        return self._transaction_level
    
    def batch_operations(self, operations: List[Dict[str, Any]]) -> None:
        """
        Execute multiple operations in a single transaction for improved performance.
        
        Args:
            operations (List[Dict[str, Any]]): List of operations to execute.
                Each operation must have:
                - 'type': 'insert', 'insert_multiple', 'update', 'delete'
                - 'table_name': name of the table
                - Additional parameters specific to the operation type
        
        Example:
            operations = [
                {
                    'type': 'insert',
                    'table_name': 'users',
                    'record': {'username': 'john'}
                },
                {
                    'type': 'update',
                    'table_name': 'users',
                    'new_record': {'username': 'john_updated'},
                    'where_conditions': {'id': 1}
                }
            ]
            db_service.batch_operations(operations)
        
        Raises:
            ValueError: If operation type is not supported.
            Exception: If any operation fails (all operations are rolled back).
        """
        if not operations:
            logger.warning("Empty operations list provided to batch_operations")
            return
        
        with self.transaction():
            operation_count = 0
            for operation in operations:
                op_type = operation.get('type')
                table_name = operation.get('table_name')
                
                if op_type == 'insert':
                    self.insert_record(table_name, operation['record'])
                    operation_count += 1
                    
                elif op_type == 'insert_multiple':
                    self.insert_multiple_records(table_name, operation['records'])
                    operation_count += len(operation['records'])
                    
                elif op_type == 'update':
                    self.update_record(
                        table_name, 
                        operation['new_record'], 
                        operation['where_conditions']
                    )
                    operation_count += 1
                    
                elif op_type == 'delete':
                    self.delete_record(table_name, operation['where_conditions'])
                    operation_count += 1
                    
                else:
                    raise ValueError(f"Unsupported operation type: {op_type}")
            
            logger.info(f"Batch operation completed successfully: {len(operations)} operations, {operation_count} records affected")
    
    def _validate_table_name(self, table_name: str) -> str:
        """
        Validate the table name to avoid SQL injection and ensure it's in the allowed list.
        
        Args:
            table_name (str): The name of the table to validate.
            
        Returns:
            bool: True if the table name is valid, False otherwise.
        """
        if not table_name or not isinstance(table_name, str):
            raise ValueError(f'{table_name} is not a valid table name')
        
        # Remove any non-alphanumeric characters except underscore
        clean_name = re.sub(r'[^a-zA-Z0-9_]', '', table_name.strip())
        
        if clean_name != table_name.strip():
            raise ValueError(f"Invalid table name: {table_name}")
            
        if clean_name not in self.ALLOWED_TABLES:
            raise ValueError(f"Table '{clean_name}' is not in allowed tables list")
            
        return clean_name
    
    def _validate_columns(self, table_name: str, columns: list[str]) -> list[str]:
        """
        Validate the columns to avoid SQL injection and ensure they're in the allowed list.
        
        Args:
            table_name (str): The name of the table to validate.
            columns (list[str]): The columns to validate.
            
        Returns:
            list[str]: The validated columns.
        """
        if table_name not in self.ALLOWED_TABLES:
            raise ValueError(f"Table '{table_name}' is not in allowed tables list")
        
        if not columns or not isinstance(columns, list):
            raise ValueError(f"Columns must be a list of strings")
        
        allowed_columns = self.ALLOWED_COLUMNS[table_name]
        validated_columns = []
        
        for col in columns:
            if not col or not isinstance(col, str):
                raise ValueError(f"Invalid column name: {col}")
            
            clean_col = re.sub(r'[^a-zA-Z0-9_]', '', col.strip())
            
            if clean_col != col.strip():
                raise ValueError(f"Invalid column name: {col}")
            
            if clean_col not in allowed_columns:
                raise ValueError(f"Column '{clean_col}' is not in allowed columns list for table '{table_name}'")
            
            validated_columns.append(clean_col)
            
        return validated_columns
        
    def insert_record(self, table_name: str, record: dict) -> None:
        """
        Inserts a single record into the database.
        Respects manual transactions - only commits if no active transaction.
        
        Args:
            table_name (str): The name of the table to insert the record into.
            record (dict): The record to insert.
            
        Returns:
            None
        """
        if not self.conn:
            logger.error("Not connected to the database")
            raise Exception("Not connected to the database")
        
        if not isinstance(record, dict):
            logger.error(f"Record must be a dictionary, got {type(record)}")
            raise ValueError("Record must be a dictionary")
        
        if not record:
            logger.error("Record dictionary cannot be empty")
            raise ValueError("Record dictionary cannot be empty")
        
        table_name = self._validate_table_name(table_name)
        columns = self._validate_columns(table_name, list(record.keys()))
        
        query = f"""
            INSERT INTO {table_name} ({', '.join(columns)})
            VALUES ({', '.join([f'%({col})s' for col in columns])})
        """
        
        try:
            self.cursor.execute(query, record)
            
            # Only commit if not in a manual transaction
            if not self.is_in_transaction():
                self.conn.commit()
                logger.debug(f"Record inserted and committed to {table_name}")
            else:
                logger.debug(f"Record inserted to {table_name} (transaction pending)")
                
        except Exception as e:
            # Only rollback if not in a manual transaction
            if not self.is_in_transaction():
                self.conn.rollback()
                logger.error(f"Error inserting record, rolled back: {e}")
            else:
                logger.error(f"Error inserting record in transaction: {e}")
            raise

    def _ensure_partition_exists(self, date_value: str) -> None:
        """
        Ensure that a partition exists for the given date in the transactions table.
        Creates the partition if it doesn't exist.
        
        Args:
            date_value (str): Date in 'YYYY-MM-DD' format
        """
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
            self.cursor.execute(check_query, (partition_name,))
            partition_exists = self.cursor.fetchone()[0]
            
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
                
                self.cursor.execute(create_partition_query)
                logger.info(f"Created partition {partition_name} for date range {start_date} to {end_date}")
                
        except Exception as e:
            logger.error(f"Error ensuring partition exists for date {date_value}: {e}")
            raise

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

    def insert_multiple_records(self, table_name: str, records: List[dict], unique_values: Dict[str, Any] = None) -> None:
        """
        Inserts multiple records into the database efficiently.
        Respects manual transactions - only commits if no active transaction.
        For transactions table, automatically creates monthly partitions if they don't exist.
        
        Args:
            table_name (str): The name of the table to insert the records into.
            records (List[dict]): The list of records to insert.
            
        Returns:
            None
        """
        if not self.conn:
            logger.error("Not connected to the database")
            raise Exception("Not connected to the database")
        
        if not isinstance(records, list):
            logger.error(f"Records must be a list, got {type(records)}")
            raise ValueError("Records must be a list")
        
        if not records:
            logger.error("Records list cannot be empty")
            raise ValueError("Records list cannot be empty")
        
        if not all(isinstance(record, dict) for record in records):
            logger.error("All items in the records list must be dictionaries")
            raise ValueError("All items in the records list must be dictionaries")
        
        table_name = self._validate_table_name(table_name)
        columns = self._validate_columns(table_name, list(records[0].keys()))
        
        # Ensure partitions exist for transactions table before inserting
        if table_name == 'transactions':
            self._ensure_partitions_for_records(records)
        
        # Verify that all records have the same columns and ensure date is in the correct format
        for i, record in enumerate(records):
            if 'date' in record:
                record['date'] = record['date'].strftime('%Y-%m-%d') if hasattr(record['date'], 'strftime') else record['date']
            if set(record.keys()) != set(columns):
                logger.error(f"Record {i} has different columns than the first record")
                raise ValueError(f"All records must have the same columns. Record {i} differs.")
        
        query = f"""
            INSERT INTO {table_name} ({', '.join(columns)})
            VALUES ({', '.join([f'%({col})s' for col in columns])})
        """
        
        try:
            psycopg2.extras.execute_batch(self.cursor, query, records)
            
            # Only commit if not in a manual transaction
            if not self.is_in_transaction():
                self.conn.commit()
                logger.info(f"{len(records)} records inserted and committed to {table_name}")
            else:
                logger.debug(f"{len(records)} records inserted to {table_name} (transaction pending)")
                
        except Exception as e:
            # Only rollback if not in a manual transaction
            if not self.is_in_transaction():
                self.conn.rollback()
                logger.error(f"Error inserting multiple records, rolled back: {e}")
            else:
                logger.error(f"Error inserting multiple records in transaction: {e}")
            raise
        
    def get_records(
            self, 
            table_name: str, 
            where_conditions: Optional[Dict[str, Any]] = None, 
            columns: Optional[List[str]] = None,
            order_by: Optional[str] = None,
            limit: Optional[int] = None,
            value_format: Literal['dict', 'tuple', 'dataframe'] = 'dataframe'
        ) -> List[Dict[str, Any]] | List[Tuple[Any]] | pd.DataFrame:
        """
        Retrieve records from a table based on specified conditions.

        Args:
            table_name (str): The name of the table from which to retrieve records.
            where_conditions (Dict[str, Any], optional): A dictionary specifying the column-value pairs to filter the records (used in the WHERE clause).
            columns (Optional[List[str]], optional): A list of column names to retrieve. If None, all columns are returned.
            order_by (Optional[str], optional): A string specifying the column(s) to order the results by. If None, no ordering is applied.
            limit (Optional[int], optional): The maximum number of records to return. If None, all matching records are returned.
            value_format (Literal['dict', 'tuple', 'dataframe'], optional): Determines the format of the returned data:
                - 'dataframe': Returns a pandas DataFrame containing the results.
                - 'dict': Returns a list of dictionaries, where each dictionary represents a row (column names as keys).
                - 'tuple': Returns a list of tuples, where each tuple represents a row (column order as in the table).
                If not specified, defaults to 'dataframe'.

        Returns:
            Union[List[Dict[str, Any]], List[Tuple[Any]], pd.DataFrame]:
                - If value_format is 'dataframe', returns a pandas DataFrame.
                - If value_format is 'dict', returns a list of dictionaries.
                - If value_format is 'tuple', returns a list of tuples.
                Note: When value_format is not 'dataframe', the function always returns a list, and the type of each element in the list depends on the value_format.

        Raises:
            Exception: If not connected to the database.
            ValueError: If where_conditions is not a dictionary or if value_format is invalid.
            Exception: If an error occurs during query execution.

        Notes:
            - The value_format argument controls the type of each element in the returned list (if not 'dataframe').
            - Use 'dataframe' for pandas DataFrame output, 'dict' for a list of dicts, or 'tuple' for a list of tuples.
            - All columns in where_conditions must be valid for the specified table.
            - The columns, order_by, and limit parameters allow for more flexible querying.
        """
        if not self.conn:
            logger.error("Not connected to the database")
            raise Exception("Not connected to the database")
        
        table_name = self._validate_table_name(table_name)        
        
        query = f"""
            SELECT * FROM {table_name}
        """
        
        if columns:
            columns_clause = ', '.join(columns)
            query = f"""
                SELECT {columns_clause} FROM {table_name}
            """
        
        params = {}
        if where_conditions is not None:
            if not isinstance(where_conditions, dict):
                logger.error(f"Where conditions must be a dictionary, got {type(where_conditions)}")
                raise ValueError("Where conditions must be a dictionary")
            if where_conditions:
                where_conditions_columns = self._validate_columns(table_name, list(where_conditions.keys()))
                where_clause = ' AND '.join([f'{col} = %({col})s' for col in where_conditions_columns])
                query += f' WHERE {where_clause}'
                params = where_conditions
        # If where_conditions is None or empty, no WHERE clause is added and params remains empty
        
        if limit:
            limit_clause = f'LIMIT {limit}'
            query += '\n' + limit_clause
            
        if order_by:
            order_by_clause = f'ORDER BY {order_by}'
            query += '\n' + order_by_clause
        
        try:
            if value_format == 'dict' or value_format == 'dataframe':
                cursor = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            elif value_format == 'tuple':
                cursor = self.conn.cursor()
            else:
                raise ValueError(f"Invalid value format: {value_format}")

            cursor.execute(query, params)
            results = cursor.fetchall()
            cursor.close()

            logger.info(f"Retrieved {len(results)} records from {table_name} in {value_format} format")

            if value_format == 'dataframe':
                return pd.DataFrame(results)
            else:
                return results

        except Exception as e:
            logger.error(f"Error getting record from {table_name}: {e}")
            logger.debug(f"Failed query: {query}")
            logger.debug(f"Parameters: {params}")
            raise
        
    def get_unique_values(self, table_name: str, column_name: str) -> List[Any]:
        """
        Get unique values from a column in a table.
        """
        if self.cursor is None:
            return []
        
        table = self._validate_table_name(table_name)
        column = self._validate_columns(table, [column_name])[0]
        
        query = f"""
            SELECT DISTINCT {column} FROM {table}
        """
        
        try:
            self.cursor.execute(query)
            results = self.cursor.fetchall()
            return [result[0] for result in results]
        
        except Exception as e:
            logger.error(f"Error getting unique values from {table_name} column {column_name}: {e}")
            logger.debug(f"Failed query: {query}")
            raise
        
    def update_record(self, table_name: str, new_record: Dict[str, Any], where_conditions: Dict[str, Any]) -> None:
        """
        Update one or more records in a table based on specified conditions.
        Respects manual transactions - only commits if no active transaction.

        This method updates the values of one or more columns in the specified table for all records
        that match the given WHERE conditions. Both the columns to update and the conditions are validated
        to prevent SQL injection and ensure they are allowed for the table.

        Args:
            table_name (str): The name of the table where the update will be performed.
            new_record (Dict[str, Any]): A dictionary mapping column names to their new values.
                These columns will be updated in the matching records.
            where_conditions (Dict[str, Any]): A dictionary mapping column names to values that
                must be matched for a record to be updated (i.e., the WHERE clause).

        Raises:
            ValueError: If `new_record` or `where_conditions` are not dictionaries, empty, or if their columns are invalid.
            Exception: If an error occurs during the update operation.

        Example:
            rows_updated = update_record(
                table_name="users",
                new_record={"username": "new_name"},
                where_conditions={"id": 5}
            )
            # This will update the username of the user with id=5.

        Notes:
            - All columns in `new_record` and `where_conditions` must be valid for the specified table.
            - If multiple records match the conditions, all will be updated.
            - The method uses parameterized queries to prevent SQL injection.
            - WHERE conditions cannot be empty to prevent accidental updates to all records.
        """
        if not self.conn:
            logger.error("Not connected to the database")
            raise Exception("Not connected to the database")
            
        if not isinstance(new_record, dict) or not isinstance(where_conditions, dict):
            logger.error(f"Parameters must be dictionaries, got {type(new_record)} and {type(where_conditions)}")
            raise ValueError("New record and where conditions must be dictionaries")
        
        if not new_record:
            logger.error("New record dictionary cannot be empty")
            raise ValueError("New record dictionary cannot be empty")
            
        if not where_conditions:
            logger.error("Where conditions cannot be empty - this would update ALL records")
            raise ValueError("Where conditions cannot be empty for safety")
        
        table_name = self._validate_table_name(table_name)
        new_record_columns = self._validate_columns(table_name, list(new_record.keys()))
        where_conditions_columns = self._validate_columns(table_name, list(where_conditions.keys()))
        
        overlapping_columns = set(new_record_columns) & set(where_conditions_columns)
        if overlapping_columns:
            logger.warning(f"Overlapping columns between SET and WHERE: {overlapping_columns}")
        
        set_clause = ', '.join([f'{col} = %(set_{col})s' for col in new_record_columns])
        where_clause = ' AND '.join([f'{col} = %(where_{col})s' for col in where_conditions_columns])
        
        query = f"""
            UPDATE {table_name}
            SET {set_clause}
            WHERE {where_clause}
        """
        
        params = {}
        for col, value in new_record.items():
            params[f'set_{col}'] = value
        for col, value in where_conditions.items():
            params[f'where_{col}'] = value
        
        try:
            # Manual implementation of execute_query for UPDATE
            query_preview = query[:100] + '...' if len(query) > 100 else query
            logger.debug(f"Executing query: {query_preview}")
            
            self.cursor.execute(query, params)
            logger.debug(f"Query executed with {len(params)} parameters")
            
            rows_affected = self.cursor.rowcount
            
            # Only commit if not in a manual transaction
            if not self.is_in_transaction():
                self.conn.commit()
                logger.info(f"Update query executed and committed - {rows_affected} rows affected")
            else:
                logger.debug(f"Update query executed - {rows_affected} rows affected (transaction pending)")
            
            if rows_affected == 0:
                logger.warning(f"No records were updated in table {table_name} with conditions {where_conditions}")
            else:
                logger.debug(f"{rows_affected} records updated in table {table_name}")
            
        except Exception as e:
            # Only rollback if not in a manual transaction
            if not self.is_in_transaction():
                self.conn.rollback()
                logger.error(f"Error updating records in {table_name}, rolled back: {e}")
            else:
                logger.error(f"Error updating records in {table_name} in transaction: {e}")
            logger.debug(f"Failed query: {query}")
            logger.debug(f"Parameters: {params}")
            raise
        
    def delete_record(self, table_name: str, where_conditions: Dict[str, Any]):
        """
        Delete one or more records from a table based on specified conditions.
        Respects manual transactions - only commits if no active transaction.

        This method deletes all records from the specified table that match the given WHERE conditions.
        Both the conditions and the table name are validated to prevent SQL injection and ensure they are allowed.

        Args:
            table_name (str): The name of the table where the deletion will be performed.
            where_conditions (Dict[str, Any]): A dictionary mapping column names to values that
                must be matched for a record to be deleted (i.e., the WHERE clause).
        """
        if not self.conn:
            logger.error("Not connected to the database")
            raise Exception("Not connected to the database")
        
        if not isinstance(where_conditions, dict):
            logger.error(f"Where conditions must be a dictionary, got {type(where_conditions)}")
            raise ValueError("Where conditions must be a dictionary")
        
        table_name = self._validate_table_name(table_name)
        where_conditions_columns = self._validate_columns(table_name, list(where_conditions.keys()))
        
        where_clause = ' AND '.join([f'{col} = %({col})s' for col in where_conditions_columns])
        
        query = f"""
            DELETE FROM {table_name} WHERE {where_clause}
        """
        
        try:
            # Manual implementation of execute_query for DELETE
            query_preview = query[:100] + '...' if len(query) > 100 else query
            logger.debug(f"Executing query: {query_preview}")
            
            self.cursor.execute(query, where_conditions)
            logger.debug(f"Query executed with {len(where_conditions)} parameters")
            
            rows_affected = self.cursor.rowcount
            
            # Only commit if not in a manual transaction
            if not self.is_in_transaction():
                self.conn.commit()
                logger.info(f"Delete query executed and committed - {rows_affected} rows affected")
            else:
                logger.debug(f"Delete query executed - {rows_affected} rows affected (transaction pending)")
            
            if rows_affected == 0:
                logger.warning(f"No records were deleted from table {table_name} with conditions {where_conditions}")
            else:
                logger.debug(f"{rows_affected} records deleted from table {table_name}")
            
        except Exception as e:
            # Only rollback if not in a manual transaction
            if not self.is_in_transaction():
                self.conn.rollback()
                logger.error(f"Error deleting records from {table_name}, rolled back: {e}")
            else:
                logger.error(f"Error deleting records from {table_name} in transaction: {e}")
            logger.debug(f"Failed query: {query}")
            logger.debug(f"Parameters: {where_conditions}")
            raise
        
    def _detect_query_type(self, query: str) -> str:
        """
        Detect the type of SQL query.
        
        Args:
            query (str): The SQL query
            
        Returns:
            str: Query type (SELECT, INSERT, UPDATE, DELETE, or OTHER)
        """
        query_upper = query.strip().upper()
        
        if query_upper.startswith('SELECT'):
            return 'SELECT'
        elif query_upper.startswith('INSERT'):
            return 'INSERT'
        elif query_upper.startswith('UPDATE'):
            return 'UPDATE'
        elif query_upper.startswith('DELETE'):
            return 'DELETE'
        elif query_upper.startswith(('CREATE', 'DROP', 'ALTER')):
            return 'DDL'
        elif query_upper.startswith('WITH') and 'SELECT' in query_upper:
            return 'SELECT'  # CTE queries
        else:
            return 'OTHER'
        
    def _format_select_results(self, query: str, params: Dict[str, Any], value_format: Literal['tuple', 'dict', 'dataframe', 'scalar']) -> Any:
        """
        Format SELECT query results based on the specified format.
        Args:
            query (str): The original query (for dataframe conversion)
            params (Dict[str, Any]): Query parameters (for dataframe conversion)
            value_format (str): Desired format ('tuple', 'dict', 'dataframe', 'scalar')
        Returns:
            Formatted results based on value_format
        """
        try:
            if value_format == 'dict' or value_format == 'dataframe':
                cursor = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            elif value_format == 'tuple':
                cursor = self.conn.cursor()
            elif value_format == 'scalar':
                cursor = self.conn.cursor()
            else:
                raise ValueError(f"Invalid value format: {value_format}")

            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)

            if value_format == 'scalar':
                data = cursor.fetchone()
                cursor.close()
                if not data:
                    logger.warning("Scalar query returned no results")
                    return None
                if isinstance(data, dict):
                    # RealDictCursor returns dict
                    scalar_value = next(iter(data.values()))
                else:
                    scalar_value = data[0]
                logger.info(f"Scalar query executed - returned: {scalar_value}")
                return scalar_value

            results = cursor.fetchall()
            cursor.close()

            logger.info(f"SELECT query executed - {len(results)} rows returned in {value_format} format")

            if value_format == 'dataframe':
                return pd.DataFrame(results)
            else:
                return results

        except Exception as e:
            logger.error(f"Error formatting select results: {e}")
            logger.debug(f"Failed query: {query}")
            logger.debug(f"Parameters: {params}")
            raise
        
    def custom_query(
            self, 
            query: str, 
            params: Dict[str, Any] = None,
            value_format: Literal['tuple', 'dict', 'dataframe', 'scalar'] = 'dict'
        ) -> Any:
        """
        Execute a custom query with parameters and flexible return formats.
        
        Automatically detects query type and handles accordingly:
        - SELECT queries: Returns results in specified format
        - INSERT/UPDATE/DELETE queries: Commits and returns row count
        - Other queries: Executes and commits
        
        Args:
            query (str): The SQL query to execute
            params (Dict[str, Any], optional): Parameters for the query
            value_format (Literal['tuple', 'dict', 'dataframe', 'scalar'], optional): 
                Format for SELECT query results:
                - 'tuple': List of tuples (default)
                - 'dict': List of dictionaries with column names as keys
                - 'dataframe': pandas DataFrame
                - 'scalar': Single value (for queries returning one row, one column)
                
        Returns:
            For SELECT queries:
            - 'tuple': List of tuples [(col1, col2), ...]
            - 'dict': List of dicts [{'col1': val1, 'col2': val2}, ...]
            - 'dataframe': pandas DataFrame
            - 'scalar': Single value (for SUM, COUNT, EXISTS, etc.)
            
            For INSERT/UPDATE/DELETE: Number of affected rows
            For others: None
            
        Raises:
            Exception: If not connected or query execution fails
            ValueError: If invalid value_format specified
        """
        if not self.conn:
            logger.error("Not connected to the database")
            raise Exception("Not connected to the database")
        
        # Validate value_format
        valid_formats = ['tuple', 'dict', 'dataframe', 'scalar']
        if value_format not in valid_formats:
            raise ValueError(f"Invalid value_format: {value_format}. Must be one of: {valid_formats}")
        
        # Detect query type
        query_type = self._detect_query_type(query)
        
        try:
            # Execute the query
            if params:
                result = self.cursor.execute(query, params)
                logger.debug(f"Query executed with {len(params)} parameters")
            else:
                result = self.cursor.execute(query)
                logger.debug("Query executed without parameters")
            
            # Handle based on query type
            if query_type == 'SELECT':
                return self._format_select_results(query, params, value_format)
                
            elif query_type in ['INSERT', 'UPDATE', 'DELETE']:
                # For write queries, handle commit and return row count
                rows_affected = result.rowcount
                
                # Only commit if not in a manual transaction
                if not self.is_in_transaction():
                    self.conn.commit()
                    logger.info(f"{query_type} query executed and committed - {rows_affected} rows affected")
                else:
                    logger.debug(f"{query_type} query executed - {rows_affected} rows affected (transaction pending)")
                
                return rows_affected
                
            else:
                # For other queries (CREATE, DROP, etc.), commit if needed
                if not self.is_in_transaction():
                    self.conn.commit()
                    logger.info(f"Custom {query_type} query executed and committed")
                else:
                    logger.debug(f"Custom {query_type} query executed (transaction pending)")
                
                return None
                
        except Exception as e:
            # Only rollback if not in a manual transaction
            if not self.is_in_transaction():
                self.conn.rollback()
                logger.error(f"Error executing custom query, rolled back: {e}")
            else:
                logger.error(f"Error executing custom query in transaction: {e}")
            
            logger.debug(f"Failed query: {query}")
            logger.debug(f"Parameters: {params}")
            raise
        
    def query(self, query: str, params: Dict[str, Any] = None) -> Any:
        if not self.conn:
            logger.error("Not connected to the database")
            raise Exception("Not connected to the database")
        
        if params:
            self.cursor.execute(query, params)
        else:
            self.cursor.execute(query)
            
        return self.cursor.fetchall()
    
    def __enter__(self):
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type:
            logger.warning(f"Exception in context manager: {exc_type.__name__}: {exc_value}")
        self.disconnect()
    