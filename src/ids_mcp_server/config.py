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


class IDSMCPConfig(BaseModel):
    """Root configuration for IDS MCP Server."""

    server: ServerConfig = Field(default_factory=ServerConfig)
    session: SessionConfig = Field(default_factory=SessionConfig)


def load_config_from_env() -> IDSMCPConfig:
    """
    Load configuration from environment variables.

    Environment Variables:
        IDS_LOG_LEVEL: Logging level (DEBUG, INFO, WARNING, ERROR)
        IDS_MASK_ERRORS: Mask error details (true/false)
        IDS_SESSION_TIMEOUT: Session timeout in seconds
        IDS_CLEANUP_INTERVAL: Cleanup interval in seconds

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

    return IDSMCPConfig(
        server=server_config,
        session=session_config
    )
