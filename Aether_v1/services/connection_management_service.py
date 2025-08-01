import sqlite3
import logging
import threading
from pathlib import Path
from typing import Dict, Any, Generator
from contextlib import contextmanager
from config import DATABASE_FILE
from .database_service import DatabaseService

logger = logging.getLogger(__name__)

class ConnectionManagementService:
    """
    Centralized connection manager for all Aether controllers.
    Handles different connection scopes based on operation patterns.
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """Singleton pattern for application-wide connection management."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if getattr(self, '_initialized', False):
            return
            
        self.db_file = Path(DATABASE_FILE)
        self._local = threading.local()  # Thread-local storage for Streamlit
        self._connection_stats = {'created': 0, 'active': 0, 'closed': 0}
        self._initialized = True
        logger.info("ConnectionManagementService initialized")
        
    def _create_base_connection(self) -> sqlite3.Connection:
        """Create base SQLite connection with standard optimizations."""
        connection = sqlite3.connect(
            self.db_file,
            autocommit=True,
            check_same_thread=False,  # Allow cross-thread usage (controlled)
            timeout=30.0
        )
        
        # Base SQLite optimizations for Aether
        connection.execute("PRAGMA journal_mode=WAL")      # Better concurrency
        connection.execute("PRAGMA synchronous=NORMAL")    # Balanced safety/speed
        connection.execute("PRAGMA foreign_keys=ON")       # Enforce constraints
        connection.execute("PRAGMA temp_store=MEMORY")     # Faster temp operations
        
        with self._lock:
            self._connection_stats['created'] += 1
            self._connection_stats['active'] += 1
        
        logger.debug("Created optimized SQLite connection")
        return connection
    
    def _configure_for_session(self, connection: sqlite3.Connection) -> None:
        """Configure connection for session-scoped operations."""
        # Moderate cache for interactive sessions
        connection.execute("PRAGMA cache_size=10000")  # 10MB cache
        connection.execute("PRAGMA mmap_size=268435456")  # 256MB memory map
        logger.debug("Configured connection for session scope")
    
    def _configure_for_batch(self, connection: sqlite3.Connection) -> None:
        """Configure connection for batch processing operations."""
        # Aggressive optimizations for batch processing
        connection.execute("PRAGMA cache_size=50000")     # 50MB cache
        connection.execute("PRAGMA synchronous=OFF")      # Fastest writes
        connection.execute("PRAGMA mmap_size=1073741824") # 1GB memory map
        connection.execute("PRAGMA journal_size_limit=67108864")  # 64MB journal
        logger.debug("Configured connection for batch scope")
    
    def _configure_for_quick_read(self, connection: sqlite3.Connection) -> None:
        """Configure connection for quick read operations."""
        # Lightweight configuration for fast reads
        connection.execute("PRAGMA cache_size=5000")   # 5MB cache
        connection.execute("PRAGMA query_only=ON")     # Read-only mode
        logger.debug("Configured connection for quick-read scope")
    
    def _close_connection(self, connection: sqlite3.Connection) -> None:
        """Safely close connection and update stats."""
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
        
        WHEN TO USE:
        - User interactions across multiple Streamlit widgets
        - Financial analysis that spans multiple operations
        - User session management
        - Multi-step workflows (like PDF processing + analysis)
        
        BENEFITS:
        - Connection reused during user session
        - Optimized for interactive workloads
        - Automatic cleanup when session ends
        """
        # Use thread-local storage for session persistence
        if not hasattr(self._local, 'session_connection'):
            self._local.session_connection = self._create_base_connection()
            self._configure_for_session(self._local.session_connection)
            logger.debug("Created new session-scoped connection")
        
        # Create DatabaseService with managed connection
        db_service = DatabaseService(self.db_file)
        db_service.conn = self._local.session_connection
        db_service.cursor = db_service.conn.cursor()
        db_service._managed_connection = True  # Mark as externally managed
        
        try:
            yield db_service
        finally:
            # Close cursor but keep connection alive for session reuse
            if db_service.cursor:
                db_service.cursor.close()
                db_service.cursor = None
    
    @contextmanager
    def get_batch_processing_service(self) -> Generator[DatabaseService, None, None]:
        """
        Get DatabaseService optimized for batch operations.
        
        WHEN TO USE:
        - Processing multiple PDF files
        - Bulk data imports/exports
        - Large transaction insertions
        - Data migration operations
        
        BENEFITS:
        - Maximum write performance
        - Large memory allocation
        - Optimized for throughput over safety
        """
        connection = self._create_base_connection()
        self._configure_for_batch(connection)
        
        db_service = DatabaseService(self.db_file)
        db_service.conn = connection
        db_service.cursor = connection.cursor()
        db_service._managed_connection = True
        
        try:
            yield db_service
        finally:
            # Restore normal settings before closing
            try:
                connection.execute("PRAGMA synchronous=NORMAL")
                if db_service.cursor:
                    db_service.cursor.close()
            except Exception as e:
                logger.warning(f"Error restoring connection settings: {e}")
            finally:
                self._close_connection(connection)
    
    @contextmanager
    def get_quick_read_service(self) -> Generator[DatabaseService, None, None]:
        """
        Get DatabaseService for quick, isolated read operations.
        
        WHEN TO USE:
        - Dashboard data refreshes
        - User validation checks
        - Quick data lookups
        - Read-only operations
        
        BENEFITS:
        - Fast connection setup/teardown
        - Read-only safety
        - Minimal resource usage
        """
        connection = self._create_base_connection()
        self._configure_for_quick_read(connection)
        
        db_service = DatabaseService(self.db_file)
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
        if hasattr(self._local, 'session_connection'):
            try:
                self._close_connection(self._local.session_connection)
                delattr(self._local, 'session_connection')
                logger.info("Session connections cleaned up")
            except Exception as e:
                logger.error(f"Error during session cleanup: {e}")
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get current connection statistics for monitoring."""
        with self._lock:
            return {
                'connections_created': self._connection_stats['created'],
                'connections_active': self._connection_stats['active'],
                'connections_closed': self._connection_stats['closed'],
                'database_file': str(self.db_file),
                'has_session_connection': hasattr(self._local, 'session_connection')
            }