"""Main entry point for IDS MCP Server."""

import asyncio
import logging
from ids_mcp_server.server import mcp
from ids_mcp_server.config import load_config_from_env


def setup_logging(log_level: str) -> None:
    """
    Configure logging.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
    """
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def main() -> None:
    """
    Main entry point for IDS MCP Server.

    Behavior:
        1. Load configuration from environment
        2. Initialize logging
        3. Run FastMCP server (blocking)

    Environment Variables:
        - IDS_LOG_LEVEL: Logging level (DEBUG, INFO, WARNING, ERROR)
        - IDS_MASK_ERRORS: Mask error details (true/false)
        - IDS_SESSION_TIMEOUT: Session timeout in seconds
    """
    # Load configuration
    config = load_config_from_env()

    # Setup logging
    setup_logging(config.server.log_level)

    logger = logging.getLogger(__name__)
    logger.info("Starting IDS MCP Server...")
    logger.info(f"Log level: {config.server.log_level}")

    # Run server
    try:
        mcp.run()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {str(e)}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
