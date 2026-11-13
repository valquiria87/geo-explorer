"""
tests/test_data_loader.py
-------------------------
Automated tests for core/data_loader.py — Etapa 5 of Geo-Explorer.

Run with:
    python -m unittest discover -s tests -v
"""

import json
import os
import tempfile
import unittest

from core.data_loader import load_learning_paths
from core.models import Level, LearningPath, LearningStep


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_tmp(content: str) -> str:
    """Write *content* to a temporary file and return its path."""
    fd, path = tempfile.mkstemp(suffix=".json")
    os.close(fd)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(content)
    return path


# ---------------------------------------------------------------------------
# Group 1 — Loading the four paths from the real data file
# ---------------------------------------------------------------------------

class TestLoadFourPaths(unittest.TestCase):
    """Verifies that the real data file loads exactly four LearningPath objects."""

    @classmethod
    def setUpClass(cls):
        cls.paths = load_learning_paths()

    def test_returns_list(self):
        self.assertIsInstance(self.paths, list)

    def test_exactly_four_paths(self):
        self.assertEqual(len(self.paths), 4)

    def test_all_items_are_learning_path(self):
        for path in self.paths:
            self.assertIsInstance(path, LearningPath)

    def test_expected_ids_present(self):
        ids = {p.id for p in self.paths}
        expected = {
            "python-beginner-01",
            "ai-intermediate-01",
            "ai-agents-intermediate-01",
            "n8n-automation-beginner-01",
        }
        self.assertEqual(ids, expected)


# ---------------------------------------------------------------------------
# Group 2 — Correct Level enum conversion
# ---------------------------------------------------------------------------

class TestLevelConversion(unittest.TestCase):
    """Verifies that every 'level' string is converted to the correct Level enum."""

    @classmethod
    def setUpClass(cls):
        cls.paths_by_id = {p.id: p for p in load_learning_paths()}

    def test_python_path_is_beginner(self):
        self.assertIs(self.paths_by_id["python-beginner-01"].level, Level.BEGINNER)

    def test_ai_path_is_intermediate(self):
        self.assertIs(self.paths_by_id["ai-intermediate-01"].level, Level.INTERMEDIATE)

    def test_agents_path_is_intermediate(self):
        self.assertIs(self.paths_by_id["ai-agents-intermediate-01"].level, Level.INTERMEDIATE)

    def test_n8n_path_is_beginner(self):
        self.assertIs(self.paths_by_id["n8n-automation-beginner-01"].level, Level.BEGINNER)

    def test_level_is_enum_instance(self):
        for path in self.paths_by_id.values():
            self.assertIsInstance(path.level, Level)


# ---------------------------------------------------------------------------
# Group 3 — Correct LearningStep conversion
# ---------------------------------------------------------------------------

class TestLearningStepConversion(unittest.TestCase):
    """Verifies that steps are properly converted to LearningStep objects."""

    @classmethod
    def setUpClass(cls):
        paths = load_learning_paths()
        cls.python_path = next(p for p in paths if p.id == "python-beginner-01")

    def test_python_path_has_five_steps(self):
        self.assertEqual(len(self.python_path.steps), 5)

    def test_all_steps_are_learning_step_instances(self):
        for step in self.python_path.steps:
            self.assertIsInstance(step, LearningStep)

    def test_first_step_order_is_one(self):
        first = self.python_path.steps[0]
        self.assertEqual(first.order, 1)

    def test_step_order_values_are_sequential(self):
        orders = [s.order for s in self.python_path.steps]
        self.assertEqual(orders, list(range(1, 6)))

    def test_step_title_is_non_empty_string(self):
        for step in self.python_path.steps:
            self.assertIsInstance(step.title, str)
            self.assertTrue(step.title)

    def test_step_description_is_non_empty_string(self):
        for step in self.python_path.steps:
            self.assertIsInstance(step.description, str)
            self.assertTrue(step.description)

    def test_first_step_title(self):
        self.assertEqual(
            self.python_path.steps[0].title,
            "Environment Setup and Python Basics",
        )

    def test_competencies_developed_is_list_of_strings(self):
        for step in self.python_path.steps:
            self.assertIsInstance(step.competencies_developed, list)
            for c in step.competencies_developed:
                self.assertIsInstance(c, str)


# ---------------------------------------------------------------------------
# Group 4 — Competency preservation
# ---------------------------------------------------------------------------

