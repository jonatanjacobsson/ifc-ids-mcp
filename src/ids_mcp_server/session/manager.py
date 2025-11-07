"""Session lifecycle management with FastMCP Context integration."""

import os
from pathlib import Path
from typing import Optional
from fastmcp import Context
from ifctester import ids

from ids_mcp_server.session.storage import get_session_storage
from ids_mcp_server.session.models import SessionData


async def get_or_create_session(ctx: Context) -> ids.Ids:
    """
    Get existing IDS for session or create new one.

    Args:
        ctx: FastMCP Context with session_id

    Returns:
        IDS object for this session
    """
    storage = get_session_storage()
    session_id = ctx.session_id

    session_data = storage.get(session_id)

    if session_data is None:
        # Create new session
        await ctx.info(f"Creating new IDS session: {session_id}")
        session_data = SessionData(session_id=session_id)
        session_data.ids_obj = ids.Ids(title="Untitled IDS")
        storage.set(session_id, session_data)
    else:
        await ctx.debug(f"Retrieved existing session: {session_id}")
        session_data.update_last_accessed()

    return session_data.ids_obj


async def create_session_from_file(ctx: Context, filepath: str) -> ids.Ids:
    """
    Load IDS from file and store in session.

    Args:
        ctx: FastMCP Context
        filepath: Path to IDS XML file

    Returns:
        Loaded IDS object

    Raises:
        FileNotFoundError: If file doesn't exist
        Exception: If file cannot be parsed
    """
    storage = get_session_storage()
    session_id = ctx.session_id

    # Validate file exists
    if not Path(filepath).exists():
        raise FileNotFoundError(f"IDS file not found: {filepath}")

    await ctx.info(f"Loading IDS from {filepath}")

    # Load using IfcTester
    ids_obj = ids.open(filepath)

    # Store in session
    session_data = SessionData(session_id=session_id)
    session_data.ids_obj = ids_obj
    if ids_obj.info.get("title"):
        session_data.set_ids_title(ids_obj.info["title"])

    storage.set(session_id, session_data)

    await ctx.info(f"IDS loaded successfully: {ids_obj.info.get('title', 'Untitled')}")

    return ids_obj


async def create_session_from_string(ctx: Context, xml_string: str) -> ids.Ids:
    """
    Load IDS from XML string and store in session.

    Args:
        ctx: FastMCP Context
        xml_string: IDS XML content

    Returns:
        Loaded IDS object

    Raises:
        Exception: If XML cannot be parsed
    """
    storage = get_session_storage()
    session_id = ctx.session_id

    await ctx.info("Loading IDS from XML string")

    # Load using IfcTester
    ids_obj = ids.from_string(xml_string)

    # Store in session
    session_data = SessionData(session_id=session_id)
    session_data.ids_obj = ids_obj
    if ids_obj.info.get("title"):
        session_data.set_ids_title(ids_obj.info["title"])

    storage.set(session_id, session_data)

    await ctx.info(f"IDS loaded from string: {ids_obj.info.get('title', 'Untitled')}")

    return ids_obj


def cleanup_session(session_id: str) -> None:
    """
    Remove session data.

    Args:
        session_id: Session to remove
    """
    storage = get_session_storage()
    storage.delete(session_id)
