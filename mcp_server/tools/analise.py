"""
mcp_server/tools/analise.py
----------------------------
MCP tool: ``analyze_competencies``

Wraps :func:`~core.competency_analyzer.analyze_profile` for MCP clients,
returning a structured list of competency-gap analyses with prioritised
recommendations.
"""

from __future__ import annotations

import logging

from mcp.server import MCPServer

from commands.desafio import load_challenges
from core.competency_analyzer import analyze_profile
from core.data_loader import load_learning_paths
from core.models import LearnerProfile, Level
from mcp_server.formatters import format_competency_analysis

logger = logging.getLogger(__name__)

_VALID_LEVELS = ", ".join(level.value for level in Level)

# Sentinel learner ID used for MCP-originated profiles (stateless per-call).
_MCP_LEARNER_ID = "mcp-learner"


# ---------------------------------------------------------------------------
# Pure tool logic — testable without starting a transport
# ---------------------------------------------------------------------------


def analyze_competencies_impl(
    competencies: list[str],
    level: str,
    goal: str,
    technologies_of_interest: list[str],
) -> dict:
    """Analyse a learner's competency gaps against available learning paths.

    This function contains all business logic for the tool and can be called
    directly in unit tests without any MCP transport.

    Parameters
    ----------
    competencies:
        Competency tags the learner already possesses.
    level:
        Current proficiency level — one of ``"beginner"``, ``"intermediate"``,
        or ``"advanced"``.
    goal:
        Free-text professional goal (may be empty).
    technologies_of_interest:
        Technologies to restrict the analysis to.  Pass an empty list to
        analyse against all available learning paths.

    Returns
    -------
    dict
        On success::

            {
                "analyses": [<CompetencyAnalysis dict>, ...],
                "total": <int>
            }

        When no paths match the requested technologies::

            {
                "analyses": [],
                "total": 0,
                "message": "No learning paths found for the specified technologies."
            }

        On validation failure: ``{"error": "<message>"}``
    """
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
        "analyze_competencies called: level=%r interests=%r",
        level,
        technologies_of_interest,
    )

    profile = LearnerProfile(
        id=_MCP_LEARNER_ID,
        name=None,
        current_competencies=list(competencies),
        current_level=level_enum,
        professional_goal=goal or "",
        technologies_of_interest=list(technologies_of_interest),
        notes="",
    )

    paths = load_learning_paths()
    challenges = load_challenges()
    results = analyze_profile(profile, paths, challenges)

    if not results:
        return {
            "analyses": [],
            "total": 0,
            "message": "No learning paths found for the specified technologies.",
        }

    return {
        "analyses": [format_competency_analysis(a) for a in results],
        "total": len(results),
    }


# ---------------------------------------------------------------------------
# MCP registration
# ---------------------------------------------------------------------------


def register(mcp: MCPServer) -> None:
    """Register ``analyze_competencies`` on *mcp*."""

    @mcp.tool()
    def analyze_competencies(
        competencies: list[str],
        level: str,
        goal: str,
        technologies_of_interest: list[str],
    ) -> dict:
        """Analyse a learner's competency gaps against Geo-Explorer learning paths.

        Compares *competencies* (self-declared) against the competencies required
        by each relevant learning path, and produces a prioritised list of
        recommendations for bridging the gaps.

        *level* must be one of ``"beginner"``, ``"intermediate"``, or
        ``"advanced"``.

        *technologies_of_interest* restricts the analysis to matching paths.
        Pass an empty list to analyse against all available paths.

        Returns ``{"analyses": [...], "total": N}`` on success, or
        ``{"error": "..."}`` on validation failure.
        """
        return analyze_competencies_impl(
            competencies=competencies,
            level=level,
            goal=goal,
            technologies_of_interest=technologies_of_interest,
        )
