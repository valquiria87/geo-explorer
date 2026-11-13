"""
commands/desafio.py
-------------------
Command that selects and displays a challenge (desafio) for a given
technology and proficiency level.

Public API
~~~~~~~~~~
- ``load_challenges(filepath)``                   → list[Challenge]
- ``filter_challenges(technology, level, pool)``  → list[Challenge]
- ``generate_challenge(technology, level)``        → None  (prints to stdout)

Design principles
~~~~~~~~~~~~~~~~~
* **Separation of concerns** — loading, filtering, and presentation are
  independent functions, each testable in isolation.
* **No mutation** — the original data loaded from JSON is never modified.
* **No external dependencies** — standard library only.
* **Graceful errors** — empty input and invalid levels produce clear messages;
  no raw tracebacks reach the user.
"""

from __future__ import annotations

import json
import os
import random
from typing import Optional

from core.models import Challenge, Level


# ---------------------------------------------------------------------------
# Path resolution — always relative to this file, never to cwd
# ---------------------------------------------------------------------------

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DATA_FILE = os.path.join(_PROJECT_ROOT, "data", "challenges.json")


# ---------------------------------------------------------------------------
# Internal conversion helpers
# ---------------------------------------------------------------------------


def _parse_challenge(raw: object, index: int) -> Challenge:
    """Convert a raw JSON dict to a :class:`Challenge`.

    Parameters
    ----------
    raw:
        The value read from the JSON array.
    index:
        Zero-based position in the source array; used in error messages.

    Raises
    ------
    ValueError
        When required fields are missing, have the wrong type, or the level
        string does not map to a known :class:`Level` value.
    """
    context = f"challenge index {index}"

    if not isinstance(raw, dict):
        raise ValueError(
            f"[{context}] Challenge must be a JSON object, "
            f"got {type(raw).__name__!r}."
        )

    required = (
        "id", "title", "technology", "level",
        "description", "evaluation_criteria", "competencies_assessed",
    )
    for field_name in required:
        if field_name not in raw:
            raise ValueError(
                f"[{context}] Missing required field '{field_name}'."
            )

    challenge_id: str = str(raw["id"])

    for list_field in ("evaluation_criteria", "competencies_assessed"):
        if not isinstance(raw[list_field], list):
            raise ValueError(
                f"[challenge '{challenge_id}'] '{list_field}' must be a list."
            )

    level_raw = raw["level"]
    if not isinstance(level_raw, str):
        raise ValueError(
            f"[challenge '{challenge_id}'] 'level' must be a string, "
            f"got {type(level_raw).__name__!r}."
        )
    try:
        level = Level(level_raw.lower())
    except ValueError:
        valid = ", ".join(m.value for m in Level)
        raise ValueError(
            f"[challenge '{challenge_id}'] Unknown level {level_raw!r}. "
            f"Valid values: {valid}."
        )

    estimated_hours_raw = raw.get("estimated_hours")
    estimated_hours: Optional[float] = (
        float(estimated_hours_raw) if estimated_hours_raw is not None else None
    )

    return Challenge(
        id=challenge_id,
        title=str(raw["title"]),
        technology=str(raw["technology"]),
        level=level,
        description=str(raw["description"]),
        evaluation_criteria=[str(c) for c in raw["evaluation_criteria"]],
        competencies_assessed=[str(c) for c in raw["competencies_assessed"]],
        estimated_hours=estimated_hours,
    )


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------


def load_challenges(filepath: str = _DATA_FILE) -> list[Challenge]:
    """Read ``data/challenges.json`` and return a list of :class:`Challenge`.

    Parameters
    ----------
    filepath:
        Absolute path to the JSON file.  Defaults to the bundled
        ``data/challenges.json`` resolved relative to the project root.

    Returns
    -------
    list[Challenge]
        All challenges found in the file, in the order they appear.

    Raises
    ------
    FileNotFoundError
        When the file does not exist at *filepath*.
    OSError
        When the file exists but cannot be read.
    ValueError
        When the file contains invalid JSON or an incompatible structure.
    """
    try:
        with open(filepath, encoding="utf-8") as fh:
            raw_text = fh.read()
    except FileNotFoundError:
        raise FileNotFoundError(
            f"Challenges file not found: {filepath}\n"
            "Make sure 'data/challenges.json' exists in the project root."
        )
    except OSError as exc:
        raise OSError(f"Could not read '{filepath}': {exc}") from exc

    try:
        payload = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"'{filepath}' contains invalid JSON: {exc}"
        ) from exc

    if not isinstance(payload, list):
        raise ValueError(
            f"'{filepath}' must contain a JSON array at the top level, "
            f"got {type(payload).__name__!r}."
        )

    return [_parse_challenge(record, i) for i, record in enumerate(payload)]


# ---------------------------------------------------------------------------
# Filtering
# ---------------------------------------------------------------------------


def filter_challenges(
    technology: str,
    level: Level,
    pool: list[Challenge],
) -> list[Challenge]:
    """Return all challenges in *pool* that match *technology* and *level*.

    The technology comparison is case-insensitive.  The original *pool* list
    and its items are never mutated.

    Parameters
    ----------
    technology:
        Technology name to match (e.g. ``"python"`` or ``"Python"``).
    level:
        :class:`Level` enum value to match.
    pool:
        The collection of challenges to search within.

    Returns
    -------
    list[Challenge]
        A new list containing only the matching challenges, preserving order.
        Returns an empty list when nothing matches.
    """
    needle = technology.strip().lower()
    return [
        c for c in pool
        if c.technology.lower() == needle and c.level == level
    ]


# ---------------------------------------------------------------------------
# Formatting / display
# ---------------------------------------------------------------------------


def _display_challenge(challenge: Challenge) -> None:
    """Print a single :class:`Challenge` to standard output."""
    print(f"Title      : {challenge.title}")
    print(f"Technology : {challenge.technology}")
    print(f"Level      : {challenge.level.value}")
    if challenge.estimated_hours is not None:
        print(f"Est. Hours : {challenge.estimated_hours:g}")
    print()
    print(f"Description:")
    print(f"  {challenge.description}")
    print()
    print(f"Evaluation criteria ({len(challenge.evaluation_criteria)}):")
    for criterion in challenge.evaluation_criteria:
        print(f"  - {criterion}")
    print()
    print(f"Competencies assessed:")
    for competency in challenge.competencies_assessed:
        print(f"  - {competency}")


# ---------------------------------------------------------------------------
# Public command
# ---------------------------------------------------------------------------


def generate_challenge(technology: str, level: Level) -> None:
    """Print a randomly selected challenge for *technology* and *level*.

    Behaviour
    ---------
    * Validates that *technology* is a non-empty, non-whitespace string.
    * Loads all challenges from ``data/challenges.json``.
    * Filters by *technology* (case-insensitive) and *level*.
    * If one or more matches are found, picks one at random and prints it.
    * Prints a clear "not found" message when no challenge matches.
    * Never modifies the loaded data.

    Parameters
    ----------
    technology:
        Technology name entered by the user (e.g. ``"Python"``).
    level:
        Desired difficulty level.
    """
    if not technology or not technology.strip():
        print("Error: please provide a non-empty technology name.")
        return

    challenges = load_challenges()
    matches = filter_challenges(technology, level, challenges)

    if not matches:
        print(
            f"No challenge found for technology '{technology.strip()}' "
            f"at level '{level.value}'."
        )
        return

    chosen = random.choice(matches)
    _display_challenge(chosen)
