"""Configuration management for IDS MCP Server."""

import os
from typing import Optional
from pydantic import BaseModel, Field


class ServerConfig(BaseModel):
    """FastMCP server configuration."""

    name: str = "IDS MCP Server"
    mask_error_details: bool = False  # True in production
    log_level: str = "INFO"


class SessionConfig(BaseModel):
    """Session management configuration."""

    cleanup_interval: int = 3600  # seconds
    session_timeout: int = 86400  # 24 hours


class AuditToolConfig(BaseModel):
    """IDS-Audit-tool configuration."""

    enabled: bool = True
    path: Optional[str] = None  # Auto-detect if None


class IDSMCPConfig(BaseModel):
    """Root configuration for IDS MCP Server."""

    server: ServerConfig = Field(default_factory=ServerConfig)
    session: SessionConfig = Field(default_factory=SessionConfig)
    audit_tool: AuditToolConfig = Field(default_factory=AuditToolConfig)


def load_config_from_env() -> IDSMCPConfig:
    """
    Load configuration from environment variables.

    Environment Variables:
        IDS_LOG_LEVEL: Logging level (DEBUG, INFO, WARNING, ERROR)
        IDS_MASK_ERRORS: Mask error details (true/false)
        IDS_SESSION_TIMEOUT: Session timeout in seconds
        IDS_CLEANUP_INTERVAL: Cleanup interval in seconds
        IDS_AUDIT_TOOL_ENABLED: Enable IDS-Audit-tool validation (true/false, default: true)
        IDS_AUDIT_TOOL_PATH: Custom path to ids-tool.exe (optional, auto-detect if not set)

    Returns:
        IDSMCPConfig: Configuration object
    """
    server_config = ServerConfig(
        log_level=os.getenv("IDS_LOG_LEVEL", "INFO"),
        mask_error_details=os.getenv("IDS_MASK_ERRORS", "false").lower() == "true"
    )

    session_config = SessionConfig(
        session_timeout=int(os.getenv("IDS_SESSION_TIMEOUT", "86400")),
        cleanup_interval=int(os.getenv("IDS_CLEANUP_INTERVAL", "3600"))
    )

    audit_tool_config = AuditToolConfig(
        enabled=os.getenv("IDS_AUDIT_TOOL_ENABLED", "true").lower() == "true",
        path=os.getenv("IDS_AUDIT_TOOL_PATH", None)
    )

    return IDSMCPConfig(
        server=server_config,
        session=session_config,
        audit_tool=audit_tool_config
    )
