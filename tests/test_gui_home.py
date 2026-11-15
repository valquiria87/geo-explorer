from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest


_APP_PATH = Path(__file__).resolve().parents[1] / "gui" / "app.py"


def test_home_renders_four_feature_cards_and_active_buttons():
    app = AppTest.from_file(str(_APP_PATH)).run()

    assert not app.exception
    assert any("Geo-Explorer" in item.value for item in app.title)
    markdown = "\n".join(item.value for item in app.markdown)
    for feature in (
        "Trilhas de Aprendizagem",
        "Desafio Prático",
        "Análise de Competências",
        "Certificado",
    ):
        assert feature in markdown

    button_keys = {item.key for item in app.button}
    assert {
        "home_go_trilhas",
        "home_go_desafio",
        "home_go_analise",
        "home_go_certificado",
    } <= button_keys


def _home_text() -> str:
    app = AppTest.from_file(str(_APP_PATH)).run()
    assert not app.exception
    # Streamlit keeps source line breaks inside paragraphs; normalise whitespace.
    return " ".join(" ".join(item.value for item in app.markdown).split())


def test_home_does_not_promise_completion_or_progress_tracking():
    text = _home_text()

    for old_text in (
        "ao concluir",
        "de conclusão",
        "acompanhe sua evolução",
    ):
        assert old_text not in text


def test_home_describes_certificate_as_self_declared_record():
    text = _home_text()

    assert "a partir de uma trilha do catálogo" in text
    assert "competências autodeclaradas e não verificadas" in text
    assert "registram uma trilha do catálogo e competências autodeclaradas" in text
    assert "compare suas competências autodeclaradas" in text


@pytest.mark.parametrize(
    ("button_key", "page_title"),
    [
        ("home_go_trilhas", "Trilhas"),
        ("home_go_desafio", "Desafio"),
        ("home_go_analise", "Análise"),
        ("home_go_certificado", "Certificado"),
    ],
)
def test_home_feature_button_navigates_to_its_page(button_key, page_title):
    app = AppTest.from_file(str(_APP_PATH)).run()

    app.button(key=button_key).click().run()

    assert not app.exception
    assert any(page_title in item.value for item in app.title)


@pytest.mark.parametrize(
    ("page_key", "page_title"),
    [
        ("nav_home", "Geo-Explorer"),
        ("nav_trilhas", "Trilhas"),
        ("nav_desafio", "Desafio"),
        ("nav_certificado", "Certificado"),
        ("nav_analise", "Análise"),
    ],
)
def test_sidebar_navigation_routes_to_each_page(page_key, page_title):
    app = AppTest.from_file(str(_APP_PATH)).run()

    app.button(key=page_key).click().run()

    assert not app.exception
    assert any(page_title in item.value for item in app.title)
