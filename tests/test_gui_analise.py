from pathlib import Path
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

from gui.pages import analise


_APP_PATH = Path(__file__).resolve().parents[1] / "gui" / "app.py"


def test_analysis_page_submits_profile_and_renders_core_results():
    app = AppTest.from_file(str(_APP_PATH)).run()
    app.button(key="nav_analise").click().run()
    assert not app.exception

    app.text_input(key="analysis_name").set_value("Ana Lima")
    app.text_area(key="analysis_professional_goal").set_value(
        "Tornar-se desenvolvedora backend"
    )
    app.multiselect(key="analysis_technologies").set_value(["Python"])
    app.text_area(key="analysis_competencies").set_value(
        "Python syntax and semantics\ncontrol flow"
    )
    app.button(key="analysis_submit").click().run()

    assert not app.exception
    profile = app.session_state["geo_explorer_analysis_profile"]
    results = app.session_state["geo_explorer_analysis_results"]
    assert profile.name == "Ana Lima"
    assert profile.professional_goal == "Tornar-se desenvolvedora backend"
    assert profile.technologies_of_interest == ["Python"]
    assert profile.current_competencies == [
        "Python syntax and semantics",
        "control flow",
    ]
    assert len(results) == 1
    assert results[0].path.technology == "Python"
    assert any("autodeclaradas" in item.value for item in app.info)
    assert any("Índice de cobertura declarada" in item.label for item in app.metric)


def test_empty_technology_selection_analyzes_every_path_and_survives_navigation():
    app = AppTest.from_file(str(_APP_PATH)).run()
    app.button(key="home_go_analise").click().run()
    assert not app.exception

    app.button(key="analysis_submit").click().run()
    assert not app.exception
    results = app.session_state["geo_explorer_analysis_results"]
    assert len(results) > 1

    profile_id = app.session_state["geo_explorer_analysis_profile_id"]
    app.button(key="nav_home").click().run()
    app.button(key="nav_analise").click().run()
    assert not app.exception
    assert app.session_state["geo_explorer_analysis_profile_id"] == profile_id
    assert len(app.session_state["geo_explorer_analysis_results"]) == len(results)


def test_recommendations_are_rendered_in_the_core_order():
    app = AppTest.from_file(str(_APP_PATH)).run()
    app.button(key="nav_analise").click().run()
    app.multiselect(key="analysis_technologies").set_value(["Python"])
    app.button(key="analysis_submit").click().run()
    assert not app.exception

    recommendations = app.session_state["geo_explorer_analysis_results"][0].recommendations
    expected_labels = [
        f"{index}. Prioridade {recommendation.priority}/5 — "
        f"{', '.join(recommendation.competencies_to_develop)}"
        for index, recommendation in enumerate(recommendations, start=1)
    ]
    assert [item.label for item in app.expander] == expected_labels


def test_missing_competencies_and_recommendation_details_are_rendered():
    app = AppTest.from_file(str(_APP_PATH)).run()
    app.button(key="nav_analise").click().run()
    app.multiselect(key="analysis_technologies").set_value(["Python"])
    app.button(key="analysis_submit").click().run()
    assert not app.exception

    analysis = app.session_state["geo_explorer_analysis_results"][0]
    assert analysis.missing_competencies
    rendered = "\n".join(item.value for item in app.markdown)
    assert "Lacunas identificadas" in rendered
    for competency in analysis.missing_competencies:
        assert competency in rendered

    recommendation = analysis.recommendations[0]
    first_recommendation = app.expander[0]
    recommendation_content = "\n".join(
        item.value for item in first_recommendation.markdown
    )
    assert recommendation.rationale in recommendation_content
    assert recommendation.target_id in recommendation_content


def test_empty_path_data_shows_message_without_form():
    with (
        patch.object(analise, "_load_analysis_data", return_value=([], [])),
        patch.object(analise.st, "title"),
        patch.object(analise.st, "markdown"),
        patch.object(analise.st, "info") as info,
        patch.object(
            analise.st,
            "form",
            side_effect=AssertionError("The form must not be rendered"),
        ),
    ):
        analise.render()

    assert "Nenhuma trilha de aprendizagem está disponível para análise." in [
        call.args[0] for call in info.call_args_list
    ]


def test_missing_learning_path_file_is_reported():
    with (
        patch.object(
            analise,
            "load_learning_paths",
            side_effect=FileNotFoundError("missing"),
        ),
        patch.object(analise.st, "error") as error,
    ):
        result = analise._load_analysis_data()

    assert result is None
    error.assert_called_once()
    assert "Arquivo de trilhas não encontrado" in error.call_args.args[0]


def test_invalid_challenge_data_is_reported():
    with (
        patch.object(analise, "load_learning_paths", return_value=[]),
        patch.object(
            analise,
            "load_challenges",
            side_effect=ValueError("invalid data"),
        ),
        patch.object(analise.st, "error") as error,
    ):
        result = analise._load_analysis_data()

    assert result is None
    error.assert_called_once()
    assert "Não foi possível carregar os desafios" in error.call_args.args[0]
