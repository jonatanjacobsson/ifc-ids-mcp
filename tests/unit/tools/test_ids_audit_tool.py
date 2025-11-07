"""Tests for IDS-Audit-tool integration."""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from ids_mcp_server.tools.ids_audit_tool import get_audit_tool_path, run_audit_tool
from ids_mcp_server.config import AuditToolConfig


@patch("ids_mcp_server.tools.ids_audit_tool.Path")
def test_get_audit_tool_path_exists(mock_path_class, tmp_path):
    """Test getting audit tool path when it exists in bin/ directory."""
    # Create mock tool directory structure with bin/ subdirectory
    tools_dir = tmp_path / "tools" / "ids-audit-tool" / "bin"
    tools_dir.mkdir(parents=True)
    tool_exe = tools_dir / "ids-tool.exe"
    tool_exe.write_text("mock exe")

    # Mock __file__ path resolution
    mock_file_path = MagicMock()
    mock_file_path.parent.parent.parent.parent = tmp_path
    mock_path_class.return_value = mock_file_path

    result = get_audit_tool_path()

    assert result == tool_exe


@patch("ids_mcp_server.tools.ids_audit_tool.Path")
def test_get_audit_tool_path_not_found(mock_path_class, tmp_path):
    """Test getting audit tool path when it doesn't exist."""
    # Mock __file__ path resolution
    mock_file_path = MagicMock()
    mock_file_path.parent.parent.parent.parent = tmp_path
    mock_path_class.return_value = mock_file_path

    result = get_audit_tool_path()

    assert result is None


@patch("ids_mcp_server.tools.ids_audit_tool.get_audit_tool_path")
@patch("ids_mcp_server.tools.ids_audit_tool.subprocess.run")
def test_run_audit_tool_success(mock_subprocess, mock_get_path, tmp_path):
    """Test running audit tool successfully."""
    tool_path = tmp_path / "ids-tool.exe"
    tool_path.write_text("mock")
    mock_get_path.return_value = tool_path

    ids_file = tmp_path / "test.ids"
    ids_file.write_text("<?xml version='1.0'?><ids></ids>")

    # Mock successful subprocess run
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "Validation successful"
    mock_result.stderr = ""
    mock_subprocess.return_value = mock_result

    result = run_audit_tool(str(ids_file))

    assert result["valid"] is True
    assert result["exit_code"] == 0
    assert "Validation successful" in result["output"]
    assert result["errors"] == []
    mock_subprocess.assert_called_once()


@patch("ids_mcp_server.tools.ids_audit_tool.get_audit_tool_path")
@patch("ids_mcp_server.tools.ids_audit_tool.subprocess.run")
def test_run_audit_tool_with_errors(mock_subprocess, mock_get_path, tmp_path):
    """Test running audit tool with errors."""
    tool_path = tmp_path / "ids-tool.exe"
    tool_path.write_text("mock")
    mock_get_path.return_value = tool_path

    ids_file = tmp_path / "test.ids"
    ids_file.write_text("<?xml version='1.0'?><ids></ids>")

    # Mock failed subprocess run
    mock_result = MagicMock()
    mock_result.returncode = 1
    mock_result.stdout = ""
    mock_result.stderr = "Error: Invalid IDS structure"
    mock_subprocess.return_value = mock_result

    result = run_audit_tool(str(ids_file))

    assert result["valid"] is False
    assert result["exit_code"] == 1
    assert len(result["errors"]) > 0


@patch("ids_mcp_server.tools.ids_audit_tool.get_audit_tool_path")
def test_run_audit_tool_tool_not_found(mock_get_path):
    """Test running audit tool when tool is not found."""
    mock_get_path.return_value = None

    result = run_audit_tool("test.ids")

    assert result["valid"] is False
    assert result["exit_code"] == -1
    assert "not found" in result["errors"][0].lower()


