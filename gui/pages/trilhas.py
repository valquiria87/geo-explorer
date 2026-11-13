"""
gui/pages/trilhas.py
---------------------
Geo-Explorer — Learning Paths page.

Loads learning paths from core, presents a technology selector, and
displays the selected path's steps and competencies.

No business rules are duplicated here — all data comes from
``core.data_loader.load_learning_paths()``.

Public API
----------
level_badge(level_value: str) -> str
    Returns a human-readable, colour-coded label for a Level value.
    Exposed as a pure function to simplify future unit tests.

render() -> None
    Renders the Learning Paths page into the current Streamlit context.
"""

from __future__ import annotations

import streamlit as st

from core.data_loader import load_learning_paths
from core.models import LearningPath


# ---------------------------------------------------------------------------
# Visual helper — pure function, no business logic
# ---------------------------------------------------------------------------

_LEVEL_BADGE: dict[str, str] = {
    "beginner":     "🟢 Iniciante",
    "intermediate": "🟡 Intermediário",
    "advanced":     "🔴 Avançado",
}


def level_badge(level_value: str) -> str:
    """Return a human-readable badge string for a Level enum value.

    Parameters
    ----------
    level_value:
        The string value of a :class:`~core.models.Level` member
        (e.g. ``"beginner"``).

    Returns
    -------
    str
        A labelled emoji string, or the raw value if unknown.
    """
    return _LEVEL_BADGE.get(level_value, level_value)


# ---------------------------------------------------------------------------
# Data loading with error handling
# ---------------------------------------------------------------------------

def _load_paths() -> list[LearningPath] | None:
    """Load learning paths and handle all expected I/O and format errors.

    Returns the list on success, or ``None`` after displaying a
    user-friendly error message via ``st.error``.
    """
    try:
        return load_learning_paths()
    except FileNotFoundError:
        st.error(
            "⚠️ Arquivo de trilhas não encontrado. "
            "Verifique se o arquivo `data/learning_paths.json` existe."
        )
    except (ValueError, OSError) as exc:
        st.error(
            f"⚠️ Não foi possível carregar as trilhas de aprendizagem. "
            f"Detalhes: {exc}"
        )
    return None


# ---------------------------------------------------------------------------
# Page render
# ---------------------------------------------------------------------------

def render() -> None:
    """Render the Learning Paths page."""

    st.title("🗺️ Trilhas de Aprendizagem")
    st.markdown(
        "Selecione uma tecnologia para explorar a trilha estruturada, "
        "as etapas de estudo e as competências desenvolvidas em cada passo."
    )
    st.divider()

    # Load data — abort gracefully on error.
    paths = _load_paths()
    if paths is None:
        return
    if not paths:
        st.info("Nenhuma trilha de aprendizagem está disponível no momento.")
        return

    # Build selector options: display label → LearningPath object.
    path_map: dict[str, LearningPath] = {
        f"{p.technology} — {p.title}": p
        for p in sorted(paths, key=lambda p: p.technology)
    }

    selected_label = st.selectbox(
        "Tecnologia / Trilha",
        options=list(path_map.keys()),
        help="Escolha a trilha que deseja explorar.",
    )

    path = path_map[selected_label]

    st.divider()

    # ── Path metadata ────────────────────────────────────────────────────────
    meta_col, badge_col = st.columns([4, 1])
    with meta_col:
        st.markdown(f"## {path.title}")
        st.markdown(f"**Tecnologia:** {path.technology}")
    with badge_col:
        st.space("small")
        st.markdown(f"**Nível:** {level_badge(path.level.value)}")

    if path.description:
        st.markdown(path.description)

    st.divider()

    # ── General competencies ─────────────────────────────────────────────────
    with st.expander(f"📋 Competências da trilha ({len(path.competencies)} no total)", expanded=False):
        for comp in path.competencies:
            st.markdown(f"- {comp}")

    st.divider()

    # ── Steps ────────────────────────────────────────────────────────────────
    st.markdown(f"### Etapas ({len(path.steps)})")

    for step in sorted(path.steps, key=lambda s: s.order):
        with st.expander(f"**Etapa {step.order}** — {step.title}", expanded=False):
            st.markdown(step.description)
            if step.competencies_developed:
                st.markdown("**Competências desenvolvidas nesta etapa:**")
                for comp in step.competencies_developed:
                    st.markdown(f"- {comp}")
