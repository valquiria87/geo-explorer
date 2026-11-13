"""
tests/test_desafio.py
---------------------
Automated tests for commands/desafio.py — Etapa 7 of Geo-Explorer.

Coverage
~~~~~~~~
- Loading challenges from the JSON file.
- Conversion to Challenge objects.
- Filtering by technology.
- Filtering by level.
- Case-insensitive technology matching.
- Invalid input handling (empty technology, unknown level).
- No results found.
- Data immutability (original list and objects are never mutated).
- ID validity and uniqueness.

Run with:
    python -m unittest discover -s tests -v
"""

import unittest
from io import StringIO
from unittest.mock import patch

from commands.desafio import (
    filter_challenges,
    generate_challenge,
    load_challenges,
)
from core.models import Challenge, Level


# ---------------------------------------------------------------------------
# Shared fixture — loaded once for the whole module
# ---------------------------------------------------------------------------

_CHALLENGES: list[Challenge] = load_challenges()
_CHALLENGES_BY_ID: dict[str, Challenge] = {c.id: c for c in _CHALLENGES}


def _capture(technology: str, level: Level) -> str:
    """Call generate_challenge and return everything printed to stdout."""
    buf = StringIO()
    with patch("sys.stdout", buf):
        generate_challenge(technology, level)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Group 1 — load_challenges: file loading
# ---------------------------------------------------------------------------


class TestLoadChallenges(unittest.TestCase):
    """Verifies that the JSON file is loaded without errors."""

    def test_returns_a_list(self):
        result = load_challenges()
        self.assertIsInstance(result, list)

    def test_list_is_not_empty(self):
        result = load_challenges()
        self.assertGreater(len(result), 0)

    def test_at_least_twelve_challenges(self):
        result = load_challenges()
        self.assertGreaterEqual(len(result), 12)

    def test_raises_file_not_found_for_missing_file(self):
        with self.assertRaises(FileNotFoundError):
            load_challenges("/nonexistent/path/challenges.json")

    def test_raises_value_error_for_invalid_json(self):
        import tempfile, os
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json",
                                         delete=False, encoding="utf-8") as f:
            f.write("{ not valid json }")
            tmp_path = f.name
        try:
            with self.assertRaises(ValueError):
                load_challenges(tmp_path)
        finally:
            os.unlink(tmp_path)

    def test_raises_value_error_for_non_list_json(self):
        import tempfile, os
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json",
                                         delete=False, encoding="utf-8") as f:
            f.write('{"key": "value"}')
            tmp_path = f.name
        try:
            with self.assertRaises(ValueError):
                load_challenges(tmp_path)
        finally:
            os.unlink(tmp_path)


# ---------------------------------------------------------------------------
# Group 2 — load_challenges: Challenge object structure
# ---------------------------------------------------------------------------


class TestChallengeObjectConversion(unittest.TestCase):
    """Verifies that every loaded record is a valid Challenge instance."""

    def test_all_items_are_challenge_instances(self):
        for c in _CHALLENGES:
            self.assertIsInstance(c, Challenge,
                                  msg=f"Item {c!r} is not a Challenge")

    def test_all_have_non_empty_id(self):
        for c in _CHALLENGES:
            self.assertTrue(c.id, msg=f"Challenge has empty id: {c!r}")

    def test_all_have_non_empty_title(self):
        for c in _CHALLENGES:
            self.assertTrue(c.title, msg=f"Challenge has empty title: {c!r}")

    def test_all_have_non_empty_technology(self):
        for c in _CHALLENGES:
            self.assertTrue(c.technology,
                            msg=f"Challenge has empty technology: {c!r}")

    def test_all_levels_are_level_enum(self):
        for c in _CHALLENGES:
            self.assertIsInstance(c.level, Level,
                                  msg=f"Challenge {c.id!r} has invalid level")

    def test_all_have_non_empty_description(self):
        for c in _CHALLENGES:
            self.assertTrue(c.description,
                            msg=f"Challenge {c.id!r} has empty description")

    def test_all_evaluation_criteria_are_lists(self):
        for c in _CHALLENGES:
            self.assertIsInstance(
                c.evaluation_criteria, list,
                msg=f"Challenge {c.id!r}: evaluation_criteria is not a list",
            )

    def test_all_evaluation_criteria_are_non_empty(self):
        for c in _CHALLENGES:
            self.assertGreater(
                len(c.evaluation_criteria), 0,
                msg=f"Challenge {c.id!r} has no evaluation criteria",
            )

    def test_all_competencies_assessed_are_lists(self):
        for c in _CHALLENGES:
            self.assertIsInstance(
                c.competencies_assessed, list,
                msg=f"Challenge {c.id!r}: competencies_assessed is not a list",
            )

    def test_all_competencies_assessed_are_non_empty(self):
        for c in _CHALLENGES:
            self.assertGreater(
                len(c.competencies_assessed), 0,
                msg=f"Challenge {c.id!r} has no competencies assessed",
            )

    def test_estimated_hours_is_float_or_none(self):
        for c in _CHALLENGES:
            if c.estimated_hours is not None:
                self.assertIsInstance(
                    c.estimated_hours, float,
                    msg=f"Challenge {c.id!r}: estimated_hours has wrong type",
                )

    def test_estimated_hours_positive_when_set(self):
        for c in _CHALLENGES:
            if c.estimated_hours is not None:
                self.assertGreater(
                    c.estimated_hours, 0,
                    msg=f"Challenge {c.id!r}: estimated_hours must be > 0",
                )


