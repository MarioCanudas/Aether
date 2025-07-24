import psycopg2
import logging
import threading
from typing import Dict, Any, Generator
from contextlib import contextmanager
from dotenv import load_dotenv
import os
from .database_service import DatabaseService

load_dotenv()

logger = logging.getLogger(__name__)

DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT')
DB_NAME = os.getenv('DB_NAME')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')

class ConnectionManagementService:
    """
    Centralized connection manager for all Aether controllers.
    Handles different connection scopes based on operation patterns.
    Creates and configures psycopg2 connections for each use case, and returns
    DatabaseService instances initialized with those connections.
    """
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if getattr(self, '_initialized', False):
            return
        self._local = threading.local()
        self._connection_stats = {'created': 0, 'active': 0, 'closed': 0}
        self._initialized = True
        logger.info("ConnectionManagementService initialized")

    def _create_base_connection(self) -> psycopg2.extensions.connection:
        connection = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            connect_timeout=10
        )
        with self._lock:
            self._connection_stats['created'] += 1
            self._connection_stats['active'] += 1
        logger.debug("Created PostgreSQL connection")
        return connection

    def _configure_for_session(self, connection: psycopg2.extensions.connection) -> None:
        """
        Configure connection for session-scoped operations (default settings).
        """
        # Example: Set a moderate statement timeout
        with connection.cursor() as cur:
            cur.execute("SET statement_timeout = 10000;")  # 10 seconds
        logger.debug("Configured connection for session scope")

    def _configure_for_batch(self, connection: psycopg2.extensions.connection) -> None:
        """
        Configure connection for batch processing operations (bulk inserts, etc).
        """
        # Example: Increase work_mem, disable synchronous_commit for speed
        with connection.cursor() as cur:
            cur.execute("SET work_mem = '128MB';")
            cur.execute("SET synchronous_commit = OFF;")
            cur.execute("SET statement_timeout = 60000;")  # 60 seconds
        logger.debug("Configured connection for batch scope")

    def _configure_for_quick_read(self, connection: psycopg2.extensions.connection) -> None:
        """
        Configure connection for quick, read-only operations.
        """
        # Example: Set read-only transaction, lower timeout
        with connection.cursor() as cur:
            cur.execute("SET default_transaction_read_only = ON;")
            cur.execute("SET statement_timeout = 2000;")  # 2 seconds
        logger.debug("Configured connection for quick-read scope")

    def _close_connection(self, connection: psycopg2.extensions.connection) -> None:
        try:
            connection.close()
            with self._lock:
                self._connection_stats['active'] -= 1
                self._connection_stats['closed'] += 1
            logger.debug("Connection closed successfully")
        except Exception as e:
            logger.error(f"Error closing connection: {e}")

    @contextmanager
    def get_session_scoped_service(self) -> Generator[DatabaseService, None, None]:
        """
        Get DatabaseService with session-scoped connection.
        Use for user interactions, session workflows, etc.
        """
        connection = self._create_base_connection()
        self._configure_for_session(connection)
        db_service = DatabaseService()
        db_service.conn = connection
        db_service.cursor = connection.cursor()
        db_service._managed_connection = True
        try:
            yield db_service
        finally:
            if db_service.cursor:
                db_service.cursor.close()
            self._close_connection(connection)

    @contextmanager
    def get_batch_processing_service(self) -> Generator[DatabaseService, None, None]:
        """
        Get DatabaseService optimized for batch operations (bulk inserts, data migration).
        """
        connection = self._create_base_connection()
        self._configure_for_batch(connection)
        db_service = DatabaseService()
        db_service.conn = connection
        db_service.cursor = connection.cursor()
        db_service._managed_connection = True
        try:
            yield db_service
        finally:
            if db_service.cursor:
                db_service.cursor.close()
            self._close_connection(connection)

    @contextmanager
    def get_quick_read_service(self) -> Generator[DatabaseService, None, None]:
        """
        Get DatabaseService for quick, isolated read-only operations.
        """
        connection = self._create_base_connection()
        self._configure_for_quick_read(connection)
        db_service = DatabaseService()
        db_service.conn = connection
        db_service.cursor = connection.cursor()
        db_service._managed_connection = True
        try:
            yield db_service
        finally:
            if db_service.cursor:
                db_service.cursor.close()
            self._close_connection(connection)

    def cleanup_session(self) -> None:
        """
        Clean up current thread's session-scoped connections.
        Call this when Streamlit session ends or user logs out.
        """
        # No-op for PostgreSQL, but kept for API compatibility
        logger.info("Session cleanup called (no-op for PostgreSQL)")

    def get_connection_stats(self) -> Dict[str, Any]:
        """
        Get current connection statistics for monitoring and debugging.
        Returns:
            dict: Dictionary with connection stats and database info.
        """
        with self._lock:
            return {
                'connections_created': self._connection_stats['created'],
                'connections_active': self._connection_stats['active'],
                'connections_closed': self._connection_stats['closed'],
                'database_host': DB_HOST,
                'database_name': DB_NAME,
            }