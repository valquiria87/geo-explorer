"""
Geo-Explorer — Ponto de Entrada da Interface Web (Streamlit)
"""
from __future__ import annotations

import sys
from pathlib import Path

# Adiciona a raiz do projeto ao sys.path para garantir que todos os módulos
# (gui, core, commands, data) sejam importados sem erros na nuvem.
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Carrega e executa a aplicação do Streamlit
from gui.app import *
