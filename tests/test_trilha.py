"""
tests/test_trilha.py
--------------------
Automated tests for commands/trilha.py — Etapa 6 of Geo-Explorer.

Run with:
    python -m unittest discover -s tests -v
"""

import unittest
from io import StringIO
from unittest.mock import patch

from commands.trilha import find_learning_path, show_learning_path
from core.data_loader import load_learning_paths
from core.models import LearningPath, LearningStep, Level


# ---------------------------------------------------------------------------
# Shared fixture — loaded once for the whole module
# ---------------------------------------------------------------------------

_PATHS: list[LearningPath] = load_learning_paths()
_PATHS_BY_ID = {p.id: p for p in _PATHS}


def _capture(technology: str) -> str:
    """Call show_learning_path and return everything printed to stdout."""
    buf = StringIO()
    with patch("sys.stdout", buf):
        show_learning_path(technology)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Group 1 — find_learning_path: basic lookup
# ---------------------------------------------------------------------------

class TestFindLearningPath(unittest.TestCase):
    """Verifies the lookup helper against the real data set."""

    def test_find_python_exact_case(self):
        result = find_learning_path("Python", _PATHS)
        self.assertIsNotNone(result)
        self.assertEqual(result.id, "python-beginner-01")

    def test_find_python_lowercase(self):
        result = find_learning_path("python", _PATHS)
        self.assertIsNotNone(result)
        self.assertEqual(result.id, "python-beginner-01")

    def test_find_python_uppercase(self):
        result = find_learning_path("PYTHON", _PATHS)
        self.assertIsNotNone(result)
        self.assertEqual(result.id, "python-beginner-01")

    def test_find_python_mixed_case(self):
        result = find_learning_path("PyThOn", _PATHS)
        self.assertIsNotNone(result)
        self.assertEqual(result.id, "python-beginner-01")

    def test_find_n8n(self):
        result = find_learning_path("n8n", _PATHS)
        self.assertIsNotNone(result)
        self.assertEqual(result.id, "n8n-automation-beginner-01")

    def test_find_ai_agents(self):
        result = find_learning_path("AI Agents", _PATHS)
        self.assertIsNotNone(result)
        self.assertEqual(result.id, "ai-agents-intermediate-01")

    def test_find_artificial_intelligence(self):
        result = find_learning_path("Artificial Intelligence", _PATHS)
        self.assertIsNotNone(result)
        self.assertEqual(result.id, "ai-intermediate-01")

    def test_nonexistent_technology_returns_none(self):
        result = find_learning_path("Rust", _PATHS)
        self.assertIsNone(result)

    def test_empty_string_returns_none(self):
        result = find_learning_path("", _PATHS)
        self.assertIsNone(result)

    def test_whitespace_only_returns_none(self):
        result = find_learning_path("   ", _PATHS)
        self.assertIsNone(result)

    def test_returns_learning_path_instance(self):
        result = find_learning_path("Python", _PATHS)
        self.assertIsInstance(result, LearningPath)


# ---------------------------------------------------------------------------
# Group 2 — show_learning_path: existing technology output
# ---------------------------------------------------------------------------

class TestShowLearningPathFound(unittest.TestCase):
    """Verifies that show_learning_path prints all expected content."""

    @classmethod
    def setUpClass(cls):
        cls.output = _capture("Python")

    def test_prints_title(self):
        self.assertIn("Python Foundations", self.output)

    def test_prints_technology(self):
        self.assertIn("Python", self.output)

    def test_prints_level(self):
        self.assertIn("beginner", self.output)

    def test_prints_description(self):
        self.assertIn("structured introduction to Python", self.output)

    def test_prints_five_steps(self):
        # Each step is announced with "Step N:"
        for n in range(1, 6):
            self.assertIn(f"Step {n}:", self.output)

    def test_prints_step_titles(self):
        self.assertIn("Environment Setup and Python Basics", self.output)
        self.assertIn("Control Flow and Functions", self.output)
        self.assertIn("Collections, Comprehensions, and File I/O", self.output)
        self.assertIn("Modules, Packages, and Testing", self.output)
        self.assertIn("Object-Oriented Programming in Python", self.output)

    def test_prints_step_descriptions(self):
        self.assertIn("Install Python and configure a virtual environment", self.output)

    def test_prints_step_competencies(self):
        self.assertIn("Python syntax and semantics", self.output)
        self.assertIn("control flow", self.output)
        self.assertIn("exception handling", self.output)

    def test_prints_general_competencies_section(self):
        self.assertIn("General competencies", self.output)

    def test_prints_all_general_competencies(self):
        path = _PATHS_BY_ID["python-beginner-01"]
        for competency in path.competencies:
            self.assertIn(competency, self.output)