class TestCompetencyPreservation(unittest.TestCase):
    """Verifies that path-level competencies are preserved exactly."""

    @classmethod
    def setUpClass(cls):
        cls.paths_by_id = {p.id: p for p in load_learning_paths()}

    def test_python_path_competencies_count(self):
        self.assertEqual(len(self.paths_by_id["python-beginner-01"].competencies), 14)

    def test_python_path_includes_specific_competency(self):
        competencies = self.paths_by_id["python-beginner-01"].competencies
        self.assertIn("exception handling", competencies)

    def test_all_competencies_are_strings(self):
        for path in self.paths_by_id.values():
            for c in path.competencies:
                self.assertIsInstance(c, str)

    def test_n8n_path_competencies_count(self):
        self.assertEqual(len(self.paths_by_id["n8n-automation-beginner-01"].competencies), 10)

    def test_ai_agents_path_competencies_count(self):
        self.assertEqual(len(self.paths_by_id["ai-agents-intermediate-01"].competencies), 10)


# ---------------------------------------------------------------------------
# Group 5 — Independence from working directory
# ---------------------------------------------------------------------------

class TestWorkingDirectoryIndependence(unittest.TestCase):
    """Verifies that load_learning_paths() works regardless of cwd."""

    def test_load_from_root_directory(self):
        original_cwd = os.getcwd()
        try:
            os.chdir(os.path.expanduser("~"))
            paths = load_learning_paths()
            self.assertEqual(len(paths), 4)
        finally:
            os.chdir(original_cwd)

    def test_load_from_temp_directory(self):
        original_cwd = os.getcwd()
        try:
            os.chdir(tempfile.gettempdir())
            paths = load_learning_paths()
            self.assertEqual(len(paths), 4)
        finally:
            os.chdir(original_cwd)


# ---------------------------------------------------------------------------
# Group 6 — Non-existent file
# ---------------------------------------------------------------------------

class TestFileNotFound(unittest.TestCase):
    """Verifies that a missing file raises FileNotFoundError."""

    def test_raises_file_not_found(self):
        with self.assertRaises(FileNotFoundError):
            load_learning_paths("/nonexistent/path/learning_paths.json")

    def test_error_message_contains_path(self):
        bad_path = "/nonexistent/path/learning_paths.json"
        with self.assertRaises(FileNotFoundError) as ctx:
            load_learning_paths(bad_path)
        self.assertIn(bad_path, str(ctx.exception))


# ---------------------------------------------------------------------------
# Group 7 — Invalid JSON
# ---------------------------------------------------------------------------

class TestInvalidJSON(unittest.TestCase):
    """Verifies that malformed JSON raises ValueError."""

    def setUp(self):
        self.tmp = _write_tmp("{ this is not valid json }")

    def tearDown(self):
        os.unlink(self.tmp)

    def test_raises_value_error(self):
        with self.assertRaises(ValueError):
            load_learning_paths(self.tmp)

    def test_error_message_mentions_invalid_json(self):
        with self.assertRaises(ValueError) as ctx:
            load_learning_paths(self.tmp)
        self.assertIn("invalid JSON", str(ctx.exception))


# ---------------------------------------------------------------------------
# Group 8 — Incorrect top-level JSON structure
# ---------------------------------------------------------------------------

class TestWrongTopLevelStructure(unittest.TestCase):
    """Verifies that a JSON object (not array) at top level raises ValueError."""

    def setUp(self):
        self.tmp_object = _write_tmp('{"paths": []}')
        self.tmp_string = _write_tmp('"just a string"')
        self.tmp_number = _write_tmp("42")

    def tearDown(self):
        for path in (self.tmp_object, self.tmp_string, self.tmp_number):
            os.unlink(path)

    def test_dict_at_top_level_raises_value_error(self):
        with self.assertRaises(ValueError):
            load_learning_paths(self.tmp_object)

    def test_string_at_top_level_raises_value_error(self):
        with self.assertRaises(ValueError):
            load_learning_paths(self.tmp_string)

    def test_number_at_top_level_raises_value_error(self):
        with self.assertRaises(ValueError):
            load_learning_paths(self.tmp_number)

    def test_error_message_mentions_json_array(self):
        with self.assertRaises(ValueError) as ctx:
            load_learning_paths(self.tmp_object)
        self.assertIn("JSON array", str(ctx.exception))


