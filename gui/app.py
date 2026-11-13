"""
gui/app.py
----------
Geo-Explorer — Graphical Interface Entry Point (Etapa 12.2)

Entry point for the Streamlit GUI. Delegates rendering to page modules
routed by the sidebar navigation component.

Run with:
    streamlit run gui/app.py
"""

from __future__ import annotations

import streamlit as st

from gui.components.sidebar import render_sidebar
from gui.pages import analise, certificado, desafio, home, trilhas

# ---------------------------------------------------------------------------
# Page configuration — must be the first Streamlit call in the script
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Geo-Explorer",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Navigation + routing
# ---------------------------------------------------------------------------

page = render_sidebar()

if page == "home":
    home.render()
elif page == "trilhas":
    trilhas.render()
elif page == "desafio":
    desafio.render()
elif page == "certificado":
    certificado.render()
elif page == "analise":
    analise.render()
