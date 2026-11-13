"""
core/models.py
--------------
Fundamental domain models for Geo-Explorer — Intelligent Career Navigator.

All models are plain Python dataclasses: no external dependencies, no I/O,
no business logic. They describe the core concepts of the learning-and-growth
domain and serve as the shared vocabulary for every other module.

Domain concepts
~~~~~~~~~~~~~~~
- LearningPath        : a structured, technology-focused learning track with
                        ordered steps and the competencies each step develops.
- LearnerProfile      : a snapshot of a learner — what they know today, their
                        current level, and where they want to go professionally.
- Challenge           : a concrete, hands-on task tied to a technology and a
                        level, with explicit acceptance criteria so progress is
                        measurable.
- Recommendation      : a next-step suggestion derived from a learner's profile
                        and the gaps between their current and target
                        competencies.
- CompetencyAnalysis  : the result of comparing a learner's declared
                        competencies against those required by a single
                        LearningPath.  Pure data — no business logic.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


# ---------------------------------------------------------------------------
# Shared enumerations
# ---------------------------------------------------------------------------


class Level(str, Enum):
    """Proficiency / difficulty level, applicable to paths, learners and challenges."""

    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class RecommendationType(str, Enum):
    """Classifies what kind of next step is being recommended."""

    LEARNING_PATH = "learning_path"   # Follow a structured learning track
    CHALLENGE = "challenge"           # Tackle a practical, hands-on challenge
    COMPETENCY_REVIEW = "competency_review"  # Revisit and consolidate an existing skill


# ---------------------------------------------------------------------------
# LearningPath
# ---------------------------------------------------------------------------


@dataclass
class LearningStep:
    """
    A single step inside a :class:`LearningPath`.

    Attributes
    ----------
    title:
        Short name for this step (e.g. "Variables and Types").
    description:
        Narrative explanation of what the learner will do or study.
    competencies_developed:
        List of skill/competency tags that this step builds
        (e.g. ``["type annotations", "control flow"]``).
    order:
        1-based position of this step within its parent path.
    """

    title: str
    description: str
    competencies_developed: list[str]
    order: int


@dataclass
class LearningPath:
    """
    A structured, technology-focused learning track.

    A path is composed of an ordered sequence of :class:`LearningStep` items.
    Completing the path is expected to develop all listed ``competencies``.

    Attributes
    ----------
    id:
        Unique identifier (e.g. ``"python-beginner-01"``).
    title:
        Human-readable name (e.g. ``"Python Foundations"``).
    technology:
        Primary technology or language targeted (e.g. ``"Python"``).
    level:
        Overall difficulty of the path.
    steps:
        Ordered list of learning steps that make up the path.
    competencies:
        Aggregate list of all competencies a learner gains by finishing
        the path. Derived from the union of each step's
        ``competencies_developed``, but stored explicitly to allow
        fast lookup without iterating over every step.
    description:
        Optional longer description or motivation for the path.
    """

    id: str
    title: str
    technology: str
    level: Level
    steps: list[LearningStep]
    competencies: list[str]
    description: str = ""


# ---------------------------------------------------------------------------
# LearnerProfile
# ---------------------------------------------------------------------------


@dataclass
class LearnerProfile:
    """
    A snapshot of a learner's current state and professional aspiration.

    Attributes
    ----------
    id:
        Unique identifier for this profile (e.g. ``"learner-42"``).
    name:
        Learner's display name. ``None`` is allowed for anonymous or
        programmatically imported profiles where a name is not yet known.
    current_competencies:
        List of skill/competency tags the learner already possesses
        (e.g. ``["Python basics", "Git", "REST APIs"]``).
    current_level:
        Self-assessed or system-assessed overall proficiency level.
    professional_goal:
        Free-text description of where the learner wants to go
        (e.g. ``"Become a backend developer with FastAPI"``).
    technologies_of_interest:
        Technologies the learner wants to focus on or explore.
    notes:
        Optional free-form notes (learning style preferences, constraints, etc.).
    """

    id: str
    name: Optional[str]
    current_competencies: list[str]
    current_level: Level
    professional_goal: str
    technologies_of_interest: list[str] = field(default_factory=list)
    notes: str = ""


# ---------------------------------------------------------------------------
# Challenge
# ---------------------------------------------------------------------------


@dataclass
class Challenge:
    """
    A concrete, hands-on task that turns learning into evidence.

    Challenges are the mechanism by which abstract competencies become
    demonstrable artefacts (code, writeups, projects).

    Attributes
    ----------
    id:
        Unique identifier (e.g. ``"challenge-python-cli-01"``).
    title:
        Short, action-oriented title (e.g. ``"Build a CSV Analyser CLI"``).
    technology:
        Primary technology exercised by this challenge.
    level:
        Difficulty level.
    description:
        Full problem statement — what the learner must build or demonstrate.
    evaluation_criteria:
        Explicit, measurable acceptance criteria. Each entry is one
        checkable condition (e.g. ``"Handles missing values without crashing"``).
    competencies_assessed:
        Competency tags that this challenge validates.
    estimated_hours:
        Rough effort estimate in hours. ``None`` means unknown.
    """

    id: str
    title: str
    technology: str
    level: Level
    description: str
    evaluation_criteria: list[str]
    competencies_assessed: list[str]
    estimated_hours: Optional[float] = None


# ---------------------------------------------------------------------------
# Recommendation
# ---------------------------------------------------------------------------


@dataclass
class Recommendation:
    """
    A suggested next step for a learner, grounded in their profile and gaps.

    A recommendation does *not* encode the algorithm that produced it —
    that belongs in the business-logic layer. This model carries only
    the outcome: what to do next and why.

    Attributes
    ----------
    id:
        Unique identifier for this recommendation instance.
    learner_id:
        References the :attr:`LearnerProfile.id` this recommendation targets.
    recommendation_type:
        Classifies the nature of the suggestion (path, challenge, review).
    target_id:
        ID of the recommended :class:`LearningPath` or :class:`Challenge`.
    rationale:
        Human-readable explanation of *why* this step is recommended
        (e.g. ``"You know Python basics but lack async skills"``).
    competencies_to_develop:
        The specific gaps this recommendation is intended to close.
    priority:
        Relative importance on a **1–5 scale** (higher = more urgent).
        Defaults to ``1`` (lowest urgency).

        Scale reference:

        * ``1`` — nice to have; explore when ready.
        * ``2`` — worth doing soon to round out existing knowledge.
        * ``3`` — recommended next step; addresses a clear gap.
        * ``4`` — high priority; gap is blocking progress toward the goal.
        * ``5`` — critical; learner cannot advance meaningfully without this.
    """

    id: str
    learner_id: str
    recommendation_type: RecommendationType
    target_id: str
    rationale: str
    competencies_to_develop: list[str]
    priority: int = 1


# ---------------------------------------------------------------------------
# CompetencyAnalysis
# ---------------------------------------------------------------------------


@dataclass
class CompetencyAnalysis:
    """
    The result of comparing a learner's declared competencies against those
    required by a single :class:`LearningPath`.

    This is a **pure data container** — no algorithms, no I/O.  The values
    are computed by :mod:`core.competency_analyzer` and stored here for
    consumption by the CLI layer and tests.

    Attributes
    ----------
    path:
        The :class:`LearningPath` this analysis refers to.
    matched_competencies:
        Competencies that appear in *both* the learner's profile and the
        path's required list.  Names are preserved exactly as they appear
        in the path's JSON data (original casing).
    missing_competencies:
        Competencies required by the path that the learner has **not**
        declared.  Names come from the path's JSON data.
    extra_competencies:
        Competencies declared by the learner that are *not* required by
        this path.  Names come from the learner's profile data.
    coverage_index:
        Proportion of the path's required competencies that the learner
        has declared: ``len(matched) / len(path.competencies)``.
        Returns ``0.0`` when the path has no competencies listed.

        .. warning::
            This index reflects **self-declared** competencies only.
            It does not imply verified mastery or demonstrated evidence.
    recommendations:
        Ordered list of :class:`Recommendation` objects — one per entry in
        ``missing_competencies``, sorted by priority (descending) then by
        the earliest step that develops the competency (ascending).
    """

    path: "LearningPath"
    matched_competencies: list[str]
    missing_competencies: list[str]
    extra_competencies: list[str]
    coverage_index: float
    recommendations: list["Recommendation"] = field(default_factory=list)
