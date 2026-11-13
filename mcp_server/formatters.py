"""
mcp_server/formatters.py
------------------------
Converts domain dataclasses into plain, JSON-serialisable dicts.

No business logic lives here — only structural transformation:
  - ``datetime.date`` → ISO-8601 string
  - ``Level`` enum   → its string value
  - nested dataclasses recursed into plain dicts

Public API
~~~~~~~~~~
- ``format_learning_path(path)``           → dict
- ``format_challenge(challenge)``          → dict
- ``format_competency_analysis(analysis)`` → dict
- ``format_certificate(cert)``             → dict
"""

from __future__ import annotations

from datetime import date
from typing import Any

from core.models import (
    Challenge,
    CompetencyAnalysis,
    LearningPath,
    LearningStep,
    Recommendation,
)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _level_str(level: Any) -> str:
    """Return the string value of a Level enum (or pass through a plain string)."""
    return level.value if hasattr(level, "value") else str(level)


def _date_str(d: Any) -> str | None:
    """Return an ISO-8601 date string, or None when the value is None."""
    if d is None:
        return None
    if isinstance(d, date):
        return d.isoformat()
    return str(d)


def _format_step(step: Any) -> dict:
    return {
        "order": step.order,
        "title": step.title,
        "description": step.description,
        "competencies_developed": list(step.competencies_developed),
    }


def _format_recommendation(rec: Recommendation) -> dict:
    return {
        "id": rec.id,
        "learner_id": rec.learner_id,
        "recommendation_type": rec.recommendation_type.value,
        "target_id": rec.target_id,
        "rationale": rec.rationale,
        "competencies_to_develop": list(rec.competencies_to_develop),
        "priority": rec.priority,
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def format_learning_path(path: LearningPath) -> dict:
    """Serialise a :class:`~core.models.LearningPath` to a JSON-safe dict.

    Parameters
    ----------
    path:
        The learning path to serialise.

    Returns
    -------
    dict
        Keys: id, title, technology, level, description, steps, competencies.
    """
    return {
        "id": path.id,
        "title": path.title,
        "technology": path.technology,
        "level": _level_str(path.level),
        "description": path.description,
        "steps": [_format_step(s) for s in sorted(path.steps, key=lambda s: s.order)],
        "competencies": list(path.competencies),
    }


def format_challenge(challenge: Challenge) -> dict:
    """Serialise a :class:`~core.models.Challenge` to a JSON-safe dict.

    Parameters
    ----------
    challenge:
        The challenge to serialise.

    Returns
    -------
    dict
        Keys: id, title, technology, level, description,
              evaluation_criteria, competencies_assessed, estimated_hours.
    """
    return {
        "id": challenge.id,
        "title": challenge.title,
        "technology": challenge.technology,
        "level": _level_str(challenge.level),
        "description": challenge.description,
        "evaluation_criteria": list(challenge.evaluation_criteria),
        "competencies_assessed": list(challenge.competencies_assessed),
        "estimated_hours": challenge.estimated_hours,
    }


def format_competency_analysis(analysis: CompetencyAnalysis) -> dict:
    """Serialise a :class:`~core.models.CompetencyAnalysis` to a JSON-safe dict.

    Parameters
    ----------
    analysis:
        The analysis result to serialise.

    Returns
    -------
    dict
        Keys: path (nested dict), coverage_index, matched_competencies,
              missing_competencies, extra_competencies, recommendations.
    """
    return {
        "path": format_learning_path(analysis.path),
        "coverage_index": analysis.coverage_index,
        "matched_competencies": list(analysis.matched_competencies),
        "missing_competencies": list(analysis.missing_competencies),
        "extra_competencies": list(analysis.extra_competencies),
        "recommendations": [_format_recommendation(r) for r in analysis.recommendations],
    }


def format_certificate(cert: dict) -> dict:
    """Serialise a certificate dict (from ``build_certificate``) to a JSON-safe dict.

    The only transformation needed is converting ``issued_on`` (a ``datetime.date``
    object) to an ISO-8601 string.

    Parameters
    ----------
    cert:
        A dict as returned by :func:`~commands.certificado.build_certificate`.

    Returns
    -------
    dict
        Same structure as input, with ``issued_on`` replaced by its ISO-8601 string.
    """
    result = dict(cert)
    result["issued_on"] = _date_str(cert.get("issued_on"))
    return result
