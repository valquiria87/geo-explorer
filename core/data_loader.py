"""
core/data_loader.py
-------------------
Loads learning-path data from the JSON file bundled with the project and
converts it into the domain model objects defined in ``core/models.py``.

Public API
~~~~~~~~~~
- ``load_learning_paths()`` → list[LearningPath]

No external dependencies are used.  All I/O and conversion errors produce
descriptive messages instead of opaque tracebacks.
"""

from __future__ import annotations

import json
import os
from typing import Any

from core.models import LearningPath, LearningStep, Level


# ---------------------------------------------------------------------------
# Path resolution — always relative to this file, never to cwd
# ---------------------------------------------------------------------------

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DATA_FILE = os.path.join(_PROJECT_ROOT, "data", "learning_paths.json")


# ---------------------------------------------------------------------------
# Internal conversion helpers
# ---------------------------------------------------------------------------


def _parse_level(raw: Any, context: str) -> Level:
    """Convert a raw string value to a :class:`Level` enum member.

    Parameters
    ----------
    raw:
        The value read from the JSON field.
    context:
        Human-readable label used in error messages (e.g. path id).

    Raises
    ------
    ValueError
        When *raw* is not a string or does not map to a known ``Level``.
    """
    if not isinstance(raw, str):
        raise ValueError(
            f"[{context}] 'level' must be a string, got {type(raw).__name__!r}."
        )
    try:
        return Level(raw.lower())
    except ValueError:
        valid = ", ".join(m.value for m in Level)
        raise ValueError(
            f"[{context}] Unknown level {raw!r}. Valid values: {valid}."
        )


def _parse_step(raw: Any, path_id: str, index: int) -> LearningStep:
    """Convert a raw dict to a :class:`LearningStep`.

    Raises
    ------
    ValueError
        When required fields are missing or have the wrong type.
    """
    context = f"path '{path_id}', step index {index}"
    if not isinstance(raw, dict):
        raise ValueError(f"[{context}] Step must be a JSON object, got {type(raw).__name__!r}.")

    required = ("title", "description", "competencies_developed", "order")
    for field in required:
        if field not in raw:
            raise ValueError(f"[{context}] Missing required field '{field}'.")

    if not isinstance(raw["competencies_developed"], list):
        raise ValueError(f"[{context}] 'competencies_developed' must be a list.")

    return LearningStep(
        title=str(raw["title"]),
        description=str(raw["description"]),
        competencies_developed=[str(c) for c in raw["competencies_developed"]],
        order=int(raw["order"]),
    )


def _parse_learning_path(raw: Any, index: int) -> LearningPath:
    """Convert a raw dict to a :class:`LearningPath`.

    Raises
    ------
    ValueError
        When required fields are missing, have the wrong type, or the level
        string is not a known :class:`Level` value.
    """
    context = f"path index {index}"
    if not isinstance(raw, dict):
        raise ValueError(f"[{context}] Learning path must be a JSON object, got {type(raw).__name__!r}.")

    required = ("id", "title", "technology", "level", "steps", "competencies")
    for field in required:
        if field not in raw:
            raise ValueError(f"[{context}] Missing required field '{field}'.")

    path_id: str = str(raw["id"])

    if not isinstance(raw["steps"], list):
        raise ValueError(f"[path '{path_id}'] 'steps' must be a list.")
    if not isinstance(raw["competencies"], list):
        raise ValueError(f"[path '{path_id}'] 'competencies' must be a list.")

    steps = [_parse_step(s, path_id, i) for i, s in enumerate(raw["steps"])]
    level = _parse_level(raw["level"], path_id)

    return LearningPath(
        id=path_id,
        title=str(raw["title"]),
        technology=str(raw["technology"]),
        level=level,
        steps=steps,
        competencies=[str(c) for c in raw["competencies"]],
        description=str(raw.get("description", "")),
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def load_learning_paths(filepath: str = _DATA_FILE) -> list[LearningPath]:
    """Read ``data/learning_paths.json`` and return a list of :class:`LearningPath`.

    Parameters
    ----------
    filepath:
        Absolute path to the JSON file.  Defaults to the bundled
        ``data/learning_paths.json`` resolved relative to the project root,
        so results are independent of the current working directory.

    Returns
    -------
    list[LearningPath]
        All learning paths found in the file, in the order they appear.

    Raises
    ------
    SystemExit
        On any unrecoverable error (file not found, invalid JSON, or
        incompatible structure).  A descriptive message is printed before
        exiting so callers receive clear feedback without a raw traceback.
    """
    # --- 1. Read the file -----------------------------------------------
    try:
        with open(filepath, encoding="utf-8") as fh:
            raw_text = fh.read()
    except FileNotFoundError:
        raise FileNotFoundError(
            f"Learning-paths file not found: {filepath}\n"
            "Make sure 'data/learning_paths.json' exists in the project root."
        )
    except OSError as exc:
        raise OSError(f"Could not read '{filepath}': {exc}") from exc

    # --- 2. Parse JSON --------------------------------------------------
    try:
        payload = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"'{filepath}' contains invalid JSON: {exc}"
        ) from exc

    # --- 3. Validate top-level structure --------------------------------
    if not isinstance(payload, list):
        raise ValueError(
            f"'{filepath}' must contain a JSON array at the top level, "
            f"got {type(payload).__name__!r}."
        )

    # --- 4. Convert each record ----------------------------------------
    paths: list[LearningPath] = []
    for i, record in enumerate(payload):
        paths.append(_parse_learning_path(record, i))

    return paths
