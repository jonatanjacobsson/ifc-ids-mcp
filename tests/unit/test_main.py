"""Tests for __main__ entry point."""

import pytest
from unittest.mock import patch, MagicMock


def test_setup_logging():
    """Test logging setup."""
    import logging
    from ids_mcp_server.__main__ import setup_logging

    # Test INFO level - just verify it runs without error
    setup_logging("INFO")
    # Can't reliably check level due to pytest's own logging setup


@patch('ids_mcp_server.__main__.mcp')
@patch('ids_mcp_server.__main__.load_config_from_env')
def test_main_successful_run(mock_config, mock_mcp):
    """Test main function with successful server run."""
    from ids_mcp_server.__main__ import main
    from ids_mcp_server.config import ServerConfig, SessionConfig, IDSMCPConfig

    # Mock configuration
    mock_config.return_value = IDSMCPConfig(
        server=ServerConfig(log_level="INFO", mask_error_details=False),
        session=SessionConfig(session_timeout=86400, cleanup_interval=3600)
    )

    # Mock mcp.run() to not block
    mock_mcp.run = MagicMock()

    # Run main
    main()

    # Verify config was loaded
    mock_config.assert_called_once()

    # Verify server was started
    mock_mcp.run.assert_called_once()


@patch('ids_mcp_server.__main__.mcp')
@patch('ids_mcp_server.__main__.load_config_from_env')
def test_main_keyboard_interrupt(mock_config, mock_mcp):
    """Test main function handles KeyboardInterrupt."""
    from ids_mcp_server.__main__ import main
    from ids_mcp_server.config import ServerConfig, SessionConfig, IDSMCPConfig

    # Mock configuration
    mock_config.return_value = IDSMCPConfig(
        server=ServerConfig(log_level="INFO", mask_error_details=False),
        session=SessionConfig(session_timeout=86400, cleanup_interval=3600)
    )

    # Mock mcp.run() to raise KeyboardInterrupt
    mock_mcp.run = MagicMock(side_effect=KeyboardInterrupt())

    # Run main - should not raise
    main()

    # Verify server was called
    mock_mcp.run.assert_called_once()


@patch('ids_mcp_server.__main__.mcp')
@patch('ids_mcp_server.__main__.load_config_from_env')
def test_main_with_exception(mock_config, mock_mcp):
    """Test main function handles exceptions."""
    from ids_mcp_server.__main__ import main
    from ids_mcp_server.config import ServerConfig, SessionConfig, IDSMCPConfig

    # Mock configuration
    mock_config.return_value = IDSMCPConfig(
        server=ServerConfig(log_level="INFO", mask_error_details=False),
        session=SessionConfig(session_timeout=86400, cleanup_interval=3600)
    )

    # Mock mcp.run() to raise exception
    mock_mcp.run = MagicMock(side_effect=RuntimeError("Test error"))

    # Run main - should raise
    with pytest.raises(RuntimeError, match="Test error"):
        main()

    # Verify server was called
    mock_mcp.run.assert_called_once()
