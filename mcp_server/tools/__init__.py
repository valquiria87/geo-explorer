"""
mcp_server/tools/__init__.py
-----------------------------
Registers all four MCP tools on a given :class:`~mcp.server.MCPServer` instance.

Usage::

    from mcp.server import MCPServer
    from mcp_server.tools import register_all_tools

    mcp = MCPServer("geo-explorer")
    register_all_tools(mcp)
"""

from __future__ import annotations

from mcp.server import MCPServer

from mcp_server.tools import analise, certificado, desafio, trilha


def register_all_tools(mcp: MCPServer) -> None:
    """Register every Geo-Explorer tool on *mcp*.

    Delegates to each sub-module's ``register`` function, which attaches
    its tool via ``@mcp.tool()``.  Call this once before running the server.

    Parameters
    ----------
    mcp:
        The :class:`~mcp.server.MCPServer` instance to register tools on.
    """
    trilha.register(mcp)
    desafio.register(mcp)
    certificado.register(mcp)
    analise.register(mcp)
