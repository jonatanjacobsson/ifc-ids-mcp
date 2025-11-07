"""Pytest configuration and shared fixtures."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from pathlib import Path

from ids_mcp_server.config import IDSMCPConfig
from ids_mcp_server.session.storage import get_session_storage


@pytest.fixture
def mcp_config():
    """Provide test configuration."""
    return IDSMCPConfig()


@pytest.fixture
def mock_context():
    """Provide mock FastMCP Context."""
    ctx = MagicMock()
    ctx.session_id = "test-session-123"
    ctx.info = AsyncMock()
    ctx.debug = AsyncMock()
    ctx.warning = AsyncMock()
    ctx.error = AsyncMock()
    ctx.report_progress = AsyncMock()
    return ctx


@pytest.fixture
def sample_ids_xml():
    """Provide sample IDS XML with valid specification."""
    return """<?xml version="1.0" encoding="UTF-8"?>
<ids:ids xmlns:ids="http://standards.buildingsmart.org/IDS"
         xmlns:xs="http://www.w3.org/2001/XMLSchema"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://standards.buildingsmart.org/IDS http://standards.buildingsmart.org/IDS/1.0/ids.xsd">
    <ids:info>
        <ids:title>Test IDS</ids:title>
    </ids:info>
    <ids:specifications>
        <ids:specification name="Test Specification" ifcVersion="IFC4">
            <ids:applicability>
                <ids:entity>
                    <ids:name>
                        <ids:simpleValue>IFCWALL</ids:simpleValue>
                    </ids:name>
                </ids:entity>
            </ids:applicability>
        </ids:specification>
    </ids:specifications>
</ids:ids>"""


@pytest.fixture(autouse=True)
def cleanup_sessions():
    """Clean up sessions after each test."""
    yield
    # Cleanup code
    storage = get_session_storage()
    storage.clear()


@pytest.fixture
def temp_ids_file(tmp_path, sample_ids_xml):
    """Create temporary IDS file for testing."""
    ids_file = tmp_path / "test.ids"
    ids_file.write_text(sample_ids_xml)
    return ids_file
