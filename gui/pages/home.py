"""
gui/pages/home.py
------------------
Geo-Explorer — Home / presentation page.

Renders a professional portfolio-ready overview of the project.
Contains no business logic — purely presentational.

Public API
----------
render() -> None
    Renders the home page content into the current Streamlit context.
"""

from __future__ import annotations

import streamlit as st


def render() -> None:
    """Render the Geo-Explorer home / presentation page."""

    # ── Hero ────────────────────────────────────────────────────────────────
    st.title("🌍 Geo-Explorer")
    st.subheader(
        "Navegador Inteligente de Aprendizagem e Desenvolvimento de Competências"
    )

    st.markdown(
        """
        Identifique lacunas de conhecimento, siga trilhas estruturadas e
        acompanhe sua evolução técnica — tudo em um único ambiente.
        """
    )

    st.divider()

    # ── What is Geo-Explorer ─────────────────────────────────────────────────
    st.markdown("### O que é o Geo-Explorer?")
    st.markdown(
        """
        O **Geo-Explorer** é uma plataforma de aprendizagem estruturada que
        mapeia competências técnicas, sugere trilhas de estudo e desafios
        práticos, e emite certificados fictícios de conclusão.

        O projeto utiliza Python como linguagem principal e possui
        dependências externas, incluindo Streamlit e o SDK MCP. Também foi
        desenvolvido com ênfase em design de domínio limpo, cobertura de testes
        e arquitetura extensível — incluindo uma interface de linha de comando
        completa e um servidor MCP para integração com agentes de IA.
        """
    )

    st.divider()

    # ── Feature cards (2 × 2 grid) ───────────────────────────────────────────
    st.markdown("### Funcionalidades")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(
            """
            #### 🗺️ Trilhas de Aprendizagem
            Explore trilhas estruturadas por tecnologia e nível.
            Cada trilha detalha etapas sequenciais e as competências
            desenvolvidas em cada passo.
            """
        )
        if st.button("Explorar Trilhas →", key="home_go_trilhas", type="primary"):
            st.session_state["current_page"] = "trilhas"
            st.rerun()

    with col2:
        st.markdown(
            """
            #### 🎯 Desafio Prático
            Receba um desafio personalizado para consolidar conhecimentos.
            Inclui critérios de avaliação e competências avaliadas.
            """
        )
        if st.button("Explorar Desafio →", key="home_go_desafio"):
            st.session_state["current_page"] = "desafio"
            st.rerun()

    col3, col4 = st.columns(2)

    with col3:
        st.markdown(
            """
            #### 📊 Análise de Competências
            Declare suas competências atuais e receba uma análise
            priorizada das lacunas em relação às trilhas disponíveis.
            """
        )
        if st.button("Analisar Competências →", key="home_go_analise"):
            st.session_state["current_page"] = "analise"
            st.rerun()

    with col4:
        st.markdown(
            """
            #### 🏅 Certificado
            Gere um certificado fictício ao concluir uma atividade.
            Inclui disclaimer explícito de não-validade oficial.
            """
        )
        if st.button("Gerar Certificado →", key="home_go_certificado"):
            st.session_state["current_page"] = "certificado"
            st.rerun()

    st.divider()

    # ── Technical stack ──────────────────────────────────────────────────────
    st.markdown("### Stack Técnica")

    tc1, tc2, tc3, tc4 = st.columns(4)
    with tc1:
        st.metric(label="Linguagem", value="Python 3.15")
    with tc2:
        st.metric(label="Interface", value="Streamlit 1.67")
    with tc3:
        st.metric(label="Protocolo IA", value="MCP 2.x")
    with tc4:
        st.metric(label="Testes", value="Automatizados")

    st.divider()

    # ── Footer ───────────────────────────────────────────────────────────────
    st.caption(
        "Geo-Explorer é um projeto de portfólio. "
        "Os certificados gerados são fictícios e não possuem validade oficial."
    )
