"""
gui/components/sidebar.py
--------------------------
Reusable sidebar navigation for Geo-Explorer.

Renders the lateral menu and keeps the active page in
``st.session_state["current_page"]``.

Public API
----------
render_sidebar() -> str
    Renders the sidebar and returns the identifier of the active page.
"""

from __future__ import annotations

import streamlit as st

# ---------------------------------------------------------------------------
# Page registry
# ---------------------------------------------------------------------------

# Pages that are fully implemented and navigable.
_ACTIVE_PAGES: dict[str, str] = {
    "home":        "🏠 Início",
    "trilhas":     "🗺️ Trilhas de Aprendizagem",
    "desafio":     "🎯 Desafio Prático",
    "certificado": "🏅 Certificado",
    "analise":     "📊 Análise de Competências",
}

# Pages not yet implemented — displayed as disabled labels.
_COMING_SOON: list[str] = []

_DEFAULT_PAGE = "home"


# ---------------------------------------------------------------------------
# Public function
# ---------------------------------------------------------------------------

def render_sidebar() -> str:
    """Render the sidebar navigation and return the active page identifier.

    Updates ``st.session_state["current_page"]`` when the user clicks a
    navigation button, then returns the current value of that key.

    Returns
    -------
    str
        One of the keys defined in ``_ACTIVE_PAGES`` (e.g. ``"home"`` or
        ``"trilhas"``).
    """
    # Initialise session state on first run.
    if "current_page" not in st.session_state:
        st.session_state["current_page"] = _DEFAULT_PAGE

    with st.sidebar:
        st.markdown("## 🌍 Geo-Explorer")
        st.caption("Navegador Inteligente de Aprendizagem")
        st.divider()

        st.markdown("**Navegação**")

        # Active navigation buttons — one per implemented page.
        for page_id, label in _ACTIVE_PAGES.items():
            # Highlight the currently active page.
            button_type = (
                "primary"
                if st.session_state["current_page"] == page_id
                else "secondary"
            )
            if st.button(label, key=f"nav_{page_id}", use_container_width=True, type=button_type):
                st.session_state["current_page"] = page_id

        # Coming-soon entries — rendered as disabled buttons.
        for label in _COMING_SOON:
            st.button(
                f"{label} — Em breve",
                disabled=True,
                use_container_width=True,
            )

        st.divider()
        st.caption("Geo-Explorer · Etapa 12.2")

    return st.session_state["current_page"]