# ---------------------------------------------------------------------------
# Group 9 — Missing required fields
# ---------------------------------------------------------------------------

class TestMissingRequiredFields(unittest.TestCase):
    """Verifies that records missing required fields raise ValueError."""

    def _load_tmp(self, payload: list) -> None:
        path = _write_tmp(json.dumps(payload))
        try:
            load_learning_paths(path)
        finally:
            os.unlink(path)

    def _base_path(self) -> dict:
        return {
            "id": "test-01",
            "title": "Test Path",
            "technology": "Python",
            "level": "beginner",
            "competencies": ["a"],
            "steps": [
                {
                    "order": 1,
                    "title": "Step 1",
                    "description": "Desc",
                    "competencies_developed": ["a"],
                }
            ],
        }

    def test_missing_id_raises_value_error(self):
        record = self._base_path()
        del record["id"]
        with self.assertRaises(ValueError):
            self._load_tmp([record])

    def test_missing_title_raises_value_error(self):
        record = self._base_path()
        del record["title"]
        with self.assertRaises(ValueError):
            self._load_tmp([record])

    def test_missing_level_raises_value_error(self):
        record = self._base_path()
        del record["level"]
        with self.assertRaises(ValueError):
            self._load_tmp([record])

    def test_missing_steps_raises_value_error(self):
        record = self._base_path()
        del record["steps"]
        with self.assertRaises(ValueError):
            self._load_tmp([record])

    def test_missing_competencies_raises_value_error(self):
        record = self._base_path()
        del record["competencies"]
        with self.assertRaises(ValueError):
            self._load_tmp([record])

    def test_step_missing_title_raises_value_error(self):
        record = self._base_path()
        del record["steps"][0]["title"]
        with self.assertRaises(ValueError):
            self._load_tmp([record])

    def test_step_missing_order_raises_value_error(self):
        record = self._base_path()
        del record["steps"][0]["order"]
        with self.assertRaises(ValueError):
            self._load_tmp([record])

    def test_step_missing_competencies_developed_raises_value_error(self):
        record = self._base_path()
        del record["steps"][0]["competencies_developed"]
        with self.assertRaises(ValueError):
            self._load_tmp([record])


# ---------------------------------------------------------------------------
# Group 10 — Unknown level value
# ---------------------------------------------------------------------------

class TestUnknownLevel(unittest.TestCase):
    """Verifies that an unrecognised level string raises ValueError."""

    def _load_with_level(self, level_value: str) -> None:
        payload = [
            {
                "id": "test-01",
                "title": "Test Path",
                "technology": "Python",
                "level": level_value,
                "competencies": ["a"],
                "steps": [
                    {
                        "order": 1,
                        "title": "Step 1",
                        "description": "Desc",
                        "competencies_developed": ["a"],
                    }
                ],
            }
        ]
        path = _write_tmp(json.dumps(payload))
        try:
            load_learning_paths(path)
        finally:
            os.unlink(path)

    def test_unknown_level_string_raises_value_error(self):
        with self.assertRaises(ValueError):
            self._load_with_level("expert")

    def test_empty_level_string_raises_value_error(self):
        with self.assertRaises(ValueError):
            self._load_with_level("")

    def test_typo_in_level_raises_value_error(self):
        with self.assertRaises(ValueError):
            self._load_with_level("Beginnerr")

    def test_non_string_level_raises_value_error(self):
        payload = [
            {
                "id": "test-01",
                "title": "Test Path",
                "technology": "Python",
                "level": 1,
                "competencies": ["a"],
                "steps": [
                    {
                        "order": 1,
                        "title": "Step 1",
                        "description": "Desc",
                        "competencies_developed": ["a"],
                    }
                ],
            }
        ]
        path = _write_tmp(json.dumps(payload))
        try:
            with self.assertRaises(ValueError):
                load_learning_paths(path)
        finally:
            os.unlink(path)

    def test_error_message_mentions_valid_levels(self):
        with self.assertRaises(ValueError) as ctx:
            self._load_with_level("unknown_level")
        error_msg = str(ctx.exception)
        self.assertTrue(
            any(v.value in error_msg for v in Level),
            msg=f"Expected valid level names in error message, got: {error_msg}",
        )


if __name__ == "__main__":
    unittest.main()
