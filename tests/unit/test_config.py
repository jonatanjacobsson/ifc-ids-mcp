"""RED: Tests for configuration management."""

import pytest
import os


def test_default_config_creation(mcp_config):
    """Test creating default configuration."""
    from ids_mcp_server.config import IDSMCPConfig

    config = IDSMCPConfig()

    assert config.server.name == "IDS MCP Server"
    assert config.server.log_level == "INFO"
    assert config.server.mask_error_details is False
    assert config.session.cleanup_interval == 3600
    assert config.session.session_timeout == 86400


def test_config_from_env(monkeypatch):
    """Test loading config from environment."""
    from ids_mcp_server.config import load_config_from_env

    monkeypatch.setenv("IDS_LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("IDS_MASK_ERRORS", "true")
    monkeypatch.setenv("IDS_SESSION_TIMEOUT", "7200")
    monkeypatch.setenv("IDS_CLEANUP_INTERVAL", "1800")

    config = load_config_from_env()

    assert config.server.log_level == "DEBUG"
    assert config.server.mask_error_details is True
    assert config.session.session_timeout == 7200
    assert config.session.cleanup_interval == 1800
