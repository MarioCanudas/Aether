import logging
import os
import threading
from collections.abc import Generator
from contextlib import contextmanager
from typing import Any

from psycopg2 import extensions, pool
from streamlit import secrets

logger = logging.getLogger(__name__)

IS_SUPABASE = bool(secrets.get("IS_SUPABASE", False))
DB_HOST = secrets.get("DB_HOST")
DB_PORT = secrets.get("DB_PORT")
DB_NAME = secrets.get("DB_NAME")
DB_USER = secrets.get("DB_USER")
DB_PASSWORD = secrets.get("DB_PASSWORD")


class ConnectionManagementService:
    """
    Enhanced connection manager with connection pooling for better performance.
    """

    _instance: "ConnectionManagementService | None" = None
    _lock = threading.Lock()
    _initialized: bool = False
    _connection_stats: dict[str, int]
    _quick_read_pool: pool.ThreadedConnectionPool
    _session_pool: pool.ThreadedConnectionPool
    _batch_pool: pool.ThreadedConnectionPool

    def __new__(cls) -> "ConnectionManagementService":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if getattr(self, "_initialized", False):
            return

        # Initialize connection pools for different operation types
        self._init_connection_pools()
        self._connection_stats = {"created": 0, "active": 0, "closed": 0}
        self._initialized = True

    def _init_connection_pools(self) -> None:
        """Initialize connection pools for different operation types."""
        connection_params = {
            "host": DB_HOST,
            "port": DB_PORT,
            "dbname": DB_NAME,
            "user": DB_USER,
            "password": DB_PASSWORD,
            "connect_timeout": 10,
        }

        if IS_SUPABASE:
            connection_params["sslmode"] = "require"
            connection_params["gssencmode"] = "disable"

        # Quick read pool - optimized for fast read operations
        try:
            self._quick_read_pool = pool.ThreadedConnectionPool(
                minconn=1, maxconn=5, **connection_params
            )

            # Session pool - for user interactions
            self._session_pool = pool.ThreadedConnectionPool(
                minconn=1, maxconn=2, **connection_params
            )

            # Batch pool - for bulk operations
            self._batch_pool = pool.ThreadedConnectionPool(
                minconn=1, maxconn=2, **connection_params
            )
        except Exception as e:
            logger.error(f"Failed to initialize connection pools: {e}")
            raise

    def _configure_for_session(self, connection: extensions.connection) -> None:
        """Configure connection for session-scoped operations."""
        with connection.cursor() as cur:
            cur.execute("SET statement_timeout = 10000;")
        logger.debug("Configured connection for session scope")

    def _configure_for_batch(self, connection: extensions.connection) -> None:
        """Configure connection for batch processing operations."""
        with connection.cursor() as cur:
            cur.execute("SET work_mem = '128MB';")
            cur.execute("SET synchronous_commit = OFF;")
            cur.execute("SET statement_timeout = 60000;")
        logger.debug("Configured connection for batch scope")

    def _configure_for_quick_read(self, connection: extensions.connection) -> None:
        """Configure connection for quick, read-only operations."""
        with connection.cursor() as cur:
            cur.execute("SET default_transaction_read_only = ON;")
            cur.execute("SET statement_timeout = 2000;")
        logger.debug("Configured connection for quick-read scope")

    @contextmanager
    def get_session_connection(self) -> Generator[extensions.connection, None, None]:
        """Get session-scoped connection from pool."""
        connection = self._session_pool.getconn()
        self._configure_for_session(connection)
        try:
            with self._lock:
                self._connection_stats["active"] += 1
            yield connection
        finally:
            self._session_pool.putconn(connection)
            with self._lock:
                self._connection_stats["active"] -= 1

    @contextmanager
    def get_batch_connection(self) -> Generator[extensions.connection, None, None]:
        """Get batch processing connection from pool."""
        connection = self._batch_pool.getconn()
        self._configure_for_batch(connection)
        try:
            with self._lock:
                self._connection_stats["active"] += 1
            yield connection
        finally:
            self._batch_pool.putconn(connection)
            with self._lock:
                self._connection_stats["active"] -= 1

    @contextmanager
    def get_quick_read_connection(self) -> Generator[extensions.connection, None, None]:
        """Get quick read connection from pool."""
        connection = self._quick_read_pool.getconn()
        self._configure_for_quick_read(connection)
        try:
            with self._lock:
                self._connection_stats["active"] += 1
            yield connection
        finally:
            self._quick_read_pool.putconn(connection)
            with self._lock:
                self._connection_stats["active"] -= 1

    def get_connection_stats(self) -> dict[str, Any]:
        """Get current connection statistics."""
        with self._lock:
            return {
                "quick_read_pool_size": self._quick_read_pool.closed,
                "session_pool_size": self._session_pool.closed,
                "batch_pool_size": self._batch_pool.closed,
                "connections_active": self._connection_stats["active"],
                "database_host": os.getenv("DB_HOST"),
                "database_name": os.getenv("DB_NAME"),
            }

    def close_all_pools(self) -> None:
        """Close all connection pools (for cleanup)."""
        if hasattr(self, "_quick_read_pool"):
            self._quick_read_pool.closeall()
        if hasattr(self, "_session_pool"):
            self._session_pool.closeall()
        if hasattr(self, "_batch_pool"):
            self._batch_pool.closeall()