# ---------------------------------------------------------------------------
# Group 3 — filter_challenges: technology filter
# ---------------------------------------------------------------------------


class TestFilterChallengesByTechnology(unittest.TestCase):
    """Verifies that filtering by technology returns only matching items."""

    def test_python_challenges_exist(self):
        result = filter_challenges("Python", Level.BEGINNER, _CHALLENGES)
        self.assertGreater(len(result), 0)

    def test_all_python_results_have_correct_technology(self):
        for level in Level:
            result = filter_challenges("Python", level, _CHALLENGES)
            for c in result:
                self.assertEqual(c.technology, "Python",
                                 msg=f"Challenge {c.id!r} has wrong technology")

    def test_n8n_challenges_exist(self):
        result = filter_challenges("n8n", Level.BEGINNER, _CHALLENGES)
        self.assertGreater(len(result), 0)

    def test_all_n8n_results_have_correct_technology(self):
        for level in Level:
            result = filter_challenges("n8n", level, _CHALLENGES)
            for c in result:
                self.assertEqual(c.technology, "n8n")

    def test_ai_challenges_exist(self):
        result = filter_challenges("Artificial Intelligence",
                                   Level.BEGINNER, _CHALLENGES)
        self.assertGreater(len(result), 0)

    def test_ai_agents_challenges_exist(self):
        result = filter_challenges("AI Agents", Level.BEGINNER, _CHALLENGES)
        self.assertGreater(len(result), 0)

    def test_unknown_technology_returns_empty_list(self):
        result = filter_challenges("Rust", Level.BEGINNER, _CHALLENGES)
        self.assertEqual(result, [])

    def test_returns_list_type(self):
        result = filter_challenges("Python", Level.BEGINNER, _CHALLENGES)
        self.assertIsInstance(result, list)


# ---------------------------------------------------------------------------
# Group 4 — filter_challenges: level filter
# ---------------------------------------------------------------------------


class TestFilterChallengesByLevel(unittest.TestCase):
    """Verifies that filtering by level returns only matching items."""

    def test_beginner_results_have_beginner_level(self):
        result = filter_challenges("Python", Level.BEGINNER, _CHALLENGES)
        for c in result:
            self.assertEqual(c.level, Level.BEGINNER,
                             msg=f"Challenge {c.id!r} has wrong level")

    def test_intermediate_results_have_intermediate_level(self):
        result = filter_challenges("Python", Level.INTERMEDIATE, _CHALLENGES)
        for c in result:
            self.assertEqual(c.level, Level.INTERMEDIATE,
                             msg=f"Challenge {c.id!r} has wrong level")

    def test_advanced_results_have_advanced_level(self):
        result = filter_challenges("Python", Level.ADVANCED, _CHALLENGES)
        for c in result:
            self.assertEqual(c.level, Level.ADVANCED,
                             msg=f"Challenge {c.id!r} has wrong level")

    def test_beginner_and_advanced_are_disjoint_for_same_technology(self):
        beginner = {c.id for c in
                    filter_challenges("Python", Level.BEGINNER, _CHALLENGES)}
        advanced = {c.id for c in
                    filter_challenges("Python", Level.ADVANCED, _CHALLENGES)}
        self.assertEqual(beginner & advanced, set())

    def test_ai_has_intermediate_challenges(self):
        result = filter_challenges("Artificial Intelligence",
                                   Level.INTERMEDIATE, _CHALLENGES)
        self.assertGreater(len(result), 0)

    def test_ai_has_advanced_challenges(self):
        result = filter_challenges("Artificial Intelligence",
                                   Level.ADVANCED, _CHALLENGES)
        self.assertGreater(len(result), 0)


# ---------------------------------------------------------------------------
# Group 5 — filter_challenges: case-insensitive technology matching
# ---------------------------------------------------------------------------


