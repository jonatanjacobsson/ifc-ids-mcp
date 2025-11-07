"""RED: Tests for session cleanup."""

import pytest
import asyncio
from datetime import datetime, timedelta
from ids_mcp_server.session.cleanup import cleanup_abandoned_sessions
from ids_mcp_server.session.storage import SessionStorage
from ids_mcp_server.session.models import SessionData


def test_cleanup_old_sessions():
    """Test that old sessions are removed."""
    storage = SessionStorage()

    # Create old session (25 hours old)
    old_session = SessionData(session_id="old-session")
    old_session.metadata.last_accessed = datetime.now() - timedelta(hours=25)
    storage.set("old-session", old_session)

    # Create recent session (1 hour old)
    recent_session = SessionData(session_id="recent-session")
    recent_session.metadata.last_accessed = datetime.now() - timedelta(hours=1)
    storage.set("recent-session", recent_session)

    # Run cleanup (24 hour timeout)
    cleaned = cleanup_abandoned_sessions(storage, timeout_hours=24)

    # Old session removed, recent session kept
    assert storage.get("old-session") is None
    assert storage.get("recent-session") is not None
    assert cleaned == 1


def test_cleanup_no_sessions():
    """Test cleanup with no sessions."""
    storage = SessionStorage()

    cleaned = cleanup_abandoned_sessions(storage, timeout_hours=24)

    assert cleaned == 0


@pytest.mark.asyncio
async def test_cleanup_uses_global_storage():
    """Test that cleanup uses global storage when none provided."""
    from ids_mcp_server.session.storage import get_session_storage
    from ids_mcp_server.session.cleanup import cleanup_abandoned_sessions
    from ids_mcp_server.session.models import SessionData
    from ifctester import ids
    from datetime import datetime, timedelta

    storage = get_session_storage()

    # Add an old session
    session_data = SessionData(session_id="old_session")
    session_data.ids_obj = ids.Ids(title="Test")
    # Manually set old timestamp
    old_time = datetime.now() - timedelta(hours=48)
    session_data.metadata.last_accessed = old_time
    storage.set("old_session", session_data)

    # Call cleanup without providing storage
    cleaned = cleanup_abandoned_sessions()  # No storage param

    assert cleaned == 1


@pytest.mark.asyncio
async def test_start_cleanup_task():
    """Test background cleanup task."""
    from ids_mcp_server.session.cleanup import start_cleanup_task
    from ids_mcp_server.session.storage import get_session_storage
    from ids_mcp_server.session.models import SessionData
    from ifctester import ids
    from datetime import datetime, timedelta

    storage = get_session_storage()

    # Add an old session
    session_data = SessionData(session_id="cleanup_test_session")
    session_data.ids_obj = ids.Ids(title="Test")
    old_time = datetime.now() - timedelta(hours=48)
    session_data.metadata.last_accessed = old_time
    storage.set("cleanup_test_session", session_data)

    # Start cleanup task and run for a short time
    task = asyncio.create_task(start_cleanup_task(storage, interval_seconds=1, timeout_hours=24))

    # Let it run for a bit
    await asyncio.sleep(1.5)

    # Cancel the task
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass

    # Session should have been cleaned up
    assert storage.get("cleanup_test_session") is None


@pytest.mark.asyncio
async def test_start_cleanup_task_without_storage():
    """Test background cleanup task uses global storage."""
    from ids_mcp_server.session.cleanup import start_cleanup_task

    # Start cleanup task without storage param
    task = asyncio.create_task(start_cleanup_task(interval_seconds=1))

    # Let it run briefly
    await asyncio.sleep(0.5)

    # Cancel the task
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass

    # Test passes if no exception
    assert True
