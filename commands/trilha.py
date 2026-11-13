"""
commands/trilha.py
------------------
CLI command that displays a learning path (trilha de aprendizado) for a
given technology.

Public API
~~~~~~~~~~
- ``find_learning_path(technology, paths)`` → LearningPath | None
- ``show_learning_path(technology)``        → None  (prints to stdout)
"""

from __future__ import annotations

from typing import Optional

from core.data_loader import load_learning_paths
from core.models import LearningPath


# ---------------------------------------------------------------------------
# Lookup
# ---------------------------------------------------------------------------


def find_learning_path(
    technology: str, paths: list[LearningPath]
) -> Optional[LearningPath]:
    """Return the first :class:`LearningPath` whose *technology* matches
    *technology* (case-insensitive), or ``None`` if no match is found.

    Parameters
    ----------
    technology:
        The technology name to search for (e.g. ``"python"`` or ``"Python"``).
    paths:
        The collection of learning paths to search within.  The original
        list and its items are never mutated.

    Returns
    -------
    LearningPath | None
        The matching path, or ``None`` when no path is found.
    """
    needle = technology.strip().lower()
    for path in paths:
        if path.technology.lower() == needle:
            return path
    return None


# ---------------------------------------------------------------------------
# Formatting / display
# ---------------------------------------------------------------------------


def show_learning_path(technology: str) -> None:
    """Print the learning path for *technology* to standard output.

    Behaviour
    ---------
    * Loads all paths via :func:`~core.data_loader.load_learning_paths`.
    * Searches for a path whose ``technology`` matches *technology*
      case-insensitively.
    * Prints title, technology, level, description, ordered steps
      (including each step's competencies), and the path-level competencies.
    * Prints a clear "not found" message when the technology is unknown.
    * Prints a clear "empty input" message when *technology* is blank or
      consists only of whitespace.
    * Never modifies the loaded data.

    Parameters
    ----------
    technology:
        The technology name entered by the user.
    """
    if not technology or not technology.strip():
        print("Error: please provide a non-empty technology name.")
        return

    paths = load_learning_paths()
    path = find_learning_path(technology, paths)

    if path is None:
        print(f"No learning path found for technology: '{technology.strip()}'.")
        return

    # --- Header -----------------------------------------------------------
    print(f"Title      : {path.title}")
    print(f"Technology : {path.technology}")
    print(f"Level      : {path.level.value}")
    print(f"Description: {path.description}")
    print()

    # --- Steps ------------------------------------------------------------
    sorted_steps = sorted(path.steps, key=lambda s: s.order)
    print(f"Steps ({len(sorted_steps)}):")
    for step in sorted_steps:
        print(f"\n  Step {step.order}: {step.title}")
        print(f"  Description: {step.description}")
        if step.competencies_developed:
            competencies_str = ", ".join(step.competencies_developed)
            print(f"  Competencies developed: {competencies_str}")

    # --- Path-level competencies ------------------------------------------
    print()
    print("General competencies:")
    for competency in path.competencies:
        print(f"  - {competency}")