class TestFilterChallengesCaseInsensitive(unittest.TestCase):
    """Verifies that technology matching ignores letter case."""

    def test_python_lowercase(self):
        result = filter_challenges("python", Level.BEGINNER, _CHALLENGES)
        self.assertGreater(len(result), 0)

    def test_python_uppercase(self):
        result = filter_challenges("PYTHON", Level.BEGINNER, _CHALLENGES)
        self.assertGreater(len(result), 0)

    def test_python_mixed_case(self):
        result = filter_challenges("PyThOn", Level.BEGINNER, _CHALLENGES)
        self.assertGreater(len(result), 0)

    def test_case_insensitive_same_count_as_exact(self):
        exact = filter_challenges("Python", Level.BEGINNER, _CHALLENGES)
        lower = filter_challenges("python", Level.BEGINNER, _CHALLENGES)
        upper = filter_challenges("PYTHON", Level.BEGINNER, _CHALLENGES)
        self.assertEqual(len(exact), len(lower))
        self.assertEqual(len(exact), len(upper))

    def test_n8n_uppercase(self):
        result = filter_challenges("N8N", Level.BEGINNER, _CHALLENGES)
        self.assertGreater(len(result), 0)

    def test_ai_agents_case_insensitive(self):
        result = filter_challenges("ai agents", Level.BEGINNER, _CHALLENGES)
        self.assertGreater(len(result), 0)

    def test_artificial_intelligence_case_insensitive(self):
        result = filter_challenges(
            "ARTIFICIAL INTELLIGENCE", Level.BEGINNER, _CHALLENGES
        )
        self.assertGreater(len(result), 0)


# ---------------------------------------------------------------------------
# Group 6 — generate_challenge: invalid input handling
# ---------------------------------------------------------------------------


class TestGenerateChallengeInvalidInput(unittest.TestCase):
    """Verifies that invalid input is rejected gracefully."""

    def test_empty_string_prints_error(self):
        output = _capture("", Level.BEGINNER)
        self.assertIn("Error", output)

    def test_whitespace_only_prints_error(self):
        output = _capture("   ", Level.BEGINNER)
        self.assertIn("Error", output)

    def test_newline_only_prints_error(self):
        output = _capture("\n", Level.BEGINNER)
        self.assertIn("Error", output)

    def test_empty_input_no_challenge_output(self):
        output = _capture("", Level.BEGINNER)
        self.assertNotIn("Title", output)

    def test_whitespace_input_no_challenge_output(self):
        output = _capture("   ", Level.BEGINNER)
        self.assertNotIn("Title", output)


# ---------------------------------------------------------------------------
# Group 7 — generate_challenge: no results found
# ---------------------------------------------------------------------------


class TestGenerateChallengeNotFound(unittest.TestCase):
    """Verifies the 'not found' message when no challenge matches."""

    def test_unknown_technology_prints_not_found(self):
        output = _capture("Rust", Level.BEGINNER)
        self.assertIn("No challenge found", output)

    def test_unknown_technology_mentions_technology_name(self):
        output = _capture("Rust", Level.BEGINNER)
        self.assertIn("Rust", output)

    def test_unknown_technology_mentions_level(self):
        output = _capture("Rust", Level.BEGINNER)
        self.assertIn("beginner", output)

    def test_unknown_technology_no_title_output(self):
        output = _capture("Rust", Level.BEGINNER)
        self.assertNotIn("Title      :", output)

    def test_another_unknown_technology(self):
        output = _capture("Kotlin", Level.ADVANCED)
        self.assertIn("No challenge found", output)


# ---------------------------------------------------------------------------
# Group 8 — generate_challenge: successful output content
# ---------------------------------------------------------------------------


class TestGenerateChallengeOutput(unittest.TestCase):
    """Verifies that a found challenge prints all expected sections."""

    @classmethod
    def setUpClass(cls):
        cls.output = _capture("Python", Level.BEGINNER)

    def test_prints_title(self):
        self.assertIn("Title      :", self.output)

    def test_prints_technology(self):
        self.assertIn("Technology : Python", self.output)

    def test_prints_level(self):
        self.assertIn("Level      : beginner", self.output)

    def test_prints_description_header(self):
        self.assertIn("Description", self.output)

    def test_prints_evaluation_criteria_header(self):
        self.assertIn("Evaluation criteria", self.output)

    def test_prints_competencies_assessed_header(self):
        self.assertIn("Competencies assessed", self.output)

    def test_prints_estimated_hours(self):
        self.assertIn("Est. Hours", self.output)

    def test_n8n_challenge_output(self):
        output = _capture("n8n", Level.BEGINNER)
        self.assertIn("Technology : n8n", output)

    def test_ai_agents_challenge_output(self):
        output = _capture("AI Agents", Level.BEGINNER)
        self.assertIn("Technology : AI Agents", output)

    def test_ai_intermediate_challenge_output(self):
        output = _capture("Artificial Intelligence", Level.INTERMEDIATE)
        self.assertIn("Level      : intermediate", output)


