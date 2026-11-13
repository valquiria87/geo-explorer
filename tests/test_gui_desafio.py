from pathlib import Path
import unittest
from unittest.mock import patch

from commands.desafio import load_challenges
from core.models import Level
from gui.pages import desafio
from streamlit.testing.v1 import AppTest


_APP_PATH = Path(__file__).resolve().parents[1] / "gui" / "app.py"


class TestChallengePage(unittest.TestCase):
    def setUp(self):
        self.challenges = load_challenges()

    def test_empty_challenge_list_shows_message_without_selectors(self):
        with (
            patch.object(desafio, "_load_challenges", return_value=[]),
            patch.object(desafio.st, "title"),
            patch.object(desafio.st, "markdown"),
            patch.object(desafio.st, "info") as info,
            patch.object(
                desafio.st,
                "selectbox",
                side_effect=AssertionError("No selector should be rendered"),
            ),
        ):
            desafio.render()

        info.assert_called_once_with("Nenhum desafio está disponível no momento.")

    def test_filtered_challenge_is_rendered_after_selection(self):
        challenge = next(
            item
            for item in self.challenges
            if item.technology == "Python" and item.level == Level.BEGINNER
        )
        session_state = {}

        def select_option(label, options, **kwargs):
            if label == "Tecnologia":
                return "Python"
            if label == "Nível":
                return Level.BEGINNER
            if label == "Desafio disponível":
                self.assertIn(challenge, options)
                return challenge
            raise AssertionError(f"Unexpected selector: {label}")

        with (
            patch.object(desafio, "_load_challenges", return_value=self.challenges),
            patch.object(desafio.st, "title"),
            patch.object(desafio.st, "markdown") as markdown,
            patch.object(desafio.st, "divider"),
            patch.object(desafio.st, "selectbox", side_effect=select_option),
            patch.object(desafio.st, "button", return_value=True),
            patch.object(desafio.st, "session_state", session_state),
        ):
            desafio.render()

        rendered_text = "\n".join(str(call.args[0]) for call in markdown.call_args_list)
        self.assertIn(challenge.title, rendered_text)
        self.assertIn(f"**Tecnologia:** {challenge.technology}", rendered_text)
        self.assertIn("**Nível:** Iniciante", rendered_text)
        self.assertIn(
            f"**Tempo estimado:** {challenge.estimated_hours:g} horas",
            rendered_text,
        )
        self.assertIn(challenge.description, rendered_text)
        self.assertIn("Competências avaliadas", rendered_text)
        self.assertIn(challenge.competencies_assessed[0], rendered_text)
        self.assertIn("Critérios de avaliação", rendered_text)
        self.assertIn(challenge.evaluation_criteria[0], rendered_text)
        self.assertEqual(session_state["gui_generated_challenge_id"], challenge.id)

    def test_unmatched_filters_show_information(self):
        with (
            patch.object(desafio, "_load_challenges", return_value=self.challenges),
            patch.object(desafio, "filter_challenges", return_value=[]),
            patch.object(desafio.st, "title"),
            patch.object(desafio.st, "markdown"),
            patch.object(desafio.st, "selectbox", side_effect=["Python", Level.ADVANCED]),
            patch.object(desafio.st, "info") as info,
        ):
            desafio.render()

        info.assert_called_once_with(
            "Não há desafios disponíveis para essa tecnologia e nível."
        )

    def test_missing_challenge_file_shows_error(self):
        with (
            patch.object(
                desafio,
                "load_challenges",
                side_effect=FileNotFoundError("missing"),
            ),
            patch.object(desafio.st, "error") as error,
        ):
            result = desafio._load_challenges()

        self.assertIsNone(result)
        error.assert_called_once()
        self.assertIn("Arquivo de desafios não encontrado", error.call_args.args[0])

    def test_invalid_challenge_data_shows_error(self):
        with (
            patch.object(
                desafio,
                "load_challenges",
                side_effect=ValueError("invalid data"),
            ),
            patch.object(desafio.st, "error") as error,
        ):
            result = desafio._load_challenges()

        self.assertIsNone(result)
        error.assert_called_once()
        self.assertIn("Não foi possível carregar os desafios", error.call_args.args[0])

    def test_app_test_selects_and_displays_a_challenge(self):
        challenge = self.challenges[0]
        app = AppTest.from_file(str(_APP_PATH)).run()

        app.button(key="nav_desafio").click().run()
        app.selectbox(key="challenge_technology").set_value(challenge.technology)
        app.selectbox(key="challenge_level").set_value(challenge.level)
        app.run()
        assert not app.exception

        selected = app.selectbox(key="challenge_selection").value
        self.assertEqual(selected.id, challenge.id)
        app.button(key="show_challenge").click().run()

        assert not app.exception
        self.assertEqual(
            app.session_state["gui_generated_challenge_id"],
            selected.id,
        )
        rendered = "\n".join(item.value for item in app.markdown)
        self.assertIn(selected.title, rendered)
        self.assertIn(selected.technology, rendered)
        self.assertIn(selected.description, rendered)
        self.assertIn(f"{selected.estimated_hours:g} horas", rendered)
        for competency in selected.competencies_assessed:
            self.assertIn(competency, rendered)
        for criterion in selected.evaluation_criteria:
            self.assertIn(criterion, rendered)


if __name__ == "__main__":
    unittest.main()
