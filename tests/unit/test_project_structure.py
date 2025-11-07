"""RED: Tests for project structure and imports."""

import pytest


def test_package_importable():
    """Test that ids_mcp_server package can be imported."""
    import ids_mcp_server
    assert ids_mcp_server is not None


def test_version_defined():
    """Test that version is defined."""
    from ids_mcp_server import __version__
    assert __version__ is not None
    assert isinstance(__version__, str)
    assert __version__ == "0.1.0"


def test_config_importable():
    """Test that config module can be imported."""
    from ids_mcp_server import config
    assert config is not None


def test_session_importable():
    """Test that session module can be imported."""
    from ids_mcp_server import session
    assert session is not None
