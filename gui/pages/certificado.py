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
    st.markdown("## Certificado de Conclusão")
    st.markdown(f"**Identificador:** `{certificate['id']}`")
    st.markdown(f"**Participante:** {certificate['participant']}")
    st.markdown(f"**Atividade:** {certificate['activity']}")
    st.markdown(f"**Tecnologia:** {certificate['technology']}")
    st.markdown(f"**Nível:** {_LEVEL_LABELS.get(certificate['level'], certificate['level'])}")
    st.markdown(
        f"**Data de emissão:** {certificate['issued_on'].strftime('%d/%m/%Y')}"
    )

    st.markdown("### Competências desenvolvidas")
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
        "Registre a conclusão de uma atividade. O certificado é fictício e "
        "não possui validade oficial."
    )

    with st.form("certificate_form"):
        participant = st.text_input("Participante")
        activity = st.text_input("Atividade")
        technology = st.text_input("Tecnologia")
        level = st.selectbox(
            "Nível",
            options=list(Level),
            format_func=lambda value: _LEVEL_LABELS[value],
        )
        competencies_text = st.text_area(
            "Competências desenvolvidas",
            help="Informe uma competência por linha. Este campo é opcional.",
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
                )
            except ValueError as exc:
                st.error(f"Não foi possível gerar o certificado. {exc}")
            else:
                st.session_state[_CERTIFICATE_STATE_KEY] = certificate

    certificate = st.session_state.get(_CERTIFICATE_STATE_KEY)
    if certificate is not None:
        _render_certificate(certificate)
