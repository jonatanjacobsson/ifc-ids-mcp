"""IDS MCP Server - AI-powered IDS file creation using IfcTester."""

__version__ = "0.1.0"
__author__ = "Quasar Consulting Group"
__description__ = "MCP server for creating buildingSMART IDS files with 100% compliance"

from ids_mcp_server.server import mcp

__all__ = ["mcp", "__version__"]
