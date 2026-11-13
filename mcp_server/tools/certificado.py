"""
mcp_server/tools/certificado.py
--------------------------------
MCP tool: ``generate_certificate``

Wraps :func:`~commands.certificado.build_certificate`, returning the
certificate as a JSON-safe dict.  The presentation function
``display_certificate`` is intentionally *not* called here — stdout must
remain reserved for the MCP protocol.
"""

from __future__ import annotations

import logging

from mcp.server import MCPServer

from commands.certificado import build_certificate
from core.models import Level
from mcp_server.formatters import format_certificate

logger = logging.getLogger(__name__)

_VALID_LEVELS = ", ".join(level.value for level in Level)


# ---------------------------------------------------------------------------
# Pure tool logic — testable without starting a transport
# ---------------------------------------------------------------------------


def generate_certificate_impl(
    participant: str,
    activity: str,
    technology: str,
    level: str,
    competencies: list[str],
) -> dict:
    """Build a fictional completion certificate and return it as a JSON-safe dict.

    This function contains all business logic for the tool and can be called
    directly in unit tests without any MCP transport.

    Parameters
    ----------
    participant:
        Full name of the learner.  Must not be empty.
    activity:
        Name of the completed learning trail or challenge.  Must not be empty.
    technology:
        Primary technology covered (e.g. ``"Python"``).
    level:
        Proficiency level string — one of ``"beginner"``, ``"intermediate"``,
        or ``"advanced"``.
    competencies:
        List of competency tags developed during the activity.

    Returns
    -------
    dict
        On success: certificate fields including ``issued_on`` as ISO-8601 string.
        On failure: ``{"error": "<message>"}``
    """
    if not participant or not participant.strip():
        return {"error": "Participant name must not be empty."}

    if not activity or not activity.strip():
        return {"error": "Activity name must not be empty."}

    level_stripped = level.strip().lower() if level else ""
    try:
        Level(level_stripped)
    except ValueError:
        return {
            "error": (
                f"Invalid level '{level}'. "
                f"Valid values: {_VALID_LEVELS}."
            )
        }

    logger.debug(
        "generate_certificate called for participant=%r activity=%r",
        participant,
        activity,
    )

    try:
        cert = build_certificate(
            participant=participant,
            activity=activity,
            technology=technology,
            level=level_stripped,
            competencies=competencies,
        )
    except ValueError as exc:
        return {"error": str(exc)}

    return format_certificate(cert)


# ---------------------------------------------------------------------------
# MCP registration
# ---------------------------------------------------------------------------


def register(mcp: MCPServer) -> None:
    """Register ``generate_certificate`` on *mcp*."""

    @mcp.tool()
    def generate_certificate(
        participant: str,
        activity: str,
        technology: str,
        level: str,
        competencies: list[str],
    ) -> dict:
        """Generate a fictional (non-official) completion certificate.

        Creates a Geo-Explorer certificate record for a learner who completed a
        learning trail or challenge.  The certificate is explicitly labelled as
        fictional and carries no professional credential value.

        *level* must be one of ``"beginner"``, ``"intermediate"``, or
        ``"advanced"``.  *competencies* may be an empty list.

        Returns an ``{"error": "..."}`` dict when validation fails.
        """
        return generate_certificate_impl(
            participant=participant,
            activity=activity,
            technology=technology,
            level=level,
            competencies=competencies,
        )