# ---------------------------------------------------------------------------
# Group 3 — show_learning_path: case-insensitive search
# ---------------------------------------------------------------------------

class TestShowLearningPathCaseInsensitive(unittest.TestCase):
    """Verifies that the search is truly case-insensitive."""

    def test_lowercase_finds_path(self):
        output = _capture("python")
        self.assertIn("Python Foundations", output)

    def test_uppercase_finds_path(self):
        output = _capture("PYTHON")
        self.assertIn("Python Foundations", output)

    def test_mixed_case_finds_path(self):
        output = _capture("pYtHoN")
        self.assertIn("Python Foundations", output)

    def test_n8n_case_insensitive(self):
        output = _capture("N8N")
        self.assertIn("Automation with n8n", output)


# ---------------------------------------------------------------------------
# Group 4 — show_learning_path: all five steps are displayed
# ---------------------------------------------------------------------------

class TestShowLearningPathFiveSteps(unittest.TestCase):
    """Verifies that exactly five steps are shown for each path."""

    def _count_step_markers(self, output: str) -> int:
        """Count occurrences of 'Step N:' in the output."""
        return sum(1 for n in range(1, 10) if f"Step {n}:" in output)

    def test_python_path_has_five_steps_in_output(self):
        output = _capture("Python")
        self.assertEqual(self._count_step_markers(output), 5)

    def test_ai_path_has_five_steps_in_output(self):
        output = _capture("Artificial Intelligence")
        self.assertEqual(self._count_step_markers(output), 5)

    def test_ai_agents_path_has_five_steps_in_output(self):
        output = _capture("AI Agents")
        self.assertEqual(self._count_step_markers(output), 5)

    def test_n8n_path_has_five_steps_in_output(self):
        output = _capture("n8n")
        self.assertEqual(self._count_step_markers(output), 5)

    def test_steps_appear_in_order(self):
        output = _capture("Python")
        pos1 = output.index("Step 1:")
        pos2 = output.index("Step 2:")
        pos3 = output.index("Step 3:")
        pos4 = output.index("Step 4:")
        pos5 = output.index("Step 5:")
        self.assertLess(pos1, pos2)
        self.assertLess(pos2, pos3)
        self.assertLess(pos3, pos4)
        self.assertLess(pos4, pos5)


# ---------------------------------------------------------------------------
# Group 5 — show_learning_path: competencies are displayed
# ---------------------------------------------------------------------------

class TestShowLearningPathCompetencies(unittest.TestCase):
    """Verifies that both step-level and path-level competencies appear."""

    @classmethod
    def setUpClass(cls):
        cls.python_output = _capture("Python")
        cls.agents_output = _capture("AI Agents")
        cls.n8n_output = _capture("n8n")

    def test_python_step_competencies_in_output(self):
        for competency in ("Python syntax and semantics", "built-in data types",
                           "virtual environments", "control flow", "functions and scope",
                           "list comprehensions", "file I/O", "exception handling",
                           "modules and packages", "basic testing with pytest",
                           "classes and objects", "attributes and methods",
                           "encapsulation", "inheritance and composition"):
            self.assertIn(competency, self.python_output,
                          msg=f"Missing competency: {competency!r}")

    def test_agents_step_competencies_in_output(self):
        for competency in ("prompt engineering", "LLM API integration",
                           "ReAct reasoning pattern", "tool and function calling"):
            self.assertIn(competency, self.agents_output,
                          msg=f"Missing competency: {competency!r}")

    def test_n8n_step_competencies_in_output(self):
        for competency in ("n8n installation and configuration",
                           "trigger and node design",
                           "JavaScript expressions and the Code node"):
            self.assertIn(competency, self.n8n_output,
                          msg=f"Missing competency: {competency!r}")

    def test_general_competencies_label_present(self):
        self.assertIn("General competencies", self.python_output)

    def test_all_14_python_competencies_listed(self):
        path = _PATHS_BY_ID["python-beginner-01"]
        self.assertEqual(len(path.competencies), 14)
        for c in path.competencies:
            self.assertIn(c, self.python_output)


