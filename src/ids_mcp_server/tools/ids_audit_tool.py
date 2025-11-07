"""Integration module for buildingSMART IDS-Audit-tool."""

import subprocess
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

from ids_mcp_server.config import AuditToolConfig

logger = logging.getLogger(__name__)


def get_audit_tool_path(config: Optional[AuditToolConfig] = None) -> Optional[Path]:
    """
    Get the path to ids-tool.exe.

    Checks config for custom path first, then looks in tools/ids-audit-tool/ directory.

    Args:
        config: Optional AuditToolConfig. If provided and has a custom path, uses that.

    Returns:
        Path to ids-tool.exe if found, None otherwise
    """
    # Check config for custom path first
    if config and config.path:
        custom_path = Path(config.path)
        if custom_path.exists():
            if custom_path.is_file():
                return custom_path
            elif custom_path.is_dir():
                # If it's a directory, look for ids-tool.exe inside
                tool_path = custom_path / "ids-tool.exe"
                if tool_path.exists():
                    return tool_path
        logger.warning(f"IDS-Audit-tool not found at configured path: {config.path}")

    # Default: look in tools/ids-audit-tool/bin/ directory relative to project root
    project_root = Path(__file__).parent.parent.parent.parent
    tool_path = project_root / "tools" / "ids-audit-tool" / "bin" / "ids-tool.exe"

    if tool_path.exists():
        return tool_path

    logger.warning(
        f"IDS-Audit-tool not found at {tool_path}\n"
        f"Expected location: {tool_path}\n"
        f"Download binaries from: https://github.com/buildingSMART/IDS-Audit-tool/releases/download/audit-1.0.0/ids-audit-tool.zip"
    )
    return None


def run_audit_tool(ids_file_path: str, config: Optional[AuditToolConfig] = None) -> Dict[str, Any]:
    """
    Run ids-tool.exe to validate an IDS file.

    Args:
        ids_file_path: Path to the IDS file to validate
        config: Optional AuditToolConfig for custom tool path

    Returns:
        {
            "valid": bool,
            "exit_code": int,
            "output": str,
            "errors": List[str],
            "warnings": List[str]
        }
    """
    tool_path = get_audit_tool_path(config)
    if not tool_path:
        return {
            "valid": False,
            "exit_code": -1,
            "output": "IDS-Audit-tool executable not found",
            "errors": ["IDS-Audit-tool executable not found"],
            "warnings": []
        }

    ids_path = Path(ids_file_path)
    if not ids_path.exists():
        return {
            "valid": False,
            "exit_code": -1,
            "output": f"IDS file not found: {ids_file_path}",
            "errors": [f"IDS file not found: {ids_file_path}"],
            "warnings": []
        }

    try:
        # Run ids-tool.exe with "audit" verb followed by the IDS file path
        result = subprocess.run(
            [str(tool_path), "audit", str(ids_path)],
            capture_output=True,
            text=True,
            timeout=30,  # 30 second timeout
            cwd=str(tool_path.parent)  # Run from tool directory to find DLLs
        )

        output = result.stdout + result.stderr
        exit_code = result.returncode

        # Parse output for errors and warnings
        errors: List[str] = []
        warnings: List[str] = []

        # Exit code 0 typically means success
        # Non-zero means errors or warnings
        if exit_code == 0:
            valid = True
            # Check output for warnings even if exit code is 0
            if "warning" in output.lower():
                warnings.append("Audit tool reported warnings (see output)")
        else:
            valid = False
            # Try to extract error messages from output
            lines = output.split("\n")
            for line in lines:
                line_lower = line.lower()
                if "error" in line_lower or "failed" in line_lower:
                    errors.append(line.strip())
                elif "warning" in line_lower:
                    warnings.append(line.strip())

            # If no specific errors found, use exit code as error
            if not errors:
                errors.append(f"Audit tool exited with code {exit_code}")

        return {
            "valid": valid,
            "exit_code": exit_code,
            "output": output,
            "errors": errors,
            "warnings": warnings
        }

    except subprocess.TimeoutExpired:
        return {
            "valid": False,
            "exit_code": -1,
            "output": "Audit tool execution timed out",
            "errors": ["Audit tool execution timed out after 30 seconds"],
            "warnings": []
        }
    except Exception as e:
        logger.error(f"Error running audit tool: {str(e)}", exc_info=True)
        return {
            "valid": False,
            "exit_code": -1,
            "output": f"Error executing audit tool: {str(e)}",
            "errors": [f"Error executing audit tool: {str(e)}"],
            "warnings": []
        }

