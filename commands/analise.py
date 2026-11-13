"""
commands/analise.py
-------------------
CLI command that performs and displays a competency analysis for a learner
profile entered interactively.

Public API
~~~~~~~~~~
- ``show_competency_analysis(profile_data)`` → None  (prints to stdout)

Design principles
~~~~~~~~~~~~~~~~~
* **Separation of concerns** — data collection, analysis, and presentation
  are independent concerns.  This module owns only presentation and the
  thin wiring between user input and the analyser.
* **No mutation** — profile and path data are never modified.
* **No external dependencies** — standard library only.
* **Graceful errors** — invalid input produces clear messages; raw
  tracebacks never reach the user.
* **Honest language** — all output explicitly labels competencies as
  self-declared, not verified.
"""

from __future__ import annotations

from core.competency_analyzer import analyze_profile
from core.data_loader import load_learning_paths
from core.models import CompetencyAnalysis, LearnerProfile, Level, RecommendationType
from commands.desafio import load_challenges


# ---------------------------------------------------------------------------
# Internal formatting helpers
# ---------------------------------------------------------------------------


def _coverage_bar(index: float, width: int = 20) -> str:
    """Return a simple ASCII progress bar for *index* (0.0–1.0)."""
    filled = round(index * width)
    return "[" + "█" * filled + "░" * (width - filled) + "]"


def _format_analysis(analysis: CompetencyAnalysis) -> str:
    """Render a single :class:`~core.models.CompetencyAnalysis` as a string.

    All competency names use their original casing from the source data.
    Language explicitly labels competencies as self-declared.
    """
    lines: list[str] = []
    path = analysis.path
    pct = analysis.coverage_index * 100
    n_matched = len(analysis.matched_competencies)
    n_total = len(path.competencies)

    lines.append(f"  Trilha  : {path.title} ({path.level.value})")
    lines.append(f"  Tecnol. : {path.technology}")
    lines.append("")
    lines.append(
        f"  Índice de cobertura declarada : "
        f"{pct:.1f}%  {_coverage_bar(analysis.coverage_index)}  "
        f"({n_matched} de {n_total} competências)"
    )
    lines.append(
        "  ⚠  Este índice reflete competências auto-declaradas, "
        "não verificadas por evidências práticas."
    )

    # --- Matched ---
    lines.append("")
    if analysis.matched_competencies:
        lines.append(
            f"  ✔  Competências declaradas que correspondem à trilha "
            f"({len(analysis.matched_competencies)}):"
        )
        for c in analysis.matched_competencies:
            lines.append(f"       - {c}")
    else:
        lines.append("  ✔  Nenhuma competência declarada corresponde a esta trilha.")

    # --- Missing ---
    lines.append("")
    if analysis.missing_competencies:
        lines.append(
            f"  ✗  Competências da trilha não declaradas no perfil "
            f"({len(analysis.missing_competencies)}):"
        )
        # Build a quick priority lookup: competency name → priority
        prio_map = {
            r.competencies_to_develop[0]: r.priority
            for r in analysis.recommendations
        }
        for c in analysis.missing_competencies:
            prio = prio_map.get(c, "?")
            lines.append(f"       - {c}  [Prioridade {prio}]")
    else:
        lines.append(
            "  ✗  Nenhuma competência ausente — perfil cobre toda a trilha!"
        )

    # --- Extra ---
    if analysis.extra_competencies:
        lines.append("")
        lines.append(
            f"  ➕  Competências declaradas além do escopo desta trilha "
            f"({len(analysis.extra_competencies)}):"
        )
        for c in analysis.extra_competencies:
            lines.append(f"       - {c}")

    # --- Recommendations ---
    lines.append("")
    if analysis.recommendations:
        lines.append(
            f"  Próximos passos recomendados "
            f"({len(analysis.recommendations)} recomendações, por prioridade):"
        )
        for i, rec in enumerate(analysis.recommendations, start=1):
            comp = rec.competencies_to_develop[0]
            type_label = (
                "Trilha" if rec.recommendation_type == RecommendationType.LEARNING_PATH
                else "Desafio"
            )
            lines.append("")
            lines.append(
                f"    {i}. [Prioridade {rec.priority}] [{type_label}] "
                f"→ {rec.target_id}"
            )
            lines.append(f"       Competência : {comp}")
            # Wrap rationale at ~70 chars per line, indented
            words = rec.rationale.split()
            current_line = "       "
            for word in words:
                if len(current_line) + len(word) + 1 > 78:
                    lines.append(current_line.rstrip())
                    current_line = "       " + word + " "
                else:
                    current_line += word + " "
            if current_line.strip():
                lines.append(current_line.rstrip())
    else:
        lines.append("  Nenhuma recomendação — perfil cobre toda a trilha.")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Public command
# ---------------------------------------------------------------------------


def show_competency_analysis(profile_data: dict) -> None:
    """Run a competency analysis and print the results to standard output.

    This function is the single entry point for the ``analise`` command.
    It accepts a plain dict so that it can be called both from the
    interactive CLI (which builds the dict from user input) and directly
    from tests (which pass a pre-built dict).

    Parameters
    ----------
    profile_data:
        A dict with the following keys:

        * ``"id"``                      (str)
        * ``"name"``                    (str | None)
        * ``"current_competencies"``    (list[str])
        * ``"current_level"``           (Level)
        * ``"professional_goal"``       (str)
        * ``"technologies_of_interest"`` (list[str], may be empty)
        * ``"notes"``                   (str, may be empty)

    All keys are required.  Validation is the caller's responsibility.
    """
    profile = LearnerProfile(
        id=profile_data["id"],
        name=profile_data.get("name"),
        current_competencies=profile_data["current_competencies"],
        current_level=profile_data["current_level"],
        professional_goal=profile_data["professional_goal"],
        technologies_of_interest=profile_data.get("technologies_of_interest", []),
        notes=profile_data.get("notes", ""),
    )

    paths = load_learning_paths()
    challenges = load_challenges()
    results = analyze_profile(profile, paths, challenges)

    # Header
    name_display = profile.name or profile.id
    print()
    print("=" * 62)
    print(f"  Análise de Competências — {name_display}")
    print("=" * 62)
    if profile.professional_goal:
        print(f"  Objetivo : {profile.professional_goal}")
    print(f"  Nível    : {profile.current_level.value}")
    print()

    if not results:
        print(
            "  Nenhuma trilha encontrada para as tecnologias de interesse "
            "informadas."
        )
        return

    for idx, analysis in enumerate(results):
        if idx > 0:
            print()
            print("  " + "-" * 58)
        print(_format_analysis(analysis))
