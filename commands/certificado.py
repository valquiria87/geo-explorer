"""
commands/certificado.py
-----------------------
Command that generates a fictional certificate (certificado fictício): a record of
a learning trail selected from the catalog and of its associated competencies.
All information is self-declared; Geo-Explorer does not track or verify completion.

Public API
~~~~~~~~~~
- ``resolve_learning_path(activity, technology, level, paths)`` → tuple[LearningPath, str, str]
- ``build_certificate(participant, activity, technology, level,
                      competencies, paths, issued_on)``         → dict
- ``display_certificate(cert)``                                 → None  (prints to stdout)
- ``generate_certificate(participant, activity, technology, level,
                         competencies, paths, issued_on)``      → None  (prints to stdout)

Design principles
~~~~~~~~~~~~~~~~~
* **Separation of concerns** — data construction (build_certificate) and
  presentation (display_certificate) are independent and each testable alone.
* **Pure domain function** — build_certificate performs no I/O. The list of
  valid LearningPath objects must be injected by callers.
* **Strict catalog integration** — certificates can only be issued for activities
  matching an existing LearningPath (by ID or official title). Technology and
  level must be strictly compatible with the matched path.
* **Competency fallback** — competencies that are not provided (``None``, an
  empty list, or a list with only blank strings) default to the competencies
  of the matched trail. The rule lives only in build_certificate, so the CLI,
  GUI and MCP layers behave identically.
* **No PDF generation** in this stage.
* **No professional credential claim** — the certificate text is explicit that
  it is a fictional, non-official record produced for illustrative purposes.
* **No completion or mastery claim** — the text never states that the person
  completed or took part in the trail, nor that any competency was developed;
  the trail is only recorded as selected from the catalog and the competencies
  as associated with it and unverified.
* **Graceful validation** — empty participant, unknown activity or mismatched
  technology/level raise ValueError before any certificate data is created.
"""

from __future__ import annotations

import uuid
from datetime import date
from typing import Optional

from core.data_loader import load_learning_paths
from core.models import LearningPath, Level


# ---------------------------------------------------------------------------
# Disclaimer constant — always present in every certificate
# ---------------------------------------------------------------------------

DISCLAIMER = "CERTIFICADO FICTÍCIO — SEM VALIDADE OFICIAL"


# ---------------------------------------------------------------------------
# Catalog resolution & validation
# ---------------------------------------------------------------------------


def resolve_learning_path(
    activity: str,
    technology: str,
    level: str,
    paths: list[LearningPath],
) -> tuple[LearningPath, str, str]:
    """Resolve an activity to a valid LearningPath and ensure technology and level match.

    Lookups match exclusively against ``path.id`` or ``path.title``
    (case-insensitive). Technology is not accepted as an activity identifier.

    Parameters
    ----------
    activity:
        Official title or unique identifier of the trail.
    technology:
        Primary technology string. Must match path.technology (case-insensitive).
    level:
        Proficiency level string. Must match path.level.value (case-insensitive).
    paths:
        List of known :class:`~core.models.LearningPath` objects.

    Returns
    -------
    tuple[LearningPath, str, str]
        (matched_path, resolved_technology, resolved_level)

    Raises
    ------
    ValueError
        When activity is empty, not found in *paths*, or when technology/level
        fail compatibility checks.
    """
    if not activity or not activity.strip():
        raise ValueError("Activity name must not be empty.")

    if not isinstance(paths, list) or not paths:
        raise ValueError("A non-empty list of LearningPath instances must be provided.")

    needle = activity.strip().lower()
    matched_path: LearningPath | None = None
    for path in paths:
        if path.id.strip().lower() == needle or path.title.strip().lower() == needle:
            matched_path = path
            break

    if matched_path is None:
        valid_titles = ", ".join(f'"{p.title}"' for p in paths)
        raise ValueError(
            f"Atividade '{activity.strip()}' não encontrada no catálogo de trilhas. "
            f"Trilhas disponíveis: {valid_titles}."
        )

    if not technology or not technology.strip():
        raise ValueError("Technology must not be empty.")

    if technology.strip().lower() != matched_path.technology.lower():
        raise ValueError(
            f"Tecnologia '{technology.strip()}' incompatível com a trilha '{matched_path.title}'. "
            f"Tecnologia esperada: '{matched_path.technology}'."
        )

    if not level or not level.strip():
        raise ValueError("Level must not be empty.")

    level_norm = level.strip().lower()
    try:
        parsed_level = Level(level_norm)
    except ValueError:
        valid_levels = ", ".join(m.value for m in Level)
        raise ValueError(
            f"Nível inválido '{level.strip()}'. Valores aceitos: {valid_levels}."
        )

    if parsed_level != matched_path.level:
        raise ValueError(
            f"Nível '{level.strip()}' incompatível com a trilha '{matched_path.title}'. "
            f"Nível esperado: '{matched_path.level.value}'."
        )

    return matched_path, matched_path.technology, matched_path.level.value


# ---------------------------------------------------------------------------
# Data construction
# ---------------------------------------------------------------------------


def _normalize_competencies(competencies: Optional[list[str]]) -> list[str]:
    """Return the custom competencies stripped, in order, without blank items.

    ``None``, an empty list, or a list made only of blank strings yields ``[]``,
    which :func:`build_certificate` interprets as "not provided".
    """
    if not competencies:
        return []
    return [c.strip() for c in competencies if isinstance(c, str) and c.strip()]


