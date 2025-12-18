import logging
import threading

from models.users import NewUser, UserProfile

from .connection_management_service import ConnectionManagementService
from .database.users import UserDBService

logger = logging.getLogger(__name__)


class UserSessionService:
    """
    Service for managing user sessions.
    """

    _instance: "UserSessionService | None" = None
    _lock = threading.Lock()
    _initialized: bool = False
    _local: threading.local
    connection_manager: ConnectionManagementService
    current_user_id: int | None

    def __new__(cls) -> "UserSessionService":
        """Singleton pattern for application-wide session management."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if getattr(self, "_initialized", False):
            return

        self._local = threading.local()  # Thread-local storage for Streamlit sessions
        self.connection_manager = ConnectionManagementService()
        self._initialized = True
        self.current_user_id = None
        logger.info("UserSessionService initialized")

    def get_available_users(self) -> list[str]:
        """Return all available usernames as a flat list of strings.

        Some database drivers return rows as tuples or dicts; this method
        normalizes the results to a simple list of usernames to integrate
        cleanly with Streamlit widgets.

        Returns:
            A list of usernames.
        """
        try:
            with self.connection_manager.get_quick_read_connection() as conn:
                users_table = UserDBService(conn)
                return users_table.get_unique_values(column="username")

        except Exception as e:
            logger.error(f"Error fetching available users: {e}")
            return []

    def set_current_user_by_id(self, user_id: int | None) -> None:
        """
        Set the current user by their ID.

        Args:
            user_id: User ID to set as current, or None to clear.

        Raises:
            ValueError: If the user with the given ID is not found.
        """
        if user_id is None:
            raise ValueError("User ID cannot be None")

        with self.connection_manager.get_quick_read_connection() as conn:
            users_table = UserDBService(conn)
            user: UserProfile | None = users_table.get_user(user_id=user_id)

            if user is None:
                raise ValueError(f"User with ID {user_id} not found")

            self.current_user_id = user_id
            self._local.current_user = user
            logger.info(f"Current user set: {user.username} (ID: {user_id})")

    def clear_current_user(self) -> None:
        """
        Clear the current user.
        """
        self.current_user_id = None
        self._local.current_user = None

    def get_user_id_by_username(self, username: str) -> int | None:
        """Return the user ID for the given username or raise if not found."""
        if not isinstance(username, str) or not username:
            raise ValueError("Username must be a non-empty string")

        with self.connection_manager.get_quick_read_connection() as conn:
            users_table = UserDBService(conn)
            user_id = users_table.find_id(username=username)
            if user_id is None:
                raise ValueError(f"User with username {username} not found")
            return user_id

    def get_current_user(self) -> UserProfile | None:
        """Return the current user model for this session if set."""
        return getattr(self._local, "current_user", None)

    def get_current_user_id(self) -> int | None:
        """Return the current user's ID if a user is set for this session."""
        user = self.get_current_user()
        return user.user_id if user else None

    def get_current_username(self) -> str | None:
        """Return the current user's username if a user is set for this session."""
        user = self.get_current_user()
        return user.username if user else None

    def add_user(self, username: str, password: str | None = None) -> None:
        try:
            with self.connection_manager.get_session_connection() as conn:
                users_table = UserDBService(conn)

                users_table.add_user(NewUser(username=username, password_hash=password))
        except Exception as e:
            logger.error(f"Error adding user {username}: {e}")
            raise e
