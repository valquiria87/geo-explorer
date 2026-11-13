"""
Geo-Explorer — Intelligent Career Navigator
Entry point of the application.

Etapa 10 — CLI integration of four commands:
  1. Learning path (trilha de aprendizagem)
  2. Practical challenge (desafio prático)
  3. Fictional certificate (certificado fictício)
  4. Competency analysis (análise de competências)
"""

from __future__ import annotations

from core.models import Level
from commands.trilha import show_learning_path
from commands.desafio import generate_challenge
from commands.certificado import generate_certificate
from commands.analise import show_competency_analysis


# ---------------------------------------------------------------------------
# Level helpers
# ---------------------------------------------------------------------------

_LEVEL_MAP: dict[str, Level] = {level.value: level for level in Level}
_VALID_LEVELS = ", ".join(_LEVEL_MAP.keys())


def _parse_level(raw: str) -> Level | None:
    """Convert a user-supplied string to a :class:`Level`, or return ``None``."""
    return _LEVEL_MAP.get(raw.strip().lower())


# ---------------------------------------------------------------------------
# Input helpers
# ---------------------------------------------------------------------------

def _prompt(message: str) -> str:
    """Read a line from stdin and strip surrounding whitespace."""
    return input(message).strip()


def _prompt_required(message: str) -> str | None:
    """Prompt until the user provides a non-empty value, or types 'cancelar'.

    Returns the non-empty value, or ``None`` if the user typed 'cancelar'.
    """
    while True:
        value = _prompt(message)
        if value.lower() == "cancelar":
            return None
        if value:
            return value
        print("  Entrada inválida: o campo não pode estar vazio. "
              "Digite 'cancelar' para voltar ao menu.")


# ---------------------------------------------------------------------------
# Menu options
# ---------------------------------------------------------------------------

def _menu_trilha() -> None:
    """Option 1 — show a learning path."""
    print("\n--- Consultar Trilha de Aprendizagem ---")
    technology = _prompt_required("Tecnologia (ex: Python, n8n, AI Agents): ")
    if technology is None:
        print("Operação cancelada.")
        return
    print()
    show_learning_path(technology)


def _menu_desafio() -> None:
    """Option 2 — generate a practical challenge."""
    print("\n--- Gerar Desafio Prático ---")

    technology = _prompt_required("Tecnologia (ex: Python, n8n, AI Agents): ")
    if technology is None:
        print("Operação cancelada.")
        return

    level: Level | None = None
    while level is None:
        raw_level = _prompt(
            f"Nível ({_VALID_LEVELS}): "
        )
        if raw_level.lower() == "cancelar":
            print("Operação cancelada.")
            return
        level = _parse_level(raw_level)
        if level is None:
            print(f"  Nível inválido: '{raw_level}'. "
                  f"Valores aceitos: {_VALID_LEVELS}. "
                  "Digite 'cancelar' para voltar ao menu.")

    print()
    generate_challenge(technology, level)


def _menu_certificado() -> None:
    """Option 3 — generate a fictional certificate."""
    print("\n--- Gerar Certificado Fictício ---")

    participant = _prompt_required("Nome do participante: ")
    if participant is None:
        print("Operação cancelada.")
        return

    activity = _prompt_required("Nome da atividade concluída: ")
    if activity is None:
        print("Operação cancelada.")
        return

    technology = _prompt_required("Tecnologia principal (ex: Python): ")
    if technology is None:
        print("Operação cancelada.")
        return

    level_str: str | None = None
    while level_str is None:
        raw_level = _prompt(
            f"Nível ({_VALID_LEVELS}): "
        )
        if raw_level.lower() == "cancelar":
            print("Operação cancelada.")
            return
        if _parse_level(raw_level) is not None:
            level_str = raw_level.strip().lower()
        else:
            print(f"  Nível inválido: '{raw_level}'. "
                  f"Valores aceitos: {_VALID_LEVELS}. "
                  "Digite 'cancelar' para voltar ao menu.")

    raw_competencies = _prompt(
        "Competências desenvolvidas (separadas por vírgula, pode deixar vazio): "
    )
    competencies = (
        [c.strip() for c in raw_competencies.split(",") if c.strip()]
        if raw_competencies
        else []
    )

    print()
    try:
        generate_certificate(
            participant=participant,
            activity=activity,
            technology=technology,
            level=level_str,
            competencies=competencies,
        )
    except ValueError as exc:
        print(f"Erro ao gerar certificado: {exc}")


# ---------------------------------------------------------------------------
# Main menu loop
# ---------------------------------------------------------------------------

def _menu_analise() -> None:
    """Option 4 — competency analysis."""
    print("\n--- Analisar Competências do Aprendiz ---")

    name = _prompt("Seu nome (pode deixar vazio): ")

    raw_competencies = _prompt(
        "Competências que você já possui (separadas por vírgula): "
    )
    competencies = (
        [c.strip() for c in raw_competencies.split(",") if c.strip()]
        if raw_competencies
        else []
    )

    level: Level | None = None
    while level is None:
        raw_level = _prompt(f"Seu nível atual ({_VALID_LEVELS}): ")
        if raw_level.lower() == "cancelar":
            print("Operação cancelada.")
            return
        level = _parse_level(raw_level)
        if level is None:
            print(
                f"  Nível inválido: '{raw_level}'. "
                f"Valores aceitos: {_VALID_LEVELS}. "
                "Digite 'cancelar' para voltar ao menu."
            )

    goal = _prompt("Objetivo profissional (ex: Tornar-me desenvolvedor backend): ")

    raw_interests = _prompt(
        "Tecnologias de interesse (separadas por vírgula, deixe vazio para analisar todas): "
    )
    interests = (
        [t.strip() for t in raw_interests.split(",") if t.strip()]
        if raw_interests
        else []
    )

    profile_data = {
        "id": "learner-cli",
        "name": name if name else None,
        "current_competencies": competencies,
        "current_level": level,
        "professional_goal": goal,
        "technologies_of_interest": interests,
        "notes": "",
    }

    show_competency_analysis(profile_data)


_MENU = """
============================================================
  Geo-Explorer — Navegador Inteligente de Carreira
============================================================
  1. Consultar trilha de aprendizagem
  2. Gerar desafio prático
  3. Gerar certificado fictício
  4. Analisar competências
  5. Sair
------------------------------------------------------------"""

_HANDLERS = {
    "1": _menu_trilha,
    "2": _menu_desafio,
    "3": _menu_certificado,
    "4": _menu_analise,
}


def main() -> None:
    """Bootstrap and dispatch CLI commands."""
    while True:
        print(_MENU)
        choice = _prompt("Escolha uma opção [1-5]: ")

        if choice == "5":
            print("\nAté logo!")
            break

        handler = _HANDLERS.get(choice)
        if handler is None:
            print(f"\nOpção inválida: '{choice}'. Por favor, escolha entre 1 e 5.")
            continue

        try:
            handler()
        except KeyboardInterrupt:
            print("\n\n(Interrompido pelo usuário. Voltando ao menu...)")
        except Exception as exc:  # noqa: BLE001
            print(f"\nErro inesperado: {exc}")

        print()  # blank line before next menu render


if __name__ == "__main__":
    main()
