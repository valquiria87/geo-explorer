"""
Geo-Explorer — Streamlit Web Application Entry Point
"""
from __future__ import annotations

import sys
from pathlib import Path

# Garante que a raiz do projeto esteja no sys.path para carregar gui, core e data
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import streamlit as st

from gui.components.sidebar import render_sidebar
from gui.pages import analise, certificado, desafio, home, trilhas

# 1. Configuração da página (primeiro comando do Streamlit)
st.set_page_config(
    page_title="Geo-Explorer",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 2. Renderiza o menu lateral customizado e identifica a página ativa
page = render_sidebar()

# 3. Roteador de telas
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
