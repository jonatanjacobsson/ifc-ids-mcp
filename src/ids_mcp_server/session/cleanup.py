"""Background cleanup task for abandoned sessions."""

import asyncio
from datetime import datetime, timedelta
from typing import Optional

from ids_mcp_server.session.storage import SessionStorage, get_session_storage


def cleanup_abandoned_sessions(
    storage: Optional[SessionStorage] = None,
    timeout_hours: int = 24
) -> int:
    """
    Remove sessions that haven't been accessed recently.

    Args:
        storage: Session storage (uses global if None)
        timeout_hours: Hours of inactivity before cleanup

    Returns:
        Number of sessions cleaned up
    """
    if storage is None:
        storage = get_session_storage()

    cutoff = datetime.now() - timedelta(hours=timeout_hours)
    cleaned_count = 0

    for session_id in storage.get_all_session_ids():
        session_data = storage.get(session_id)
        if session_data and session_data.metadata.last_accessed < cutoff:
            storage.delete(session_id)
            cleaned_count += 1

    return cleaned_count


async def start_cleanup_task(
    storage: Optional[SessionStorage] = None,
    interval_seconds: int = 3600,
    timeout_hours: int = 24
) -> None:
    """
    Background task to clean up abandoned sessions.

    Args:
        storage: Session storage (uses global if None)
        interval_seconds: How often to run cleanup
        timeout_hours: Hours of inactivity before cleanup
    """
    if storage is None:
        storage = get_session_storage()

    while True:
        await asyncio.sleep(interval_seconds)
        cleaned = cleanup_abandoned_sessions(storage, timeout_hours)
        if cleaned > 0:
            print(f"Cleaned up {cleaned} abandoned session(s)")
