"""
gui/pages/analise.py
--------------------
Geo-Explorer — competency analysis page.

Collects a learner profile and renders the analysis returned by the core
business-logic layer.
"""

from __future__ import annotations

from uuid import uuid4

import streamlit as st

from commands.desafio import load_challenges
from core.competency_analyzer import analyze_profile
from core.data_loader import load_learning_paths
from core.models import (
    Challenge,
    CompetencyAnalysis,
    LearnerProfile,
    LearningPath,
    Level,
    Recommendation,
    RecommendationType,
)


_LEVEL_LABELS: dict[Level, str] = {
    Level.BEGINNER: "Iniciante",
    Level.INTERMEDIATE: "Intermediário",
    Level.ADVANCED: "Avançado",
}
_RECOMMENDATION_LABELS: dict[RecommendationType, str] = {
    RecommendationType.LEARNING_PATH: "Trilha de aprendizagem",
    RecommendationType.CHALLENGE: "Desafio prático",
    RecommendationType.COMPETENCY_REVIEW: "Revisão de competência",
}
_PROFILE_ID_KEY = "geo_explorer_analysis_profile_id"
_PROFILE_KEY = "geo_explorer_analysis_profile"
_RESULTS_KEY = "geo_explorer_analysis_results"
_DECLARATION_NOTICE = (
    "As competências informadas são autodeclaradas e não foram verificadas "
    "por evidências práticas."
)


def _load_analysis_data() -> tuple[list[LearningPath], list[Challenge]] | None:
    """Load the path and challenge data required by the analyzer."""
    try:
        paths = load_learning_paths()
    except FileNotFoundError:
        st.error(
            "Arquivo de trilhas não encontrado. "
            "Verifique se `data/learning_paths.json` existe."
        )
        return None
    except (OSError, ValueError) as exc:
        st.error(f"Não foi possível carregar as trilhas. Detalhes: {exc}")
        return None

    try:
        challenges = load_challenges()
    except FileNotFoundError:
        st.error(
            "Arquivo de desafios não encontrado. "
            "Verifique se `data/challenges.json` existe."
        )
        return None
    except (OSError, ValueError) as exc:
        st.error(f"Não foi possível carregar os desafios. Detalhes: {exc}")
        return None

    return paths, challenges


def _parse_competencies(value: str) -> list[str]:
    return [line.strip() for line in value.splitlines() if line.strip()]


def _recommendation_target(
    recommendation: Recommendation,
    paths_by_id: dict[str, LearningPath],
    challenges_by_id: dict[str, Challenge],
) -> str:
    """Resolve a recommendation's existing target ID to a display label."""
    if recommendation.recommendation_type == RecommendationType.LEARNING_PATH:
        target = paths_by_id.get(recommendation.target_id)
        if target is not None:
            return f"{target.title} ({target.id})"
    elif recommendation.recommendation_type == RecommendationType.CHALLENGE:
        target = challenges_by_id.get(recommendation.target_id)
        if target is not None:
            return f"{target.title} ({target.id})"
    return recommendation.target_id