# ---------------------------------------------------------------------------
# Group 9 — Data immutability
# ---------------------------------------------------------------------------


class TestDataImmutability(unittest.TestCase):
    """Verifies that no function mutates the loaded challenges."""

    def test_challenge_list_length_unchanged_after_filter(self):
        pool = load_challenges()
        count_before = len(pool)
        filter_challenges("Python", Level.BEGINNER, pool)
        self.assertEqual(len(pool), count_before)

    def test_challenge_technology_unchanged_after_filter(self):
        pool = load_challenges()
        python_challenge = next(
            c for c in pool if c.technology == "Python"
        )
        tech_before = python_challenge.technology
        filter_challenges("python", Level.BEGINNER, pool)
        self.assertEqual(python_challenge.technology, tech_before)

    def test_evaluation_criteria_list_unchanged_after_filter(self):
        pool = load_challenges()
        first = pool[0]
        snapshot = list(first.evaluation_criteria)
        filter_challenges(first.technology, first.level, pool)
        self.assertEqual(first.evaluation_criteria, snapshot)

    def test_competencies_assessed_unchanged_after_filter(self):
        pool = load_challenges()
        first = pool[0]
        snapshot = list(first.competencies_assessed)
        filter_challenges(first.technology, first.level, pool)
        self.assertEqual(first.competencies_assessed, snapshot)

    def test_filter_returns_new_list(self):
        pool = load_challenges()
        result = filter_challenges("Python", Level.BEGINNER, pool)
        self.assertIsNot(result, pool)

    def test_generate_challenge_does_not_mutate_pool(self):
        pool = load_challenges()
        ids_before = [c.id for c in pool]
        # Patch load_challenges inside the command module to use our pool
        with patch("commands.desafio.load_challenges", return_value=pool):
            generate_challenge("Python", Level.BEGINNER)
        self.assertEqual([c.id for c in pool], ids_before)

    def test_challenge_level_unchanged_after_generate(self):
        pool = load_challenges()
        python_challenge = next(
            c for c in pool
            if c.technology == "Python" and c.level == Level.BEGINNER
        )
        level_before = python_challenge.level
        with patch("commands.desafio.load_challenges", return_value=pool):
            generate_challenge("Python", Level.BEGINNER)
        self.assertEqual(python_challenge.level, level_before)


# ---------------------------------------------------------------------------
# Group 10 — ID validity and uniqueness
# ---------------------------------------------------------------------------


class TestChallengeIdValidity(unittest.TestCase):
    """Verifies that all challenge IDs are valid and unique."""

    def test_all_ids_are_strings(self):
        for c in _CHALLENGES:
            self.assertIsInstance(c.id, str,
                                  msg=f"Challenge has non-string id: {c!r}")

    def test_all_ids_are_non_empty(self):
        for c in _CHALLENGES:
            self.assertTrue(c.id.strip(),
                            msg=f"Challenge has blank id: {c!r}")

    def test_ids_are_unique(self):
        ids = [c.id for c in _CHALLENGES]
        self.assertEqual(len(ids), len(set(ids)),
                         msg="Duplicate challenge IDs detected")

    def test_specific_ids_exist(self):
        expected_ids = [
            "challenge-python-beginner-01",
            "challenge-python-beginner-02",
            "challenge-python-intermediate-01",
            "challenge-python-advanced-01",
            "challenge-ai-beginner-01",
            "challenge-ai-intermediate-01",
            "challenge-ai-advanced-01",
            "challenge-agents-beginner-01",
            "challenge-agents-intermediate-01",
            "challenge-agents-advanced-01",
            "challenge-n8n-beginner-01",
            "challenge-n8n-intermediate-01",
            "challenge-n8n-advanced-01",
        ]
        for expected_id in expected_ids:
            self.assertIn(expected_id, _CHALLENGES_BY_ID,
                          msg=f"Expected challenge ID not found: {expected_id!r}")

    def test_four_technologies_covered(self):
        technologies = {c.technology for c in _CHALLENGES}
        for expected_tech in (
            "Python", "Artificial Intelligence", "AI Agents", "n8n"
        ):
            self.assertIn(expected_tech, technologies,
                          msg=f"Technology {expected_tech!r} not found in challenges")

    def test_all_three_levels_covered(self):
        levels = {c.level for c in _CHALLENGES}
        for expected_level in Level:
            self.assertIn(expected_level, levels,
                          msg=f"Level {expected_level.value!r} not covered")


if __name__ == "__main__":
    unittest.main()
