"""
gui/pages/desafio.py
--------------------
Geo-Explorer — Practical Challenge page.

Loads and filters existing challenges through the command-layer helpers,
then renders the selected Challenge model without using CLI output.
"""

from __future__ import annotations

import streamlit as st

from commands.desafio import filter_challenges, load_challenges
from core.models import Challenge, Level


_LEVEL_LABELS: dict[Level, str] = {
    Level.BEGINNER: "Iniciante",
    Level.INTERMEDIATE: "Intermediário",
    Level.ADVANCED: "Avançado",
}
_GENERATED_CHALLENGE_KEY = "gui_generated_challenge_id"


def _load_challenges() -> list[Challenge] | None:
    """Load challenges and display a user-facing message on expected errors."""
    try:
        return load_challenges()
    except FileNotFoundError:
        st.error(
            "Arquivo de desafios não encontrado. "
            "Verifique se `data/challenges.json` existe."
        )
    except (ValueError, OSError) as exc:
        st.error(f"Não foi possível carregar os desafios. Detalhes: {exc}")
    return None


def _render_challenge(challenge: Challenge) -> None:
    st.divider()
    st.markdown(f"## {challenge.title}")
    st.markdown(f"**Tecnologia:** {challenge.technology}")
    st.markdown(f"**Nível:** {_LEVEL_LABELS.get(challenge.level, challenge.level.value)}")
    estimated_time = (
        f"{challenge.estimated_hours:g} horas"
        if challenge.estimated_hours is not None
        else "Não informado"
    )
    st.markdown(f"**Tempo estimado:** {estimated_time}")

    st.markdown("### Descrição")
    st.markdown(challenge.description)

    st.markdown(f"### Competências avaliadas ({len(challenge.competencies_assessed)})")
    for competency in challenge.competencies_assessed:
        st.markdown(f"- {competency}")

    st.markdown(f"### Critérios de avaliação ({len(challenge.evaluation_criteria)})")
    for criterion in challenge.evaluation_criteria:
        st.markdown(f"- {criterion}")


def render() -> None:
    """Render the practical challenge page."""
    st.title("🎯 Desafio Prático")
    st.markdown(
        "Escolha uma tecnologia e um nível para explorar os desafios disponíveis."
    )

    challenges = _load_challenges()
    if challenges is None:
        return
    if not challenges:
        st.info("Nenhum desafio está disponível no momento.")
        return

    technologies = sorted({challenge.technology for challenge in challenges})
    if not technologies:
        st.info("Nenhum desafio está disponível no momento.")
        return

    technology = st.selectbox(
        "Tecnologia",
        options=technologies,
        key="challenge_technology",
    )
    level = st.selectbox(
        "Nível",
        options=list(Level),
        format_func=lambda value: _LEVEL_LABELS[value],
        key="challenge_level",
    )
    matches = filter_challenges(technology, level, challenges)
    if not matches:
        st.info("Não há desafios disponíveis para essa tecnologia e nível.")
        return

    selected_challenge = st.selectbox(
        "Desafio disponível",
        options=matches,
        format_func=lambda challenge: challenge.title,
        key="challenge_selection",
    )

    if st.button("Exibir desafio", type="primary", key="show_challenge"):
        st.session_state[_GENERATED_CHALLENGE_KEY] = selected_challenge.id

    generated_id = st.session_state.get(_GENERATED_CHALLENGE_KEY)
    if generated_id != selected_challenge.id:
        return

    _render_challenge(selected_challenge)
