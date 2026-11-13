from pathlib import Path
import unittest
from contextlib import nullcontext
from unittest.mock import patch

from commands.certificado import DISCLAIMER
from core.models import Level
from gui.pages import certificado
from streamlit.testing.v1 import AppTest


_APP_PATH = Path(__file__).resolve().parents[1] / "gui" / "app.py"


class TestCertificatePage(unittest.TestCase):
    def _render_form(
        self,
        participant="Ana Paula Souza",
        activity="Python Foundations",
        technology="Python",
        competencies="Python syntax\nfile I/O",
    ):
        session_state = {}
        with (
            patch.object(certificado.st, "title"),
            patch.object(certificado.st, "markdown") as markdown,
            patch.object(certificado.st, "divider"),
            patch.object(certificado.st, "warning") as warning,
            patch.object(certificado.st, "error") as error,
            patch.object(certificado.st, "form", return_value=nullcontext()),
            patch.object(
                certificado.st,
                "text_input",
                side_effect=[participant, activity, technology],
            ),
            patch.object(
                certificado.st, "selectbox", return_value=Level.BEGINNER
            ),
            patch.object(
                certificado.st, "text_area", return_value=competencies
            ),
            patch.object(
                certificado.st, "form_submit_button", return_value=True
            ),
            patch.object(certificado.st, "session_state", session_state),
        ):
            certificado.render()

        return session_state, markdown, warning, error

    def test_form_builds_and_displays_certificate(self):
        session_state, markdown, warning, error = self._render_form()

        self.assertFalse(error.called)
        self.assertEqual(warning.call_args.args[0], DISCLAIMER)
        result = session_state["gui_generated_certificate"]
        self.assertEqual(result["participant"], "Ana Paula Souza")
        self.assertEqual(result["activity"], "Python Foundations")
        self.assertEqual(result["technology"], "Python")
        self.assertEqual(result["level"], "beginner")
        self.assertEqual(result["competencies"], ["Python syntax", "file I/O"])
        self.assertIn("id", result)
        self.assertIn("issued_on", result)

        rendered_text = "\n".join(str(call.args[0]) for call in markdown.call_args_list)
        self.assertIn(result["id"], rendered_text)
        self.assertIn(result["issued_on"].strftime("%d/%m/%Y"), rendered_text)

    def test_blank_participant_is_rejected_without_storing_certificate(self):
        session_state, _, _, error = self._render_form(participant="  ")

        error.assert_called_once()
        self.assertNotIn("gui_generated_certificate", session_state)

    def test_blank_technology_is_rejected_without_storing_certificate(self):
        session_state, _, _, error = self._render_form(technology="  ")

        error.assert_called_once_with("Informe a tecnologia da atividade.")
        self.assertNotIn("gui_generated_certificate", session_state)

    def test_competency_parser_ignores_blank_lines(self):
        self.assertEqual(
            certificado._parse_competencies("  Python  \n\n file I/O \n"),
            ["Python", "file I/O"],
        )

    def test_app_test_submits_and_renders_certificate(self):
        app = AppTest.from_file(str(_APP_PATH)).run()
        app.button(key="nav_certificado").click().run()
        assert not app.exception

        app.text_input[0].set_value("Ana Paula Souza")
        app.text_input[1].set_value("Python Foundations")
        app.text_input[2].set_value("Python")
        app.text_area[0].set_value("Python syntax\nfile I/O")
        app.button(key="FormSubmitter:certificate_form-Gerar certificado").click().run()

        assert not app.exception
        certificate = app.session_state["gui_generated_certificate"]
        self.assertEqual(certificate["participant"], "Ana Paula Souza")
        self.assertEqual(certificate["activity"], "Python Foundations")
        self.assertEqual(certificate["technology"], "Python")
        self.assertEqual(certificate["level"], "beginner")
        self.assertEqual(certificate["competencies"], ["Python syntax", "file I/O"])
        self.assertIn(certificate["id"], "\n".join(item.value for item in app.markdown))
        self.assertIn(
            certificate["issued_on"].strftime("%d/%m/%Y"),
            "\n".join(item.value for item in app.markdown),
        )
        self.assertIn(DISCLAIMER, [item.value for item in app.warning])

        app.button(key="nav_home").click().run()
        app.button(key="nav_certificado").click().run()
        assert not app.exception
        self.assertIn(certificate["id"], "\n".join(item.value for item in app.markdown))

    def test_app_test_rejects_empty_activity(self):
        app = AppTest.from_file(str(_APP_PATH)).run()
        app.button(key="nav_certificado").click().run()
        app.text_input[0].set_value("Ana Paula Souza")
        app.text_input[1].set_value("  ")
        app.text_input[2].set_value("Python")
        app.button(key="FormSubmitter:certificate_form-Gerar certificado").click().run()

        assert not app.exception
        self.assertNotIn("gui_generated_certificate", app.session_state)
        self.assertTrue(
            any("Activity name must not be empty" in item.value for item in app.error)
        )

    def test_app_test_allows_empty_competencies(self):
        app = AppTest.from_file(str(_APP_PATH)).run()
        app.button(key="nav_certificado").click().run()
        app.text_input[0].set_value("Ana Paula Souza")
        app.text_input[1].set_value("Python Foundations")
        app.text_input[2].set_value("Python")
        app.text_area[0].set_value("")
        app.button(key="FormSubmitter:certificate_form-Gerar certificado").click().run()

        assert not app.exception
        self.assertEqual(
            app.session_state["gui_generated_certificate"]["competencies"],
            [],
        )
        self.assertIn(
            "Nenhuma competência informada.",
            "\n".join(item.value for item in app.markdown),
        )


if __name__ == "__main__":
    unittest.main()
