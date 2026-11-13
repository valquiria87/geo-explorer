"""
mcp_server/tools/trilha.py
--------------------------
MCP tool: ``get_learning_path``

Wraps :func:`~commands.trilha.find_learning_path` and
:func:`~core.data_loader.load_learning_paths` for MCP clients.
No stdout usage — all logging goes to stderr via the standard ``logging`` module.
"""

from __future__ import annotations

import logging

from mcp.server import MCPServer

from commands.trilha import find_learning_path
from core.data_loader import load_learning_paths
from mcp_server.formatters import format_learning_path

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Pure tool logic — testable without starting a transport
# ---------------------------------------------------------------------------


def get_learning_path_impl(technology: str) -> dict:
    """Return the learning path for *technology* as a JSON-safe dict.

    This function contains all business logic for the tool and can be called
    directly in unit tests without any MCP transport.

    Parameters
    ----------
    technology:
        The technology name (e.g. ``"Python"`` or ``"n8n"``).
        Case-insensitive.  An empty / whitespace-only value returns an error.

    Returns
    -------
    dict
        On success: serialised :class:`~core.models.LearningPath` fields.
        On failure: ``{"error": "<message>"}``
    """
    if not technology or not technology.strip():
        return {"error": "Parameter 'technology' must not be empty."}

    logger.debug("get_learning_path called with technology=%r", technology)

    paths = load_learning_paths()
    path = find_learning_path(technology, paths)

    if path is None:
        return {"error": f"No learning path found for technology: '{technology.strip()}'."}

    return format_learning_path(path)


# ---------------------------------------------------------------------------
# MCP registration
# ---------------------------------------------------------------------------


def register(mcp: MCPServer) -> None:
    """Register ``get_learning_path`` on *mcp*."""

    @mcp.tool()
    def get_learning_path(technology: str) -> dict:
        """Return the structured learning path for a given technology.

        Searches the Geo-Explorer catalogue for a learning path whose
        technology matches *technology* (case-insensitive) and returns all
        of its details: title, level, ordered steps with their competencies,
        and the aggregate list of competencies developed by the full path.

        Returns an ``{"error": "..."}`` dict when no path is found or when
        the input is invalid.
        """
        return get_learning_path_impl(technology)
