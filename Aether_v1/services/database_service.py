import sqlite3
import pandas as pd
from typing import Optional, Dict, Any, List, Literal, Tuple, Generator
from pathlib import Path
import logging
import re
from contextlib import contextmanager
from config import DATABASE_FILE

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
    ALLOWED_TABLES = {'users', 'transactions'}
    ALLOWED_COLUMNS = {
        'users': {'id', 'username', 'created_at'},
        'transactions': {'id', 'user_id', 'date', 'description', 'amount', 'type', 'bank', 'statement_type', 'filename'},
    }
    
    def __init__(self, db_file: str= DATABASE_FILE):
        self.db_file = Path(db_file)
        self.conn: Optional[sqlite3.Connection] = None
        self.cursor: Optional[sqlite3.Cursor] = None
        self._transaction_level = 0  # Track nested transaction levels
        self._savepoints = []  # Stack of savepoint names for nested transactions
        
    def connect(self) -> None:
        """
        Connect to the database.
        """
        try:
            self.conn = sqlite3.connect(
                self.db_file, 
                autocommit= False,
                check_same_thread= False,
                timeout= 30.0
            )
            self.cursor = self.conn.cursor()
            logger.info(f"Connected to database: {self.db_file}")
        except Exception as e:
            logger.error(f"Error connecting to database: {e}")
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
            VALUES ({', '.join([f':{col}' for col in columns])})
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

    def insert_multiple_records(self, table_name: str, records: List[dict]) -> None:
        """
        Inserts multiple records into the database efficiently.
        Respects manual transactions - only commits if no active transaction.
        
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
        
        # Verify that all records have the same columns
        for i, record in enumerate(records):
            if set(record.keys()) != set(columns):
                logger.error(f"Record {i} has different columns than the first record")
                raise ValueError(f"All records must have the same columns. Record {i} differs.")
        
        query = f"""
            INSERT INTO {table_name} ({', '.join(columns)})
            VALUES ({', '.join([f':{col}' for col in columns])})
        """
        
        try:
            self.cursor.executemany(query, records)
            
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
            where_conditions: Dict[str, Any], 
            columns: Optional[List[str]] = None,
            order_by: Optional[str] = None,
            limit: Optional[int] = None,
            value_format: Literal['dict', 'tuple', 'dataframe'] = 'dataframe'
        ) -> List[Dict[str, Any]] | List[Tuple[Any]] | pd.DataFrame:
        """
        Retrieve records from a table based on specified conditions.

        Args:
            table_name (str): The name of the table from which to retrieve records.
            where_conditions (Dict[str, Any]): A dictionary specifying the column-value pairs to filter the records (used in the WHERE clause).
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
        
        if not isinstance(where_conditions, dict):
            logger.error(f"Where conditions must be a dictionary, got {type(where_conditions)}")
            raise ValueError("Where conditions must be a dictionary")
        
        table_name = self._validate_table_name(table_name)
        where_conditions_columns = self._validate_columns(table_name, list(where_conditions.keys()))
        
        where_clause = ' AND '.join([f'{col} = :{col}' for col in where_conditions_columns])
        
        query = f"""
            SELECT * FROM {table_name} WHERE {where_clause}
        """
        
        if columns:
            columns_clause = ', '.join(columns)
            query = f"""
                SELECT {columns_clause} FROM {table_name} WHERE {where_clause}
            """
            
        if limit:
            limit_clause = f'LIMIT {limit}'
            query += '\n' + limit_clause
            
        if order_by:
            order_by_clause = f'ORDER BY {order_by}'
            query += '\n' + order_by_clause
        
        try:
            if value_format == 'dataframe':
                # Manual implementation of query_to_dataframe
                query_preview = query[:50] + '...' if len(query) > 50 else query
                logger.debug(f"Converting query to DataFrame: {query_preview}")
                
                try:
                    df = pd.read_sql_query(query, self.conn, params= where_conditions)
                    logger.debug(f"DataFrame created with {len(where_conditions)} parameters")
                    logger.info(f"DataFrame created successfully - Shape: {df.shape}")
                    
                    # Warning for very large DataFrames
                    if len(df) > 5000:
                        logger.warning(f"Large DataFrame created: {len(df)} rows - consider adding LIMIT")
                    
                    return df
                    
                except Exception as e:
                    logger.error(f"Error converting query to DataFrame: {e}")
                    logger.debug(f"Failed query: {query}")
                    raise
            else:
                original_row_factory = self.conn.row_factory
                
                if value_format == 'dict':
                    self.conn.row_factory = lambda cursor, row: dict(
                        zip([col[0] for col in cursor.description], row)
                    )
                elif value_format == 'tuple':
                    self.conn.row_factory = None
                else:
                    raise ValueError(f"Invalid value format: {value_format}")
                
                cursor = self.conn.cursor()
                cursor.execute(query, where_conditions)
                results = cursor.fetchall()
                
                self.conn.row_factory = original_row_factory
                
                logger.info(f"Retrieved {len(results)} records from {table_name} in {value_format} format")
                return results
                
        except Exception as e:
            logger.error(f"Error getting record from {table_name}: {e}")
            logger.debug(f"Failed query: {query}")
            logger.debug(f"Parameters: {where_conditions}")
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
        
        set_clause = ', '.join([f'{col} = :set_{col}' for col in new_record_columns])
        where_clause = ' AND '.join([f'{col} = :where_{col}' for col in where_conditions_columns])
        
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
            
            result = self.cursor.execute(query, params)
            logger.debug(f"Query executed with {len(params)} parameters")
            
            rows_affected = result.rowcount
            
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
        
        where_clause = ' AND '.join([f'{col} = :{col}' for col in where_conditions_columns])
        
        query = f"""
            DELETE FROM {table_name} WHERE {where_clause}
        """
        
        try:
            # Manual implementation of execute_query for DELETE
            query_preview = query[:100] + '...' if len(query) > 100 else query
            logger.debug(f"Executing query: {query_preview}")
            
            result = self.cursor.execute(query, where_conditions)
            logger.debug(f"Query executed with {len(where_conditions)} parameters")
            
            rows_affected = result.rowcount
            
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
        
    def __enter__(self):
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type:
            logger.warning(f"Exception in context manager: {exc_type.__name__}: {exc_value}")
        self.disconnect()
    
    