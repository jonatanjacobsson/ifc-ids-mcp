"""Thread-safe session storage."""

import threading
from typing import Dict, Optional, List
from ids_mcp_server.session.models import SessionData


class SessionStorage:
    """
    Thread-safe in-memory session storage.

    This class provides thread-safe operations for storing and retrieving
    session data across multiple concurrent requests.
    """

    def __init__(self):
        """Initialize empty storage with thread lock."""
        self._storage: Dict[str, SessionData] = {}
        self._lock = threading.Lock()

    def get(self, session_id: str) -> Optional[SessionData]:
        """
        Get session data (thread-safe).

        Args:
            session_id: Session identifier

        Returns:
            SessionData if found, None otherwise
        """
        with self._lock:
            return self._storage.get(session_id)

    def set(self, session_id: str, data: SessionData) -> None:
        """
        Set session data (thread-safe).

        Args:
            session_id: Session identifier
            data: Session data to store
        """
        with self._lock:
            self._storage[session_id] = data

    def delete(self, session_id: str) -> None:
        """
        Delete session (thread-safe).

        Args:
            session_id: Session to remove
        """
        with self._lock:
            if session_id in self._storage:
                del self._storage[session_id]

    def get_all_session_ids(self) -> List[str]:
        """
        Get all active session IDs.

        Returns:
            List of session IDs
        """
        with self._lock:
            return list(self._storage.keys())

    def clear(self) -> None:
        """Clear all sessions (useful for testing)."""
        with self._lock:
            self._storage.clear()


# Global session storage instance
_session_storage = SessionStorage()


def get_session_storage() -> SessionStorage:
    """
    Get the global session storage instance.

    Returns:
        SessionStorage: Global session storage
    """
    return _session_storage
