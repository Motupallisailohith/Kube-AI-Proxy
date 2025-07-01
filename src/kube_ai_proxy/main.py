# src/kube_ai_proxy/main.py

"""Main entry point for Kube AI Proxy.

This launches your custom MCP server under your own project namespace.
"""

import logging
import os
import signal
import sys

# Configure root logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)],
)
logger = logging.getLogger("kube-ai-proxy")


def handle_interrupt(signum, frame):
    """Gracefully handle termination signals."""
    logger.info(f"Received signal {signum}, shutting down gracefully...")
    sys.exit(0)


def main():
    """Initialize and start the MCP server."""
    # 1) Bind signals for clean shutdown
    signal.signal(signal.SIGINT, handle_interrupt)
    signal.signal(signal.SIGTERM, handle_interrupt)

    # 2) Verify we can import FastMCP from the 'fastmcp' package
    try:
        from fastmcp import FastMCP
        print(f"✅ Imported FastMCP from: {FastMCP.__module__}", file=sys.stderr)
    except ImportError as e:
        logger.error(f"❌ Unable to import FastMCP: {e}")
        sys.exit(1)

    # 3) Import your configured server instance (built in kube_ai_proxy/mcp/__init__.py)
    from kube_ai_proxy.config import MCP_TRANSPORT
    from kube_ai_proxy.mcp import mcp  # this 'mcp' is your FastMCP() instance

    # 4) Validate transport option
    transport = MCP_TRANSPORT.lower()
    if transport not in ("stdio", "sse"):
        logger.error(
            f"Invalid transport protocol '{transport}' specified. Defaulting to 'stdio'."
        )
        transport = "stdio"

    logger.info(f"Starting Kube AI Proxy MCP server with '{transport}' transport")
    # 5) Run the server (this blocks until shutdown)
    mcp.run(transport=transport)


if __name__ == "__main__":
    main()
