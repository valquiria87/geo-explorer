from pathlib import Path
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

from core.data_loader import load_learning_paths
from gui.pages import trilhas


_APP_PATH = Path(__file__).resolve().parents[1] / "gui" / "app.py"


def test_learning_path_selector_and_steps_use_existing_data_in_order():
    paths = load_learning_paths()
    expected_path = sorted(paths, key=lambda path: path.technology)[0]
    app = AppTest.from_file(str(_APP_PATH)).run()

    app.button(key="nav_trilhas").click().run()

    assert not app.exception
    selector = app.selectbox[0]
    assert selector.label == "Tecnologia / Trilha"
    assert selector.value == f"{expected_path.technology} — {expected_path.title}"

    markdown = "\n".join(item.value for item in app.markdown)
    assert expected_path.title in markdown
    assert expected_path.technology in markdown
    assert expected_path.description in markdown

    expected_steps = sorted(expected_path.steps, key=lambda step: step.order)
    actual_step_titles = [
        item.label.split(" — ", maxsplit=1)[-1]
        for item in app.expander
        if "Etapa " in item.label
    ]
    assert actual_step_titles == [step.title for step in expected_steps]

    if expected_steps:
        step = expected_steps[0]
        first_step_expander = next(
            item for item in app.expander if step.title in item.label
        )
        step_content = "\n".join(item.value for item in first_step_expander.markdown)
        assert step.description in step_content
        for competency in step.competencies_developed:
            assert competency in step_content


def test_empty_learning_path_list_shows_message_without_selector():
    with (
        patch.object(trilhas, "_load_paths", return_value=[]),
        patch.object(trilhas.st, "title"),
        patch.object(trilhas.st, "markdown"),
        patch.object(trilhas.st, "divider"),
        patch.object(trilhas.st, "info") as info,
        patch.object(
            trilhas.st,
            "selectbox",
            side_effect=AssertionError("A selector must not be rendered"),
        ),
    ):
        trilhas.render()

    info.assert_called_once_with(
        "Nenhuma trilha de aprendizagem está disponível no momento."
    )


def test_missing_learning_path_file_shows_error():
    with (
        patch.object(
            trilhas,
            "load_learning_paths",
            side_effect=FileNotFoundError("missing"),
        ),
        patch.object(trilhas.st, "error") as error,
    ):
        result = trilhas._load_paths()

    assert result is None
    error.assert_called_once()
    assert "Arquivo de trilhas não encontrado" in error.call_args.args[0]


def test_invalid_learning_path_data_shows_error():
    with (
        patch.object(
            trilhas,
            "load_learning_paths",
            side_effect=ValueError("invalid data"),
        ),
        patch.object(trilhas.st, "error") as error,
    ):
        result = trilhas._load_paths()

    assert result is None
    error.assert_called_once()
    assert "Não foi possível carregar as trilhas" in error.call_args.args[0]
