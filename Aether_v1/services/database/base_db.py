from abc import ABC, abstractmethod
from decimal import Decimal
from datetime import date
import logging
import psycopg2
import psycopg2.extras
from contextlib import contextmanager
from typing import Optional, Generator, Literal, List, Set, Dict, Tuple, Any 

logger = logging.getLogger(__name__)

class BaseDBService(ABC):
    """
    Abstract base class for all table services.
    Provides common database operations, validation, and connection management.
    """
    def __init__(self, connection: psycopg2.extensions.connection):
        self.connection = connection
        self.cursor: Optional[psycopg2.extensions.cursor] = None
        self._transaction_level = 0
        self._savepoints = []
        
    @property
    @abstractmethod
    def table_name(self) -> str:
        """Return the name of the table this service operates on."""
        pass
    
    @property
    @abstractmethod
    def allowed_columns(self) -> Set[str]:
        """Return the set of allowed columns for this table."""
        pass
    
    @property
    @abstractmethod
    def id_col(self) -> str:
        """Return the name of the ID column for this table."""
        pass
    
    def _get_cursor(self, dict_cursor: bool = False) -> psycopg2.extensions.cursor:
        """Get a cursor for the connection, optionally configured for dictionary output."""
        if dict_cursor:
            return self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        else:
            return self.connection.cursor()
    
    def _begin_transaction(self) -> None:
        """Start a new transaction or create savepoint."""
        if not self.connection:
            raise Exception("No database connection")
        
        self._transaction_level += 1
        
        if self._transaction_level == 1:
            self.connection.cursor().execute("BEGIN;")
            logger.debug("Transaction started")
        else:
            savepoint_name = f"sp_{self._transaction_level}"
            self.connection.cursor().execute(f"SAVEPOINT {savepoint_name}")
            self._savepoints.append(savepoint_name)
            logger.debug(f"Savepoint created: {savepoint_name}")
    
    def _commit_transaction(self) -> None:
        """Commit current transaction or release savepoint."""
        if not self.connection:
            raise Exception("No database connection")
        
        if self._transaction_level == 0:
            logger.warning("No active transaction to commit")
            return
        
        if self._transaction_level == 1:
            self.connection.commit()
            logger.debug("Transaction committed")
        else:
            savepoint_name = self._savepoints.pop()
            self.connection.cursor().execute(f"RELEASE SAVEPOINT {savepoint_name}")
            logger.debug(f"Savepoint released: {savepoint_name}")
        
        self._transaction_level -= 1
    
    def _rollback_transaction(self) -> None:
        """Rollback current transaction or revert to savepoint."""
        if not self.connection:
            raise Exception("No database connection")
        
        if self._transaction_level == 0:
            logger.warning("No active transaction to rollback")
            return
        
        if self._transaction_level == 1:
            self.connection.rollback()
            logger.debug("Transaction rolled back")
        else:
            savepoint_name = self._savepoints.pop()
            self.connection.cursor().execute(f"ROLLBACK TO SAVEPOINT {savepoint_name}")
            logger.debug(f"Rolled back to savepoint: {savepoint_name}")
        
        self._transaction_level -= 1
    
    @contextmanager
    def transaction(self) -> Generator[None, None, None]:
        """Context manager for automatic transaction handling."""
        self._begin_transaction()
        try:
            yield
            self._commit_transaction()
        except Exception as e:
            self._rollback_transaction()
            raise
    
    def is_in_transaction(self) -> bool:
        """Check if there is an active transaction."""
        return self._transaction_level > 0
    
    def _validate_columns(self, columns: List[str]) -> List[str]:
        """Validate columns for this table."""
        if not columns or not isinstance(columns, list):
            raise ValueError("Columns must be a list of strings")
        
        validated_columns = []
        for col in columns:
            if not col or not isinstance(col, str):
                raise ValueError(f"Invalid column name: {col}")
            
            if col not in self.allowed_columns:
                raise ValueError(f"Column '{col}' not allowed for table '{self.table_name}'")
            
            validated_columns.append(col)
        
        return validated_columns
    
    def _validate_conditions(self, conditions: Dict[str, Any]) -> Dict[str, Any]:
        """Validate conditions for the query, based on the allowed columns for the table."""
        validated_conditions = {}
        
        for col, value in conditions.items():
            if not col or not isinstance(col, str):
                raise ValueError(f"Invalid column name: {col}")
            
            if col not in self.allowed_columns:
                raise ValueError(f"Column '{col}' not allowed for table '{self.table_name}'")
            else:
                validated_conditions[col] = value
                
        return validated_conditions
    
    def execute_query(
        self,
        query: str,
        params: Optional[Dict[str, Any]] = None,
        fetch: Optional[Literal['all', 'one']] = None,
        dict_cursor: bool = False,
        batch: Optional[bool] = False,
    ) -> List[Tuple[Any, ...] | Dict[str, Any]] | Tuple[Any, ...] | Dict[str, Any] | None:
        """Execute a custom SQL query."""
        cursor = self._get_cursor(dict_cursor=dict_cursor)
        
        try:
            if batch:
                psycopg2.extras.execute_batch(cursor, query, params or {})
                return
            else:
                cursor.execute(query, params or {})
            
            if fetch == 'all':
                return cursor.fetchall()
            elif fetch == 'one':
                return cursor.fetchone()
            else:
                return None
        finally:
            cursor.close()
    
    def find_by_id(self, id: int, columns: Optional[List[str]] = None) -> Optional[Dict[str, Any]]:
        """Find a record by its ID."""

        if columns:
            columns = self._validate_columns(columns)
            query = f"SELECT {', '.join(columns)} FROM {self.table_name} WHERE {self.id_col} = %(id)s"
        else:
            query = f"SELECT * FROM {self.table_name} WHERE {self.id_col} = %(id)s"
        
        result = self.execute_query(query, params={'id': id}, fetch='one', dict_cursor=True)
        
        return result if result else None
        
    def count(self, **conditions: Any) -> int:
        """Count the number of records in the table."""
        query = f"SELECT COUNT(*) FROM {self.table_name}"
        
        if conditions:
            params = self._validate_conditions(conditions)
            
            query += " WHERE "
            query += " AND ".join([f"{col} = %({col})s" for col in params.keys()])
        else:
            params = {}

        result = self.execute_query(query, params= params, fetch= 'one')
        return result[0] if result else 0
    
    def find_id(self, **conditions: Any) -> int | None:
        """Find the ID of a record by its conditions."""
        
        if self.count(**conditions) > 1:
            raise ValueError(f"Conditions {conditions} match multiple records")
        
        query = f"SELECT {self.id_col} FROM {self.table_name}"
        
        if conditions:
            params = self._validate_conditions(conditions)
            
            query += " WHERE "
            query += " AND ".join([f"{col} = %({col})s" for col in params.keys()])
        else:
            params = {}
            
        result = self.execute_query(query, params= params, fetch= 'one')
        
        return result[0] if result else None
    
    def exists(self, **conditions: Any) -> bool:
        """Check if a record exists in the table."""
        query = f"SELECT EXISTS(SELECT 1 FROM {self.table_name}"
        
        if conditions:
            params = self._validate_conditions(conditions)
            
            query += " WHERE "
            query += " AND ".join([f"{col} = %({col})s" for col in params.keys()])
        
        query += ")"
        
        return self.execute_query(query, params= params, fetch= 'one')[0]
    
    def get_unique_values(self, column: str, **conditions: Any) -> List[Any]:
        """Get unique values for a column."""
        if column not in self.allowed_columns:
            raise ValueError(f"Column '{column}' not allowed for table '{self.table_name}'")
        
        query = f"SELECT DISTINCT {column} FROM {self.table_name}"
        
        if conditions:
            params = self._validate_conditions(conditions)
            
            query += " WHERE "
            query += " AND ".join([f"{col} = %({col})s" for col in params.keys()])
        else:
            params = {}
        
        result = self.execute_query(query, params= params, fetch= 'all')
        
        return [value[0] for value in result] if result else []
    
    def get_sum(self, column: str, start_date: Optional[date] = None, end_date: Optional[date] = None, **conditions: Any) -> Decimal:
        """Get the sum of a column."""
        query = f"SELECT SUM({column}) FROM {self.table_name}"
        params = {}
        
        if conditions:
            params = self._validate_conditions(conditions)
            
            query += " WHERE "
            query += " AND ".join([f"{col} = %({col})s" for col in params.keys()])
            
        if start_date and end_date:
            query += f" AND date BETWEEN %(start_date)s AND %(end_date)s"
            params['start_date'] = start_date
            params['end_date'] = end_date
        elif start_date:
            query += f" AND date >= %(start_date)s"
            params['start_date'] = start_date
        elif end_date:
            query += f" AND date <= %(end_date)s"
            params['end_date'] = end_date
            
        result = self.execute_query(query, params= params, fetch= 'one')
        
        return result[0] if result[0] is not None else Decimal(0)
    
    def update(self, id: int, **updates: Any) -> None:
        """Update a record by its ID."""
        params = self._validate_conditions(updates)
        params['id'] = id
        
        with self.transaction():
            query = f"UPDATE {self.table_name} SET "
            query += ", ".join([f"{col} = %({col})s" for col in updates])
            query += f" WHERE {self.id_col} = %(id)s"
            
            self.execute_query(query, params= params)
            
    def add_value(self, column: str, value: float | Decimal, **conditions: Any) -> None:
        """Add a value to a column."""
        with self.transaction():
            query = f"UPDATE {self.table_name} SET {column} = {column} + %(value)s"
            
            if conditions:
                params = self._validate_conditions(conditions)
                
                query += " WHERE "
                query += " AND ".join([f"{col} = %({col})s" for col in params.keys()])
            else:
                params = {}
                
            params['value'] = value
                
            self.execute_query(query, params= params)