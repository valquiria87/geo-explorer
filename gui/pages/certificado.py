"""
gui/pages/certificado.py
------------------------
Geo-Explorer — fictional certificate page.

Builds certificate data through commands.certificado.build_certificate and
renders it in the GUI without invoking CLI presentation or export features.
"""

from __future__ import annotations

import streamlit as st

from commands.certificado import DISCLAIMER, build_certificate
from core.data_loader import load_learning_paths
from core.models import Level


_LEVEL_LABELS: dict[Level, str] = {
    Level.BEGINNER: "Iniciante",
    Level.INTERMEDIATE: "Intermediário",
    Level.ADVANCED: "Avançado",
}
_CERTIFICATE_STATE_KEY = "gui_generated_certificate"


def _parse_competencies(value: str) -> list[str]:
    return [line.strip() for line in value.splitlines() if line.strip()]


def _render_certificate(certificate: dict) -> None:
    st.divider()
    st.warning(certificate["disclaimer"])
    st.markdown("## Registro de Trilha e Competências Associadas")
    st.markdown(f"**Identificador:** `{certificate['id']}`")
    st.markdown(f"**Participante:** {certificate['participant']}")
    st.markdown(f"**Atividade:** {certificate['activity']}")
    st.markdown(f"**Tecnologia:** {certificate['technology']}")
    st.markdown(f"**Nível:** {_LEVEL_LABELS.get(certificate['level'], certificate['level'])}")
    st.markdown(
        f"**Data de emissão:** {certificate['issued_on'].strftime('%d/%m/%Y')}"
    )

    st.markdown("### Competências associadas à atividade")
    if certificate["competencies"]:
        for competency in certificate["competencies"]:
            st.markdown(f"- {competency}")
    else:
        st.markdown("Nenhuma competência informada.")

    st.markdown(certificate["recognition"])


def render() -> None:
    """Render the fictional certificate form and any generated certificate."""
    st.title("🏅 Certificado")
    st.markdown(
        "Selecione uma trilha do catálogo para gerar um certificado fictício. "
        "O documento registra a trilha escolhida e as competências associadas. "
        "Competências personalizadas são informadas pela pessoa e são "
        "autodeclaradas; se o campo ficar vazio, são usadas as competências do "
        "catálogo. O Geo-Explorer "
        "não acompanha nem valida a conclusão de trilhas ou desafios, e as "
        "competências associadas não foram verificadas. "
        "O certificado não possui validade oficial."
    )

    try:
        paths = load_learning_paths()
    except Exception as exc:
        st.error(f"Não foi possível carregar o catálogo de trilhas: {exc}")
        return
    if not paths:
        st.error("Nenhuma trilha disponível no catálogo para gerar um registro.")
        return

    with st.form("certificate_form"):
        participant = st.text_input("Participante")
        # Load catalog and allow user to select an activity (learning path) via selectbox
        # Prepare options as "title (technology – level)"
        options = []
        path_map = {}
        for lp in paths:
            label = f"{lp.title} ({lp.technology} – {_LEVEL_LABELS.get(lp.level, lp.level)})"
            options.append(label)
            path_map[label] = lp
        selected_label = st.selectbox("Atividade (trilha de aprendizado)", options, format_func=lambda x: x)
        selected_path = path_map.get(selected_label)
        # Auto-fill fields based on selected path
        activity = selected_path.title if selected_path else ""
        technology = selected_path.technology if selected_path else ""
        level = selected_path.level  # level enum
        # Override the level selectbox with the path's level (read-only display)
        # We'll hide the level selector and show the label
        st.markdown(f"**Tecnologia:** {technology}")
        st.markdown(f"**Nível:** {_LEVEL_LABELS.get(level, level)}")


        competencies_text = st.text_area(
            "Competências associadas à atividade",
            help=(
                "Competências personalizadas são informadas pela pessoa, uma "
                "por linha, e são autodeclaradas. Para usar as competências da "
                "trilha selecionada, deixe vazio."
            ),
        )
        submitted = st.form_submit_button("Gerar certificado", type="primary")

    if submitted:
        st.session_state.pop(_CERTIFICATE_STATE_KEY, None)
        if not technology.strip():
            st.error("Informe a tecnologia da atividade.")
        else:
            try:
                certificate = build_certificate(
                    participant=participant,
                    activity=activity,
                    technology=technology.strip(),
                    level=level.value,
                    competencies=_parse_competencies(competencies_text),
                    paths=paths,
                )
            except ValueError as exc:
                st.error(f"Não foi possível gerar o certificado. {exc}")
            else:
                st.session_state[_CERTIFICATE_STATE_KEY] = certificate

    certificate = st.session_state.get(_CERTIFICATE_STATE_KEY)
    if certificate is not None:
        _render_certificate(certificate)
