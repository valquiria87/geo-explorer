"""
commands/certificado.py
-----------------------
Command that generates a fictional completion certificate (certificado fictício)
for a learning activity completed in Geo-Explorer.

Public API
~~~~~~~~~~
- ``build_certificate(participant, activity, technology, level,
                      competencies, issued_on)``  → dict
- ``display_certificate(cert)``                   → None  (prints to stdout)
- ``generate_certificate(participant, activity, technology, level,
                         competencies, issued_on)`` → None  (prints to stdout)

Design principles
~~~~~~~~~~~~~~~~~
* **Separation of concerns** — data construction (build_certificate) and
  presentation (display_certificate) are independent and each testable alone.
* **No external dependencies** — standard library only (uuid, datetime).
* **No PDF generation** in this stage.
* **No professional credential claim** — the certificate text is explicit that
  it is a fictional, non-official record produced for learning-progress purposes.
* **Graceful validation** — empty participant name or empty activity name
  raise ValueError before any certificate data is created.
"""

from __future__ import annotations

import uuid
from datetime import date
from typing import Optional


# ---------------------------------------------------------------------------
# Disclaimer constant — always present in every certificate
# ---------------------------------------------------------------------------

DISCLAIMER = "CERTIFICADO FICTÍCIO — SEM VALIDADE OFICIAL"


# ---------------------------------------------------------------------------
# Data construction
# ---------------------------------------------------------------------------


def build_certificate(
    participant: str,
    activity: str,
    technology: str,
    level: str,
    competencies: list[str],
    issued_on: Optional[date] = None,
) -> dict:
    """Build and return a certificate data dictionary.

    The certificate dict contains all fields needed to render or store the
    certificate.  No I/O is performed here.

    Parameters
    ----------
    participant:
        Full name of the person who completed the activity.
        Must be a non-empty, non-whitespace string.
    activity:
        Name of the learning trail or challenge completed.
        Must be a non-empty, non-whitespace string.
    technology:
        Primary technology covered (e.g. ``"Python"``).
    level:
        Proficiency level of the activity (e.g. ``"beginner"``).
    competencies:
        List of competencies developed during the activity.
    issued_on:
        Issue date.  Defaults to ``date.today()`` when ``None``.

    Returns
    -------
    dict
        A dictionary with the following keys:

        ``id``          — unique identifier (UUID4 string)
        ``participant`` — participant name (stripped)
        ``activity``    — activity name (stripped)
        ``technology``  — technology string
        ``level``       — level string
        ``issued_on``   — issue date as ``datetime.date``
        ``competencies``— copy of the competencies list
        ``disclaimer``  — always equal to :data:`DISCLAIMER`
        ``recognition`` — short recognition text

    Raises
    ------
    ValueError
        When *participant* or *activity* is empty or consists only of
        whitespace.
    """
    if not participant or not participant.strip():
        raise ValueError("Participant name must not be empty.")
    if not activity or not activity.strip():
        raise ValueError("Activity name must not be empty.")

    effective_date = issued_on if issued_on is not None else date.today()

    return {
        "id": str(uuid.uuid4()),
        "participant": participant.strip(),
        "activity": activity.strip(),
        "technology": technology,
        "level": level,
        "issued_on": effective_date,
        "competencies": list(competencies),
        "disclaimer": DISCLAIMER,
        "recognition": (
            f"Reconhecemos que {participant.strip()} concluiu a atividade "
            f'"{activity.strip()}" no âmbito do Geo-Explorer — '
            "Navegador Inteligente de Carreira, desenvolvendo as competências "
            "listadas neste documento para fins de aprendizado e progresso pessoal."
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
    print(f"  Certificado de Conclusão")
    print()
    print(f"  ID          : {cert['id']}")
    print(f"  Participante: {cert['participant']}")
    print(f"  Atividade   : {cert['activity']}")
    print(f"  Tecnologia  : {cert['technology']}")
    print(f"  Nível       : {cert['level']}")
    print(f"  Emissão     : {cert['issued_on'].strftime('%d/%m/%Y')}")
    print()
    print("  Competências desenvolvidas:")
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
    competencies: list[str],
    issued_on: Optional[date] = None,
) -> None:
    """Build and print a fictional completion certificate.

    Parameters
    ----------
    participant:
        Full name of the learner.
    activity:
        Name of the trail or challenge completed.
    technology:
        Primary technology covered.
    level:
        Proficiency level (e.g. ``"beginner"``).
    competencies:
        List of competencies developed.
    issued_on:
        Optional issue date; defaults to today.

    Raises
    ------
    ValueError
        When *participant* or *activity* is empty or consists only of
        whitespace.
    """
    cert = build_certificate(
        participant=participant,
        activity=activity,
        technology=technology,
        level=level,
        competencies=competencies,
        issued_on=issued_on,
    )
    display_certificate(cert)
