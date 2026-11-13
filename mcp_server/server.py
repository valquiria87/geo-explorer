"""
mcp_server/server.py
--------------------
Entry point for the Geo-Explorer MCP server.

Usage
-----
Run over stdio (for MCP clients such as Claude Desktop or VS Code)::

    python -m mcp_server.server

Public API
~~~~~~~~~~
- ``create_server()`` — build and return a configured :class:`~mcp.server.MCPServer`.
  Use this in tests to obtain an in-process server without starting stdio.
- ``main()`` — call ``create_server()`` then ``mcp.run()``.

stdout is reserved exclusively for the MCP JSON-RPC protocol.
All diagnostic output is sent to stderr via the standard ``logging`` module,
which the SDK's ``configure_logging()`` (called inside ``MCPServer.__init__``)
routes to stderr automatically.
"""

from __future__ import annotations

import logging

from mcp.server import MCPServer

from mcp_server.tools import register_all_tools

logger = logging.getLogger(__name__)

_SERVER_NAME = "geo-explorer"
_SERVER_VERSION = "1.0.0"


def create_server() -> MCPServer:
    """Build and return a fully configured Geo-Explorer :class:`~mcp.server.MCPServer`.

    All four tools are registered before the instance is returned.
    The server is **not** started — no transport is opened.  Use this
    function to obtain an in-process server in tests::

        from mcp import Client
        from mcp_server.server import create_server

        async def test_something():
            async with Client(create_server()) as client:
                result = await client.list_tools()

    Returns
    -------
    MCPServer
        A configured server instance ready to be run or tested.
    """
    mcp = MCPServer(
        name=_SERVER_NAME,
        version=_SERVER_VERSION,
    )
    register_all_tools(mcp)
    logger.debug("Geo-Explorer MCP server created with %d tools", 4)
    return mcp


def main() -> None:
    """Start the Geo-Explorer MCP server over stdio.

    Blocks until the client disconnects.  Intended as the process entry point;
    never call this from tests.
    """
    mcp = create_server()
    logger.info("Starting Geo-Explorer MCP server (stdio transport)")
    mcp.run()  # transport="stdio" by default


if __name__ == "__main__":
    main()
