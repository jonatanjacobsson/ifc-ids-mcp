"""RED: Tests for session storage."""

import pytest
import threading
from ids_mcp_server.session.storage import SessionStorage
from ids_mcp_server.session.models import SessionData


def test_storage_initialization():
    """Test creating empty storage."""
    storage = SessionStorage()
    assert storage is not None
    assert storage.get_all_session_ids() == []


def test_storage_set_and_get():
    """Test storing and retrieving session data."""
    storage = SessionStorage()
    session_data = SessionData(session_id="test-123")

    storage.set("test-123", session_data)
    retrieved = storage.get("test-123")

    assert retrieved is not None
    assert retrieved.metadata.session_id == "test-123"


def test_storage_delete():
    """Test deleting session data."""
    storage = SessionStorage()
    session_data = SessionData(session_id="test-456")

    storage.set("test-456", session_data)
    assert storage.get("test-456") is not None

    storage.delete("test-456")
    assert storage.get("test-456") is None


def test_storage_get_all_session_ids():
    """Test getting all session IDs."""
    storage = SessionStorage()

    storage.set("session-1", SessionData("session-1"))
    storage.set("session-2", SessionData("session-2"))
    storage.set("session-3", SessionData("session-3"))

    session_ids = storage.get_all_session_ids()
    assert len(session_ids) == 3
    assert "session-1" in session_ids
    assert "session-2" in session_ids
    assert "session-3" in session_ids


def test_storage_thread_safety():
    """Test concurrent access to storage."""
    storage = SessionStorage()
    errors = []

    def create_session(sid):
        try:
            data = SessionData(session_id=sid)
            storage.set(sid, data)
        except Exception as e:
            errors.append(e)

    # Create 100 sessions concurrently
    threads = [
        threading.Thread(target=create_session, args=(f"session-{i}",))
        for i in range(100)
    ]

    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(errors) == 0
    assert len(storage.get_all_session_ids()) == 100
