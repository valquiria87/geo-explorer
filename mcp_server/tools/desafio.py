"""
mcp_server/tools/desafio.py
---------------------------
MCP tool: ``get_challenge``

Wraps :func:`~commands.desafio.load_challenges`,
:func:`~commands.desafio.filter_challenges`, and a random selection, mirroring
the CLI behaviour without writing to stdout.
"""

from __future__ import annotations

import logging
import random

from mcp.server import MCPServer

from commands.desafio import filter_challenges, load_challenges
from core.models import Level
from mcp_server.formatters import format_challenge

logger = logging.getLogger(__name__)

_VALID_LEVELS = ", ".join(level.value for level in Level)


# ---------------------------------------------------------------------------
# Pure tool logic — testable without starting a transport
# ---------------------------------------------------------------------------


def get_challenge_impl(technology: str, level: str) -> dict:
    """Return a randomly selected challenge for *technology* and *level*.

    This function contains all business logic for the tool and can be called
    directly in unit tests without any MCP transport.

    Parameters
    ----------
    technology:
        Technology name (e.g. ``"Python"``).  Case-insensitive.
    level:
        Difficulty level string — must be one of ``"beginner"``,
        ``"intermediate"``, or ``"advanced"``.

    Returns
    -------
    dict
        On success: serialised :class:`~core.models.Challenge` fields.
        On failure: ``{"error": "<message>"}``
    """
    if not technology or not technology.strip():
        return {"error": "Parameter 'technology' must not be empty."}

    level_stripped = level.strip().lower() if level else ""
    try:
        level_enum = Level(level_stripped)
    except ValueError:
        return {
            "error": (
                f"Invalid level '{level}'. "
                f"Valid values: {_VALID_LEVELS}."
            )
        }

    logger.debug(
        "get_challenge called with technology=%r level=%r", technology, level
    )

    challenges = load_challenges()
    matches = filter_challenges(technology, level_enum, challenges)

    if not matches:
        return {
            "error": (
                f"No challenge found for technology '{technology.strip()}' "
                f"at level '{level_enum.value}'."
            )
        }

    chosen = random.choice(matches)
    return format_challenge(chosen)


# ---------------------------------------------------------------------------
# MCP registration
# ---------------------------------------------------------------------------


def register(mcp: MCPServer) -> None:
    """Register ``get_challenge`` on *mcp*."""

    @mcp.tool()
    def get_challenge(technology: str, level: str) -> dict:
        """Return a randomly selected practical challenge for a technology and level.

        Searches the Geo-Explorer challenge catalogue for entries that match
        *technology* (case-insensitive) and *level*, then picks one at random.

        *level* must be one of ``"beginner"``, ``"intermediate"``, or
        ``"advanced"``.

        Returns an ``{"error": "..."}`` dict when no challenge matches or when
        the input is invalid.
        """
        return get_challenge_impl(technology, level)
