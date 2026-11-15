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
from core.data_loader import load_learning_paths
from core.models import LearningPath, Level
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
    competencies: list[str] | None = None,
    paths: list[LearningPath] | None = None,
) -> dict:
    """Build a fictional trail-and-competency record and return it as a JSON-safe dict.

    This function contains all business logic for the tool and can be called
    directly in unit tests without any MCP transport.

    Parameters
    ----------
    participant:
        Full name of the learner.  Must not be empty.
    activity:
        Title or ID of a learning trail from the catalog (challenges are not
        accepted).  Must not be empty.
    technology:
        Primary technology covered (e.g. ``"Python"``).
    level:
        Proficiency level string — one of ``"beginner"``, ``"intermediate"``,
        or ``"advanced"``.
    competencies:
        Optional.  Competency tags associated with the trail (self-declared and
        not verified).  When omitted
        (``None``), empty, or made only of blank strings, the competencies of the
        matched learning trail are used.  Custom tags are stripped and blank
        items are dropped.
    paths:
        Optional list of LearningPath instances; loads from catalog file if None.

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

    if paths is None:
        try:
            paths = load_learning_paths()
        except Exception as exc:
            return {"error": f"Failed to load learning paths catalog: {exc}"}

    try:
        cert = build_certificate(
            participant=participant,
            activity=activity,
            technology=technology,
            level=level_stripped,
            competencies=competencies,
            paths=paths,
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
        competencies: list[str] | None = None,
    ) -> dict:
        """Generate a fictional (non-official) record based on a learning trail
        selected from the Geo-Explorer catalog.

        The record contains self-declared information: *activity* must be the
        title or ID of a catalog trail (challenges are not accepted) and the
        competencies are only associated with that trail.  The tool does not
        track progress and does not verify completion of trails or challenges.
        The record is explicitly labelled as fictional and carries no
        professional credential value.

        *level* must be one of ``"beginner"``, ``"intermediate"``, or
        ``"advanced"``.  *competencies* is optional: omit it, or send an empty
        list, to use the competencies of the selected learning trail.  Custom
        entries are stripped and blank entries are ignored.

        Returns an ``{"error": "..."}`` dict when validation fails.
        """
        return generate_certificate_impl(
            participant=participant,
            activity=activity,
            technology=technology,
            level=level,
            competencies=competencies,
        )