@patch("ids_mcp_server.tools.ids_audit_tool.get_audit_tool_path")
def test_run_audit_tool_file_not_found(mock_get_path, tmp_path):
    """Test running audit tool when IDS file doesn't exist."""
    tool_path = tmp_path / "ids-tool.exe"
    tool_path.write_text("mock")
    mock_get_path.return_value = tool_path

    result = run_audit_tool("nonexistent.ids")

    assert result["valid"] is False
    assert result["exit_code"] == -1
    assert "not found" in result["errors"][0].lower()


@patch("ids_mcp_server.tools.ids_audit_tool.get_audit_tool_path")
@patch("ids_mcp_server.tools.ids_audit_tool.subprocess.run")
def test_run_audit_tool_timeout(mock_subprocess, mock_get_path, tmp_path):
    """Test running audit tool with timeout."""
    import subprocess

    tool_path = tmp_path / "ids-tool.exe"
    tool_path.write_text("mock")
    mock_get_path.return_value = tool_path

    ids_file = tmp_path / "test.ids"
    ids_file.write_text("<?xml version='1.0'?><ids></ids>")

    # Mock timeout exception
    mock_subprocess.side_effect = subprocess.TimeoutExpired("ids-tool.exe", 30)

    result = run_audit_tool(str(ids_file))

    assert result["valid"] is False
    assert result["exit_code"] == -1
    assert "timed out" in result["errors"][0].lower()


@patch("ids_mcp_server.tools.ids_audit_tool.get_audit_tool_path")
@patch("ids_mcp_server.tools.ids_audit_tool.subprocess.run")
def test_run_audit_tool_exception(mock_subprocess, mock_get_path, tmp_path):
    """Test running audit tool with exception."""
    tool_path = tmp_path / "ids-tool.exe"
    tool_path.write_text("mock")
    mock_get_path.return_value = tool_path

    ids_file = tmp_path / "test.ids"
    ids_file.write_text("<?xml version='1.0'?><ids></ids>")

    # Mock exception
    mock_subprocess.side_effect = Exception("Unexpected error")

    result = run_audit_tool(str(ids_file))

    assert result["valid"] is False
    assert result["exit_code"] == -1
    assert "Error executing" in result["errors"][0]


def test_get_audit_tool_path_with_custom_file_path(tmp_path):
    """Test getting audit tool path with custom file path in config."""
    custom_tool = tmp_path / "custom-ids-tool.exe"
    custom_tool.write_text("mock")

    config = AuditToolConfig(path=str(custom_tool))
    result = get_audit_tool_path(config)

    assert result == custom_tool


def test_get_audit_tool_path_with_custom_dir_path(tmp_path):
    """Test getting audit tool path with custom directory path in config."""
    custom_dir = tmp_path / "custom-tool-dir"
    custom_dir.mkdir()
    custom_tool = custom_dir / "ids-tool.exe"
    custom_tool.write_text("mock")

    config = AuditToolConfig(path=str(custom_dir))
    result = get_audit_tool_path(config)

    assert result == custom_tool


@patch("ids_mcp_server.tools.ids_audit_tool.get_audit_tool_path")
@patch("ids_mcp_server.tools.ids_audit_tool.subprocess.run")
def test_run_audit_tool_with_config(mock_subprocess, mock_get_path, tmp_path):
    """Test running audit tool with config parameter."""
    tool_path = tmp_path / "ids-tool.exe"
    tool_path.write_text("mock")
    mock_get_path.return_value = tool_path

    ids_file = tmp_path / "test.ids"
    ids_file.write_text("<?xml version='1.0'?><ids></ids>")

    config = AuditToolConfig(enabled=True, path=str(tmp_path))

    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "Success"
    mock_result.stderr = ""
    mock_subprocess.return_value = mock_result

    result = run_audit_tool(str(ids_file), config)

    assert result["valid"] is True
    # Verify config was passed to get_audit_tool_path
    mock_get_path.assert_called_once_with(config)