def build_certificate(
    participant: str,
    activity: str,
    technology: str,
    level: str,
    competencies: Optional[list[str]],
    paths: list[LearningPath],
    issued_on: Optional[date] = None,
) -> dict:
    """Build and return a certificate data dictionary validated against *paths*.

    The certificate dict contains all fields needed to render or store the
    certificate.  No I/O is performed here.

    Parameters
    ----------
    participant:
        Full name of the person named in the record (self-declared).
        Must be a non-empty, non-whitespace string.
    activity:
        Title or unique ID of the learning trail.
    technology:
        Primary technology covered (must match the trail).
    level:
        Proficiency level of the activity (must match the trail).
    competencies:
        Competencies associated with the trail. ``None``, an empty list, or a
        list containing only empty/whitespace strings means "not provided":
        the competencies of the matched trail are used, as an independent copy.
        Custom competencies are supplied by the person; each item is kept in
        order, stripped, and blank items are dropped.
    paths:
        Mandatory list of valid :class:`~core.models.LearningPath` instances.
    issued_on:
        Issue date.  Defaults to ``date.today()`` when ``None``.

    Returns
    -------
    dict
        A dictionary with the following keys:

        ``id``          — unique identifier (UUID4 string)
        ``participant`` — participant name (stripped)
        ``activity``    — resolved official activity title
        ``technology``  — validated technology string
        ``level``       — validated level string
        ``issued_on``   — issue date as ``datetime.date``
        ``competencies``— independent list: the custom competencies (stripped,
                          blanks dropped) or a copy of the matched trail's
                          competencies when none were provided
        ``disclaimer``  — always equal to :data:`DISCLAIMER`
        ``recognition`` — short recognition text

    Raises
    ------
    ValueError
        When *participant* is empty, *paths* is missing/empty, or the activity,
        technology, or level fail catalog validation.
    """
    if not participant or not participant.strip():
        raise ValueError("Participant name must not be empty.")

    matched_path, resolved_tech, resolved_level = resolve_learning_path(
        activity=activity,
        technology=technology,
        level=level,
        paths=paths,
    )

    effective_date = issued_on if issued_on is not None else date.today()
    # Single place for the fallback rule: nothing provided -> the trail's own
    # competencies, copied so the certificate never aliases the catalog.
    effective_competencies = _normalize_competencies(competencies) or list(
        matched_path.competencies
    )

    return {
        "id": str(uuid.uuid4()),
        "participant": participant.strip(),
        "activity": matched_path.title,
        "technology": resolved_tech,
        "level": resolved_level,
        "issued_on": effective_date,
        "competencies": effective_competencies,
        "disclaimer": DISCLAIMER,
        "recognition": (
            "Registro fictício e sem validade oficial, gerado com informações "
            f"autodeclaradas de {participant.strip()}. A trilha "
            f'"{matched_path.title}" foi selecionada do catálogo do Geo-Explorer — '
            "Navegador Inteligente de Carreira. Competências personalizadas, "
            "quando fornecidas, são informadas pela pessoa; quando omitidas, "
            "são utilizadas as competências associadas à trilha selecionada "
            "no catálogo. Essas competências não foram verificadas. Este "
            "registro não comprova progresso, conclusão ou domínio de "
            "competências, nem participação."
        ),
    }


# ---------------------------------------------------------------------------
# Presentation
# ---------------------------------------------------------------------------


def display_certificate(cert: dict) -> None:
    """Print a formatted certificate to standard output.

    Parameters
    ----------
    cert:
        A certificate dictionary as returned by :func:`build_certificate`.
    """
    border = "=" * 60
    print(border)
    print(f"  {cert['disclaimer']}")
    print(border)
    print()
    print("  Registro de Trilha e Competências Associadas")
    print()
    print(f"  ID          : {cert['id']}")
    print(f"  Participante: {cert['participant']}")
    print(f"  Atividade   : {cert['activity']}")
    print(f"  Tecnologia  : {cert['technology']}")
    print(f"  Nível       : {cert['level']}")
    print(f"  Emissão     : {cert['issued_on'].strftime('%d/%m/%Y')}")
    print()
    print("  Competências associadas à atividade:")
    for competency in cert["competencies"]:
        print(f"    - {competency}")
    print()
    print(f"  {cert['recognition']}")
    print()
    print(border)


# ---------------------------------------------------------------------------
# Public command
# ---------------------------------------------------------------------------


def generate_certificate(
    participant: str,
    activity: str,
    technology: str,
    level: str,
    competencies: Optional[list[str]],
    paths: Optional[list[LearningPath]] = None,
    issued_on: Optional[date] = None,
) -> None:
    """Build and print a fictional certificate record validated against the catalog.

    Parameters
    ----------
    participant:
        Full name of the learner.
    activity:
        Official title or unique ID of the trail.
    technology:
        Primary technology covered.
    level:
        Proficiency level (e.g. ``"beginner"``).
    competencies:
        Competencies associated with the trail. Custom competencies are
        supplied by the person; ``None``/empty/blank-only uses the matched
        trail's competencies (see :func:`build_certificate`).
    paths:
        Optional list of trails. Defaults to loading from catalog file.
    issued_on:
        Optional issue date; defaults to today.

    Raises
    ------
    ValueError
        When validation fails.
    """
    if paths is None:
        paths = load_learning_paths()

    cert = build_certificate(
        participant=participant,
        activity=activity,
        technology=technology,
        level=level,
        competencies=competencies,
        paths=paths,
        issued_on=issued_on,
    )
    display_certificate(cert)