def _render_analysis(
    profile: LearnerProfile,
    results: list[CompetencyAnalysis],
    paths: list[LearningPath],
    challenges: list[Challenge],
) -> None:
    st.subheader("Perfil analisado")
    st.markdown(f"**Nome:** {profile.name or 'Não informado'}")
    st.markdown(
        f"**Objetivo profissional:** "
        f"{profile.professional_goal or 'Não informado'}"
    )
    st.markdown(f"**Nível atual:** {_LEVEL_LABELS[profile.current_level]}")
    interests = (
        ", ".join(profile.technologies_of_interest)
        if profile.technologies_of_interest
        else "Todas as tecnologias"
    )
    st.markdown(f"**Tecnologias de interesse:** {interests}")

    st.markdown("**Competências declaradas:**")
    if profile.current_competencies:
        for competency in profile.current_competencies:
            st.markdown(f"- {competency}")
    else:
        st.caption("Nenhuma competência informada.")

    if not results:
        st.info("Nenhuma trilha encontrada para as tecnologias selecionadas.")
        return

    paths_by_id = {path.id: path for path in paths}
    challenges_by_id = {challenge.id: challenge for challenge in challenges}

    for analysis in results:
        path = analysis.path
        st.divider()
        st.markdown(f"## {path.title}")
        st.markdown(
            f"**Tecnologia:** {path.technology} · "
            f"**Nível da trilha:** {_LEVEL_LABELS[path.level]}"
        )

        percentage = analysis.coverage_index * 100
        st.metric("Índice de cobertura declarada", f"{percentage:.1f}%")
        st.progress(analysis.coverage_index)
        st.caption(
            f"{len(analysis.matched_competencies)} de "
            f"{len(path.competencies)} competências da trilha correspondem "
            "às competências declaradas."
        )
        st.info(_DECLARATION_NOTICE)

        st.markdown("### Competências correspondentes")
        if analysis.matched_competencies:
            for competency in analysis.matched_competencies:
                st.markdown(f"- {competency}")
        else:
            st.caption("Nenhuma competência declarada corresponde à trilha.")

        st.markdown("### Lacunas identificadas")
        if analysis.missing_competencies:
            for competency in analysis.missing_competencies:
                st.markdown(f"- {competency}")
        else:
            st.success("Nenhuma lacuna identificada para esta trilha.")

        if analysis.extra_competencies:
            st.markdown("### Competências fora do escopo desta trilha")
            for competency in analysis.extra_competencies:
                st.markdown(f"- {competency}")

        st.markdown("### Recomendações priorizadas")
        if not analysis.recommendations:
            st.caption("Nenhuma recomendação necessária para esta trilha.")
            continue

        for index, recommendation in enumerate(analysis.recommendations, start=1):
            competency = ", ".join(recommendation.competencies_to_develop)
            with st.expander(
                f"{index}. Prioridade {recommendation.priority}/5 — {competency}",
                expanded=False,
            ):
                recommendation_type = _RECOMMENDATION_LABELS.get(
                    recommendation.recommendation_type,
                    "Recomendação",
                )
                st.markdown(f"**Tipo:** {recommendation_type}")
                st.markdown(
                    "**Alvo:** "
                    + _recommendation_target(
                        recommendation, paths_by_id, challenges_by_id
                    )
                )
                st.markdown(recommendation.rationale)


def render() -> None:
    """Render the profile form and any analysis stored in this session."""
    st.title("📊 Análise de Competências")
    st.markdown(
        "Informe seu perfil para comparar suas competências declaradas "
        "com as trilhas de aprendizagem disponíveis."
    )
    st.info(_DECLARATION_NOTICE)

    loaded_data = _load_analysis_data()
    if loaded_data is None:
        return
    paths, challenges = loaded_data
    if not paths:
        st.info("Nenhuma trilha de aprendizagem está disponível para análise.")
        return

    technologies = sorted({path.technology for path in paths})
    st.caption(
        "Deixe as tecnologias de interesse sem seleção para analisar todas as trilhas."
    )

    with st.form("analysis_form"):
        name = st.text_input("Nome (opcional)", key="analysis_name")
        professional_goal = st.text_area(
            "Objetivo profissional",
            key="analysis_professional_goal",
        )
        current_level = st.selectbox(
            "Nível atual",
            options=list(Level),
            format_func=lambda level: _LEVEL_LABELS[level],
            key="analysis_current_level",
        )
        technologies_of_interest = st.multiselect(
            "Tecnologias de interesse",
            options=technologies,
            key="analysis_technologies",
        )
        competencies_text = st.text_area(
            "Competências que você já possui",
            help="Informe uma competência por linha.",
            key="analysis_competencies",
        )
        submitted = st.form_submit_button(
            "Analisar perfil",
            type="primary",
            key="analysis_submit",
        )

    if submitted:
        profile_id = st.session_state.get(_PROFILE_ID_KEY)
        if profile_id is None:
            profile_id = str(uuid4())
            st.session_state[_PROFILE_ID_KEY] = profile_id

        profile = LearnerProfile(
            id=profile_id,
            name=name.strip() or None,
            current_competencies=_parse_competencies(competencies_text),
            current_level=current_level,
            professional_goal=professional_goal.strip(),
            technologies_of_interest=list(technologies_of_interest),
        )
        st.session_state[_PROFILE_KEY] = profile
        st.session_state.pop(_RESULTS_KEY, None)
        st.session_state[_RESULTS_KEY] = analyze_profile(
            profile, paths, challenges
        )

    profile = st.session_state.get(_PROFILE_KEY)
    results = st.session_state.get(_RESULTS_KEY)
    if profile is not None and results is not None:
        _render_analysis(profile, results, paths, challenges)
