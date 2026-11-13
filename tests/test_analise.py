"""
tests/test_analise.py
----------------------
Tests for commands/analise.py.

These tests call show_competency_analysis() with a pre-built profile_data
dict and inspect what is printed to stdout.  The real JSON data files are
used so the output reflects the actual learning paths and challenges.
"""

from __future__ import annotations

import pytest

from commands.analise import show_competency_analysis, _format_analysis, _coverage_bar
from core.models import Level


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _profile_data(
    competencies: list[str] | None = None,
    level: Level = Level.BEGINNER,
    goal: str = "Test goal",
    interests: list[str] | None = None,
    name: str | None = "Test User",
    learner_id: str = "learner-test",
) -> dict:
    return {
        "id": learner_id,
        "name": name,
        "current_competencies": competencies if competencies is not None else [],
        "current_level": level,
        "professional_goal": goal,
        "technologies_of_interest": interests if interests is not None else [],
        "notes": "",
    }


# ===========================================================================
# _coverage_bar()
# ===========================================================================


class TestCoverageBar:
    def test_zero_produces_empty_bar(self):
        bar = _coverage_bar(0.0, width=4)
        assert bar == "[░░░░]"

    def test_full_produces_filled_bar(self):
        bar = _coverage_bar(1.0, width=4)
        assert bar == "[████]"

    def test_half_produces_half_filled(self):
        bar = _coverage_bar(0.5, width=4)
        assert bar == "[██░░]"


# ===========================================================================
# show_competency_analysis() — stdout content
# ===========================================================================


class TestShowCompetencyAnalysis:
    def test_header_contains_learner_name(self, capsys):
        show_competency_analysis(_profile_data(name="Ana Lima", interests=["Python"]))
        out = capsys.readouterr().out
        assert "Ana Lima" in out

    def test_header_uses_id_when_name_is_none(self, capsys):
        show_competency_analysis(
            _profile_data(name=None, learner_id="learner-42", interests=["Python"])
        )
        out = capsys.readouterr().out
        assert "learner-42" in out

    def test_professional_goal_printed(self, capsys):
        show_competency_analysis(
            _profile_data(goal="Become a backend developer", interests=["Python"])
        )
        out = capsys.readouterr().out
        assert "Become a backend developer" in out

    def test_coverage_index_printed(self, capsys):
        show_competency_analysis(_profile_data(interests=["Python"]))
        out = capsys.readouterr().out
        assert "cobertura declarada" in out

    def test_self_declared_warning_printed(self, capsys):
        show_competency_analysis(_profile_data(interests=["Python"]))
        out = capsys.readouterr().out
        assert "auto-declaradas" in out

    def test_unknown_technology_interest_prints_no_trail_message(self, capsys):
        show_competency_analysis(_profile_data(interests=["UnknownTech999"]))
        out = capsys.readouterr().out
        assert "Nenhuma trilha encontrada" in out

    def test_empty_competencies_shows_all_missing(self, capsys):
        show_competency_analysis(_profile_data(competencies=[], interests=["Python"]))
        out = capsys.readouterr().out
        assert "não declaradas no perfil" in out

    def test_full_match_shows_no_missing(self, capsys):
        from core.data_loader import load_learning_paths
        paths = load_learning_paths()
        python_path = next(p for p in paths if p.technology == "Python")
        data = _profile_data(
            competencies=list(python_path.competencies),
            interests=["Python"],
        )
        show_competency_analysis(data)
        out = capsys.readouterr().out
        assert "Nenhuma recomendação" in out or "cobre toda a trilha" in out

    def test_no_interests_analyses_multiple_paths(self, capsys):
        show_competency_analysis(_profile_data(interests=[]))
        out = capsys.readouterr().out
        # With no interest filter, all 4 paths should appear — check at least 2 technologies
        assert "Python" in out
        assert "n8n" in out

    def test_output_does_not_use_normalised_lowercase_names(self, capsys):
        """Competency names in output must preserve original casing."""
        show_competency_analysis(
            _profile_data(
                competencies=["Python syntax and semantics"],
                interests=["Python"],
            )
        )
        out = capsys.readouterr().out
        # "Python syntax and semantics" should appear as-is, not all-lower
        assert "Python syntax and semantics" in out

    def test_recommendations_present_when_missing_competencies(self, capsys):
        show_competency_analysis(_profile_data(competencies=[], interests=["Python"]))
        out = capsys.readouterr().out
        assert "Próximos passos recomendados" in out

    def test_priority_labels_present_in_output(self, capsys):
        show_competency_analysis(_profile_data(competencies=[], interests=["Python"]))
        out = capsys.readouterr().out
        assert "Prioridade" in out

    def test_level_shown_in_header(self, capsys):
        show_competency_analysis(
            _profile_data(level=Level.INTERMEDIATE, interests=["Python"])
        )
        out = capsys.readouterr().out
        assert "intermediate" in out

    def test_extra_competencies_shown_when_present(self, capsys):
        show_competency_analysis(
            _profile_data(
                competencies=["Python syntax and semantics", "My Unique Skill XYZ"],
                interests=["Python"],
            )
        )
        out = capsys.readouterr().out
        assert "My Unique Skill XYZ" in out

    def test_no_crash_on_empty_competencies_all_paths(self, capsys):
        """Should not raise for empty competencies when all paths are analysed."""
        show_competency_analysis(_profile_data(competencies=[], interests=[]))
        out = capsys.readouterr().out
        assert out  # something was printed

    def test_multiple_paths_separated_in_output(self, capsys):
        """When two interests are given, both paths appear in output."""
        show_competency_analysis(
            _profile_data(interests=["Python", "n8n"], competencies=[])
        )
        out = capsys.readouterr().out
        assert "Python" in out
        assert "n8n" in out


# ===========================================================================
# _format_analysis() — unit tests for the formatter
# ===========================================================================


class TestFormatAnalysis:
    @pytest.fixture()
    def python_analysis(self):
        from core.data_loader import load_learning_paths
        from commands.desafio import load_challenges
        from core.competency_analyzer import analyze_profile

        paths = load_learning_paths()
        challenges = load_challenges()
        profile_data = _profile_data(
            competencies=["Python syntax and semantics", "control flow"],
            interests=["Python"],
        )
        from core.models import LearnerProfile
        profile = LearnerProfile(
            id=profile_data["id"],
            name=profile_data["name"],
            current_competencies=profile_data["current_competencies"],
            current_level=profile_data["current_level"],
            professional_goal=profile_data["professional_goal"],
            technologies_of_interest=profile_data["technologies_of_interest"],
        )
        results = analyze_profile(profile, paths, challenges)
        return results[0]

    def test_format_includes_path_title(self, python_analysis):
        text = _format_analysis(python_analysis)
        assert "Python Foundations" in text

    def test_format_includes_coverage_percentage(self, python_analysis):
        text = _format_analysis(python_analysis)
        assert "%" in text

    def test_format_warning_about_self_declared(self, python_analysis):
        text = _format_analysis(python_analysis)
        assert "auto-declaradas" in text

    def test_format_matched_section_present(self, python_analysis):
        text = _format_analysis(python_analysis)
        assert "✔" in text

    def test_format_missing_section_present(self, python_analysis):
        text = _format_analysis(python_analysis)
        assert "✗" in text

    def test_format_no_mastery_language(self, python_analysis):
        text = _format_analysis(python_analysis)
        assert "domina" not in text.lower()
