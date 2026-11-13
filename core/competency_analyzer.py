"""
core/competency_analyzer.py
----------------------------
Pure business-logic layer for Geo-Explorer's competency analysis feature.

All public functions are **pure**: they accept plain domain objects, perform
no I/O, mutate no input, and always return new objects.  This makes every
function directly unit-testable without mocks or fixtures.

Public API
~~~~~~~~~~
- ``normalize(text)``                              → str
- ``analyze_profile(profile, paths, challenges)``  → list[CompetencyAnalysis]

Internal helpers (not part of the public API but importable for testing)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
- ``_build_analysis(profile, path, challenges)``   → CompetencyAnalysis
- ``_build_recommendation(...)``                   → Recommendation
- ``_priority(n_steps, n_challenges)``             → int
- ``_level_rank(level)``                           → int
- ``_recommendation_id(learner_id, competency)``   → str
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from core.models import (
    CompetencyAnalysis,
    LearnerProfile,
    LearningPath,
    Challenge,
    Recommendation,
    RecommendationType,
    Level,
)

# ---------------------------------------------------------------------------
# Sentinel value used in sort key when a competency has no associated step
# ---------------------------------------------------------------------------

_NO_STEP_SENTINEL: int = 9999


# ---------------------------------------------------------------------------
# Normalisation
# ---------------------------------------------------------------------------


def normalize(text: str) -> str:
    """Return a canonical comparison form of *text*.

    Strips surrounding whitespace and folds to lower-case.  The original
    string is **never** used for normalised operations — callers must call
    this function explicitly when they need a comparison key.

    This function is intentionally minimal: it does not collapse internal
    spaces, remove punctuation, or apply stemming.  Competency names in the
    project data are already well-formed; only casing and edge whitespace
    differ across sources.

    Parameters
    ----------
    text:
        Any competency string (from a profile, a path, or a challenge).

    Returns
    -------
    str
        Lower-cased, stripped version of *text*.
    """
    return text.strip().lower()


# ---------------------------------------------------------------------------
# Level numeric rank (used for challenge-proximity selection)
# ---------------------------------------------------------------------------

_LEVEL_RANK: dict[Level, int] = {
    Level.BEGINNER: 1,
    Level.INTERMEDIATE: 2,
    Level.ADVANCED: 3,
}


def _level_rank(level: Level) -> int:
    """Return the numeric rank for *level* (BEGINNER=1, INTERMEDIATE=2, ADVANCED=3)."""
    return _LEVEL_RANK[level]


# ---------------------------------------------------------------------------
# Priority calculation
# ---------------------------------------------------------------------------


def _priority(n_steps: int, n_challenges: int) -> int:
    """Compute the recommendation priority for a missing competency.

    Parameters
    ----------
    n_steps:
        Number of :class:`~core.models.LearningStep` objects within the
        target path that list this competency in
        ``competencies_developed``.
    n_challenges:
        Number of :class:`~core.models.Challenge` objects for the same
        technology that list this competency in ``competencies_assessed``.

    Returns
    -------
    int
        Priority on the 1–5 scale defined in :class:`~core.models.Recommendation`.
    """
    if n_steps >= 3:
        return 5
    if n_steps == 2:
        return 4
    if n_steps == 1 and n_challenges >= 1:
        return 3
    if n_steps == 1 and n_challenges == 0:
        return 2
    # n_steps == 0 (competency in path.competencies but no step develops it,
    # OR only appears in challenges)
    return 1


# ---------------------------------------------------------------------------
# Recommendation ID helper
# ---------------------------------------------------------------------------


def _recommendation_id(learner_id: str, competency: str) -> str:
    """Build a stable, filesystem-safe recommendation ID.

    Parameters
    ----------
    learner_id:
        The learner's profile ID.
    competency:
        The original competency name (will be normalised and slugified).

    Returns
    -------
    str
        A string of the form ``"rec-<learner_id>-<slug>"``.
    """
    slug = re.sub(r"[^a-z0-9]+", "-", normalize(competency)).strip("-")
    return f"rec-{learner_id}-{slug}"


# ---------------------------------------------------------------------------
# Single-competency recommendation builder
# ---------------------------------------------------------------------------


def _build_recommendation(
    competency: str,
    path: LearningPath,
    challenges: list[Challenge],
    learner_profile: LearnerProfile,
) -> Recommendation:
    """Build one :class:`~core.models.Recommendation` for a single missing
    *competency* within *path*.

    The function inspects *path*'s steps and the provided *challenges* to
    determine priority, target, type, and a human-readable rationale.
    All names in the output use their **original casing** from the source
    data.

    Parameters
    ----------
    competency:
        The missing competency name, exactly as it appears in
        ``path.competencies`` (original casing).
    path:
        The :class:`~core.models.LearningPath` being analysed.
    challenges:
        Full pool of :class:`~core.models.Challenge` objects (all
        technologies); the function filters by ``path.technology``.
    learner_profile:
        Used for ``learner_id`` and ``current_level`` (proximity ranking).
    """
    c_norm = normalize(competency)
    tech_norm = normalize(path.technology)

    # --- Steps that develop this competency (sorted by order for display) ---
    steps_with_c = sorted(
        [
            s for s in path.steps
            if c_norm in {normalize(x) for x in s.competencies_developed}
        ],
        key=lambda s: s.order,
    )
    n_steps = len(steps_with_c)

    # --- Challenges (same technology) that assess this competency -----------
    challenges_with_c = [
        ch for ch in challenges
        if c_norm in {normalize(x) for x in ch.competencies_assessed}
        and normalize(ch.technology) == tech_norm
    ]
    n_challenges = len(challenges_with_c)

    # --- Priority -----------------------------------------------------------
    priority = _priority(n_steps, n_challenges)

    # --- Target selection ---------------------------------------------------
    if n_steps >= 1:
        rec_type = RecommendationType.LEARNING_PATH
        target_id = path.id
    elif n_challenges >= 1:
        rec_type = RecommendationType.CHALLENGE
        learner_rank = _level_rank(learner_profile.current_level)
        # Sort by proximity to learner level, then by id for determinism
        sorted_candidates = sorted(
            challenges_with_c,
            key=lambda ch: (abs(_level_rank(ch.level) - learner_rank), ch.id),
        )
        target_id = sorted_candidates[0].id
    else:
        # Competency in path.competencies but absent from all steps and challenges
        rec_type = RecommendationType.LEARNING_PATH
        target_id = path.id

    # --- Rationale ----------------------------------------------------------
    if n_steps >= 1:
        step_refs = ", ".join(
            f"Step {s.order} ({s.title})" for s in steps_with_c
        )
        if challenges_with_c:
            challenge_refs = "; ".join(ch.title for ch in challenges_with_c)
            rationale = (
                f"'{competency}' não foi declarada no perfil e é exigida pela trilha. "
                f"Desenvolvida em: {step_refs}. "
                f"Avaliada pelo(s) desafio(s): {challenge_refs}."
            )
        else:
            rationale = (
                f"'{competency}' não foi declarada no perfil e é exigida pela trilha. "
                f"Desenvolvida em: {step_refs}."
            )
    elif n_challenges >= 1:
        # Build rationale that mentions ALL challenges, even though target picks closest
        challenge_refs = "; ".join(ch.title for ch in challenges_with_c)
        rationale = (
            f"'{competency}' não foi declarada no perfil e é exigida pela trilha, "
            f"mas não possui etapa associada. "
            f"Avaliada pelo(s) desafio(s): {challenge_refs}."
        )
    else:
        rationale = (
            f"'{competency}' não foi declarada no perfil e é exigida pela trilha "
            f"'{path.title}', mas não possui etapa ou desafio diretamente "
            f"associado nos dados disponíveis."
        )

    return Recommendation(
        id=_recommendation_id(learner_profile.id, competency),
        learner_id=learner_profile.id,
        recommendation_type=rec_type,
        target_id=target_id,
        rationale=rationale,
        competencies_to_develop=[competency],
        priority=priority,
    )


# ---------------------------------------------------------------------------
# Single-path analysis builder
# ---------------------------------------------------------------------------


def _build_analysis(
    profile: LearnerProfile,
    path: LearningPath,
    challenges: list[Challenge],
) -> CompetencyAnalysis:
    """Compare *profile*'s declared competencies against *path* and return a
    fully populated :class:`~core.models.CompetencyAnalysis`.

    Parameters
    ----------
    profile:
        The learner whose declared competencies are compared.
    path:
        The learning path to analyse against.
    challenges:
        Full challenge pool; used when building recommendations.
    """
    # Build normalised → original maps
    # If the profile has duplicate normalised forms, last entry wins (edge case)
    perfil_map: dict[str, str] = {normalize(c): c for c in profile.current_competencies}
    trilha_map: dict[str, str] = {normalize(c): c for c in path.competencies}

    matched_keys = perfil_map.keys() & trilha_map.keys()
    missing_keys = trilha_map.keys() - perfil_map.keys()
    extra_keys = perfil_map.keys() - trilha_map.keys()

    # Recover original names (path names for matched/missing; profile names for extra)
    matched = sorted([trilha_map[k] for k in matched_keys])
    missing = sorted([trilha_map[k] for k in missing_keys])
    extra = sorted([perfil_map[k] for k in extra_keys])

    coverage_index = (
        len(matched_keys) / len(trilha_map) if trilha_map else 0.0
    )

    # Build one recommendation per missing competency
    recs: list[Recommendation] = []
    for comp in missing:
        recs.append(_build_recommendation(comp, path, challenges, profile))

    # Sort: priority DESC, then earliest step order ASC (sentinel for no step),
    # then competency name ASC for full determinism
    def _sort_key(r: Recommendation) -> tuple:
        comp = r.competencies_to_develop[0]
        c_norm = normalize(comp)
        first_step_order = _NO_STEP_SENTINEL
        for s in sorted(path.steps, key=lambda s: s.order):
            if c_norm in {normalize(x) for x in s.competencies_developed}:
                first_step_order = s.order
                break
        return (-r.priority, first_step_order, comp)

    recs.sort(key=_sort_key)

    return CompetencyAnalysis(
        path=path,
        matched_competencies=matched,
        missing_competencies=missing,
        extra_competencies=extra,
        coverage_index=coverage_index,
        recommendations=recs,
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def analyze_profile(
    profile: LearnerProfile,
    paths: list[LearningPath],
    challenges: list[Challenge],
) -> list[CompetencyAnalysis]:
    """Analyse *profile* against all relevant learning paths.

    Parameters
    ----------
    profile:
        The learner whose declared competencies are compared.
    paths:
        Full collection of available :class:`~core.models.LearningPath` objects.
    challenges:
        Full collection of available :class:`~core.models.Challenge` objects.

    Returns
    -------
    list[CompetencyAnalysis]
        One :class:`~core.models.CompetencyAnalysis` per path that was
        analysed.  When ``profile.technologies_of_interest`` is non-empty,
        only paths whose ``technology`` matches (case-insensitively) are
        included.  When the list is empty, **all** paths are analysed.

    Notes
    -----
    * Input objects are **never mutated**.
    * The returned list preserves the order of the matching paths as they
      appear in *paths*.
    """
    if profile.technologies_of_interest:
        interest_norms = {normalize(t) for t in profile.technologies_of_interest}
        target_paths = [p for p in paths if normalize(p.technology) in interest_norms]
    else:
        target_paths = list(paths)

    return [_build_analysis(profile, path, challenges) for path in target_paths]
