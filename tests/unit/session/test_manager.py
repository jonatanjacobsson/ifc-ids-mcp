"""RED: Tests for session manager."""

import pytest
from ids_mcp_server.session.manager import (
    get_or_create_session,
    create_session_from_string
)
from ifctester import ids


@pytest.mark.asyncio
async def test_get_or_create_session_new(mock_context):
    """Test creating new session via Context."""
    ids_obj = await get_or_create_session(mock_context)

    assert ids_obj is not None
    assert isinstance(ids_obj, ids.Ids)


@pytest.mark.asyncio
async def test_get_or_create_session_existing(mock_context):
    """Test retrieving existing session."""
    # First call creates
    ids_obj1 = await get_or_create_session(mock_context)
    ids_obj1.info["title"] = "Test IDS"

    # Second call retrieves same object
    ids_obj2 = await get_or_create_session(mock_context)

    assert ids_obj2.info["title"] == "Test IDS"
    assert ids_obj1 is ids_obj2  # Same object reference


@pytest.mark.asyncio
async def test_create_session_from_string(mock_context, sample_ids_xml):
    """Test loading IDS from XML string."""
    ids_obj = await create_session_from_string(mock_context, sample_ids_xml)

    assert ids_obj.info["title"] == "Test IDS"

    # Verify it's stored in session
    ids_obj2 = await get_or_create_session(mock_context)
    assert ids_obj2.info["title"] == "Test IDS"