# ---------------------------------------------------------------------------
# Group 6 — show_learning_path: technology not found
# ---------------------------------------------------------------------------

class TestShowLearningPathNotFound(unittest.TestCase):
    """Verifies the 'not found' message when the technology is unknown."""

    def test_unknown_technology_prints_message(self):
        output = _capture("Rust")
        self.assertIn("No learning path found", output)

    def test_unknown_technology_mentions_name(self):
        output = _capture("Rust")
        self.assertIn("Rust", output)

    def test_unknown_technology_no_step_output(self):
        output = _capture("Rust")
        self.assertNotIn("Step 1:", output)

    def test_another_unknown_technology(self):
        output = _capture("Kotlin")
        self.assertIn("No learning path found", output)


# ---------------------------------------------------------------------------
# Group 7 — show_learning_path: empty / whitespace input
# ---------------------------------------------------------------------------

class TestShowLearningPathEmptyInput(unittest.TestCase):
    """Verifies that blank or whitespace-only input is rejected gracefully."""

    def test_empty_string_prints_error(self):
        output = _capture("")
        self.assertIn("Error", output)

    def test_whitespace_only_prints_error(self):
        output = _capture("   ")
        self.assertIn("Error", output)

    def test_empty_string_no_step_output(self):
        output = _capture("")
        self.assertNotIn("Step 1:", output)

    def test_whitespace_no_step_output(self):
        output = _capture("   ")
        self.assertNotIn("Step 1:", output)

    def test_newline_only_prints_error(self):
        output = _capture("\n")
        self.assertIn("Error", output)


# ---------------------------------------------------------------------------
# Group 8 — Data immutability
# ---------------------------------------------------------------------------

class TestDataImmutability(unittest.TestCase):
    """Verifies that show_learning_path never mutates the loaded data."""

    def test_path_list_length_unchanged(self):
        paths_before = load_learning_paths()
        count_before = len(paths_before)
        show_learning_path("Python")
        paths_after = load_learning_paths()
        self.assertEqual(len(paths_after), count_before)

    def test_python_path_technology_unchanged(self):
        paths = load_learning_paths()
        python_path = next(p for p in paths if p.id == "python-beginner-01")
        technology_before = python_path.technology
        # Call with the original reference still accessible
        show_learning_path("python")
        self.assertEqual(python_path.technology, technology_before)

    def test_python_path_steps_count_unchanged(self):
        paths = load_learning_paths()
        python_path = next(p for p in paths if p.id == "python-beginner-01")
        steps_count_before = len(python_path.steps)
        show_learning_path("Python")
        self.assertEqual(len(python_path.steps), steps_count_before)

    def test_python_path_competencies_unchanged(self):
        paths = load_learning_paths()
        python_path = next(p for p in paths if p.id == "python-beginner-01")
        competencies_snapshot = list(python_path.competencies)
        show_learning_path("PYTHON")
        self.assertEqual(python_path.competencies, competencies_snapshot)

    def test_step_competencies_developed_unchanged(self):
        paths = load_learning_paths()
        python_path = next(p for p in paths if p.id == "python-beginner-01")
        first_step = python_path.steps[0]
        snapshot = list(first_step.competencies_developed)
        show_learning_path("Python")
        self.assertEqual(first_step.competencies_developed, snapshot)

    def test_find_learning_path_does_not_mutate_list(self):
        paths = load_learning_paths()
        original_ids = [p.id for p in paths]
        find_learning_path("Python", paths)
        self.assertEqual([p.id for p in paths], original_ids)


if __name__ == "__main__":
    unittest.main()
