from dataclasses import replace
from pathlib import Path
import unittest
from contextlib import ExitStack, nullcontext
from unittest.mock import patch

from commands.certificado import DISCLAIMER, build_certificate
from core.data_loader import load_learning_paths
from gui.pages import certificado
from streamlit.testing.v1 import AppTest


_APP_PATH = Path(__file__).resolve().parents[1] / "gui" / "app.py"

# Real catalog (data/learning_paths.json). The page offers one selectbox option
# per trail, labelled "<title> (<technology> – <level>)".
_CATALOG = load_learning_paths()
_PYTHON_FOUNDATIONS = "Python Foundations"


def _catalog_index(title):
    return next(i for i, path in enumerate(_CATALOG) if path.title == title)


class TestCertificatePage(unittest.TestCase):
    def _render_form(
        self,
        participant="Ana Paula Souza",
        activity_title=_PYTHON_FOUNDATIONS,
        competencies="Python syntax\nfile I/O",
        paths=None,
        build_error=None,
    ):
        """Render the page with Streamlit widgets mocked.

        ``activity_title`` picks the selectbox option whose label starts with
        that catalog title. ``paths`` overrides the catalog loaded by the page
        and ``build_error`` makes ``build_certificate`` raise that error.
        The options offered to the selectbox are kept in
        ``self.selectbox_options``; the ``build_certificate`` mock (when
        ``build_error`` is given) is kept in ``self.build_mock``.
        """
        session_state = {}
        self.selectbox_options = []
        self.build_mock = None

        def select_activity(label, options, *args, **kwargs):
            self.selectbox_options = list(options)
            return next(
                option
                for option in self.selectbox_options
                if option.startswith(f"{activity_title} (")
            )

        with ExitStack() as stack:
            stack.enter_context(patch.object(certificado.st, "title"))
            markdown = stack.enter_context(patch.object(certificado.st, "markdown"))
            stack.enter_context(patch.object(certificado.st, "divider"))
            warning = stack.enter_context(patch.object(certificado.st, "warning"))
            error = stack.enter_context(patch.object(certificado.st, "error"))
            stack.enter_context(
                patch.object(certificado.st, "form", return_value=nullcontext())
            )
            stack.enter_context(
                patch.object(certificado.st, "text_input", return_value=participant)
            )
            stack.enter_context(
                patch.object(certificado.st, "selectbox", side_effect=select_activity)
            )
            self.text_area = stack.enter_context(
                patch.object(certificado.st, "text_area", return_value=competencies)
            )
            stack.enter_context(
                patch.object(certificado.st, "form_submit_button", return_value=True)
            )
            stack.enter_context(
                patch.object(certificado.st, "session_state", session_state)
            )
            if paths is not None:
                stack.enter_context(
                    patch.object(certificado, "load_learning_paths", return_value=paths)
                )
            if build_error is not None:
                self.build_mock = stack.enter_context(
                    patch.object(
                        certificado, "build_certificate", side_effect=build_error
                    )
                )
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
        # Technology is no longer typed: it comes from the selected trail.
        # A catalog trail with a blank technology exercises the same guard.
        blank_technology_path = replace(
            _CATALOG[_catalog_index(_PYTHON_FOUNDATIONS)], technology="  "
        )
        session_state, _, _, error = self._render_form(paths=[blank_technology_path])

        error.assert_called_once_with("Informe a tecnologia da atividade.")
        self.assertNotIn("gui_generated_certificate", session_state)

    def test_unregistered_activity_shows_error(self):
        # An unregistered activity can no longer be typed into the page, so the
        # domain rejection is raised by build_certificate (real message taken
        # from the real catalog) and the page must show it and store nothing.
        with self.assertRaises(ValueError) as rejected:
            build_certificate(
                participant="Ana Paula Souza",
                activity="Curso Inexistente",
                technology="Python",
                level="beginner",
                competencies=None,
                paths=_CATALOG,
            )
        session_state, _, _, error = self._render_form(build_error=rejected.exception)

        self.build_mock.assert_called_once()
        self.assertEqual(self.build_mock.call_args.kwargs["activity"], "Python Foundations")
        error.assert_called_once()
        self.assertIn("não encontrada no catálogo", error.call_args.args[0])
        self.assertNotIn("gui_generated_certificate", session_state)

    def test_activity_options_come_only_from_catalog(self):
        self._render_form()

        self.assertEqual(len(self.selectbox_options), len(_CATALOG))
        for path in _CATALOG:
            self.assertTrue(
                any(
                    option.startswith(f"{path.title} (")
                    for option in self.selectbox_options
                ),
                path.title,
            )
        self.assertFalse(
            any("Curso Inexistente" in option for option in self.selectbox_options)
        )

    def test_empty_catalog_shows_error_without_rendering_certificate(self):
        session_state, _, _, error = self._render_form(paths=[])

        error.assert_called_once_with(
            "Nenhuma trilha disponível no catálogo para gerar um registro."
        )
        self.assertNotIn("gui_generated_certificate", session_state)
        self.assertEqual(self.selectbox_options, [])

    def test_selecting_each_catalog_path_fills_technology_and_level(self):
        for path in _CATALOG:
            with self.subTest(path=path.id):
                session_state, _, _, error = self._render_form(
                    activity_title=path.title, competencies="qualquer competência"
                )

                self.assertFalse(error.called)
                result = session_state["gui_generated_certificate"]
                self.assertEqual(result["activity"], path.title)
                self.assertEqual(result["technology"], path.technology)
                self.assertEqual(result["level"], path.level.value)

    def test_empty_competencies_field_uses_trail_competencies(self):
        for path in _CATALOG:
            for text in ("", "   \n \n\t"):
                with self.subTest(path=path.id, text=text):
                    session_state, _, _, error = self._render_form(
                        activity_title=path.title, competencies=text
                    )

                    self.assertFalse(error.called)
                    result = session_state["gui_generated_certificate"]
                    self.assertEqual(result["competencies"], path.competencies)

    def test_custom_competencies_are_used_instead_of_trail_competencies(self):
        session_state, _, _, _ = self._render_form(
            competencies="  control flow  \n\n   \n file I/O "
        )

        result = session_state["gui_generated_certificate"]
        self.assertEqual(result["competencies"], ["control flow", "file I/O"])

    def test_help_text_explains_that_empty_field_uses_trail_competencies(self):
        self._render_form()

        help_text = self.text_area.call_args.kwargs["help"]
        self.assertIn("deixe vazio", help_text)
        self.assertIn("competências da trilha", help_text)

    def test_trail_without_competencies_shows_empty_message(self):
        bare = replace(_CATALOG[_catalog_index(_PYTHON_FOUNDATIONS)], competencies=[])
        session_state, markdown, _, error = self._render_form(
            paths=[bare], competencies=""
        )

        self.assertFalse(error.called)
        self.assertEqual(session_state["gui_generated_certificate"]["competencies"], [])
        rendered = "\n".join(str(call.args[0]) for call in markdown.call_args_list)
        self.assertIn("Nenhuma competência informada.", rendered)

    def test_page_texts_declare_a_self_declared_record(self):
        session_state, markdown, _, error = self._render_form()

        self.assertFalse(error.called)
        rendered = "\n".join(str(call.args[0]) for call in markdown.call_args_list)
        self.assertIn("## Registro de Trilha e Competências Associadas", rendered)
        self.assertIn("### Competências associadas à atividade", rendered)
        self.assertIn("autodeclarad", rendered)
        self.assertIn("não acompanha nem valida a conclusão", rendered)
        self.assertIn("não foram verificadas", rendered)
        self.assertEqual(
            self.text_area.call_args.args[0], "Competências associadas à atividade"
        )

    def test_page_texts_make_no_completion_or_competency_claims(self):
        _, markdown, _, _ = self._render_form()

        rendered = "\n".join(str(call.args[0]) for call in markdown.call_args_list)
        for old_text in (
            "Certificado de Conclusão",
            "Registre a conclusão",
            "Competências desenvolvidas",
            "concluiu",
            "participou",
            "desenvolvendo",
        ):
            with self.subTest(old_text=old_text):
                self.assertNotIn(old_text, rendered)

    def test_competency_parser_ignores_blank_lines(self):
        self.assertEqual(
            certificado._parse_competencies("  Python  \n\n file I/O \n"),
            ["Python", "file I/O"],
        )

    def test_app_test_submits_and_renders_certificate(self):
        app = AppTest.from_file(str(_APP_PATH)).run()
        app.button(key="nav_certificado").click().run()
        assert not app.exception

        index = _catalog_index(_PYTHON_FOUNDATIONS)
        self.assertEqual(len(app.text_input), 1)  # only the participant is typed
        self.assertTrue(app.selectbox[0].options[index].startswith("Python Foundations ("))
        app.text_input[0].set_value("Ana Paula Souza")
        app.selectbox[0].select_index(index)
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

    def test_app_test_shows_record_title_and_labels(self):
        app = AppTest.from_file(str(_APP_PATH)).run()
        app.button(key="nav_certificado").click().run()
        assert not app.exception

        self.assertEqual(app.text_area[0].label, "Competências associadas à atividade")
        page_text = " ".join(" ".join(item.value for item in app.markdown).split())
        self.assertIn("não acompanha nem valida a conclusão", page_text)
        app.text_input[0].set_value("Ana Paula Souza")
        app.selectbox[0].select_index(_catalog_index(_PYTHON_FOUNDATIONS))
        app.button(key="FormSubmitter:certificate_form-Gerar certificado").click().run()

        assert not app.exception
        page_text = "\n".join(item.value for item in app.markdown)
        self.assertIn("## Registro de Trilha e Competências Associadas", page_text)
        self.assertNotIn("Certificado de Conclusão", page_text)
        self.assertNotIn("concluiu", page_text)

    def test_app_test_rejects_empty_activity(self):
        # The activity is chosen from the catalog: there is no free-text field
        # and no blank option, so an empty activity cannot be submitted.
        app = AppTest.from_file(str(_APP_PATH)).run()
        app.button(key="nav_certificado").click().run()
        assert not app.exception

        self.assertEqual(len(app.text_input), 1)  # participant only
        options = app.selectbox[0].options
        self.assertEqual(len(options), len(_CATALOG))
        self.assertTrue(all(option.strip() for option in options))

    def test_app_test_rejects_blank_participant(self):
        app = AppTest.from_file(str(_APP_PATH)).run()
        app.button(key="nav_certificado").click().run()
        app.text_input[0].set_value("  ")
        app.selectbox[0].select_index(_catalog_index(_PYTHON_FOUNDATIONS))
        app.button(key="FormSubmitter:certificate_form-Gerar certificado").click().run()

        assert not app.exception
        self.assertNotIn("gui_generated_certificate", app.session_state)
        self.assertTrue(
            any("Participant name must not be empty" in item.value for item in app.error)
        )

    def test_app_test_empty_competencies_use_trail_competencies(self):
        # An empty competencies field means "not provided": the certificate must
        # carry the competencies of the trail selected in the form.
        app = AppTest.from_file(str(_APP_PATH)).run()
        app.button(key="nav_certificado").click().run()
        app.text_input[0].set_value("Ana Paula Souza")
        app.selectbox[0].select_index(_catalog_index(_PYTHON_FOUNDATIONS))
        app.text_area[0].set_value("")
        app.button(key="FormSubmitter:certificate_form-Gerar certificado").click().run()

        assert not app.exception
        trail = _CATALOG[_catalog_index(_PYTHON_FOUNDATIONS)]
        self.assertEqual(
            app.session_state["gui_generated_certificate"]["competencies"],
            trail.competencies,
        )
        rendered = "\n".join(item.value for item in app.markdown)
        self.assertNotIn("Nenhuma competência informada.", rendered)
        self.assertIn(f"- {trail.competencies[0]}", rendered)


if __name__ == "__main__":
    unittest.main()
