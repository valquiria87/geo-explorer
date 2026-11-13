"""
tests/test_competency_analyzer.py
----------------------------------
Unit tests for core/competency_analyzer.py.

Every test function uses only in-memory objects built from scratch — no file
I/O, no mocks.  This keeps the suite fast and isolated.

Coverage targets
~~~~~~~~~~~~~~~~
- normalize()
- _level_rank()
- _priority()
- _recommendation_id()
- _build_recommendation() — all six branches
- _build_analysis()       — matched/missing/extra sets, coverage_index,
                            recommendation count, ordering, name preservation
- analyze_profile()       — technology filtering (with/without interests)
"""

from __future__ import annotations

import pytest

from core.competency_analyzer import (
    _build_analysis,
    _build_recommendation,
    _level_rank,
    _priority,
    _recommendation_id,
    analyze_profile,
    normalize,
)
from core.models import (
    Challenge,
    CompetencyAnalysis,
    LearnerProfile,
    LearningPath,
    LearningStep,
    Level,
    Recommendation,
    RecommendationType,
)


# ===========================================================================
# Fixtures — minimal in-memory domain objects
# ===========================================================================


def _make_step(order: int, competencies: list[str], title: str = "") -> LearningStep:
    return LearningStep(
        title=title or f"Step {order}",
        description="",
        competencies_developed=competencies,
        order=order,
    )


def _make_path(
    pid: str,
    technology: str,
    level: Level,
    competencies: list[str],
    steps: list[LearningStep] | None = None,
) -> LearningPath:
    return LearningPath(
        id=pid,
        title=f"Path {pid}",
        technology=technology,
        level=level,
        steps=steps or [],
        competencies=competencies,
        description="",
    )


def _make_challenge(
    cid: str,
    technology: str,
    level: Level,
    competencies: list[str],
) -> Challenge:
    return Challenge(
        id=cid,
        title=f"Challenge {cid}",
        technology=technology,
        level=level,
        description="",
        evaluation_criteria=[],
        competencies_assessed=competencies,
        estimated_hours=None,
    )


def _make_profile(
    current_competencies: list[str],
    level: Level = Level.BEGINNER,
    interests: list[str] | None = None,
) -> LearnerProfile:
    return LearnerProfile(
        id="learner-01",
        name="Test Learner",
        current_competencies=current_competencies,
        current_level=level,
        professional_goal="test goal",
        technologies_of_interest=interests if interests is not None else [],
    )


# ===========================================================================
# normalize()
# ===========================================================================


class TestNormalize:
    def test_strips_whitespace(self):
        assert normalize("  Python  ") == "python"

    def test_folds_to_lower(self):
        assert normalize("Python Basics") == "python basics"

    def test_empty_string(self):
        assert normalize("") == ""

    def test_already_normalized(self):
        assert normalize("exception handling") == "exception handling"

    def test_internal_spaces_preserved(self):
        # normalize does NOT collapse internal spaces — only strip + lower
        assert normalize("a  b") == "a  b"


# ===========================================================================
# _level_rank()
# ===========================================================================


class TestLevelRank:
    def test_beginner_is_1(self):
        assert _level_rank(Level.BEGINNER) == 1

    def test_intermediate_is_2(self):
        assert _level_rank(Level.INTERMEDIATE) == 2

    def test_advanced_is_3(self):
        assert _level_rank(Level.ADVANCED) == 3


# ===========================================================================
# _priority()
# ===========================================================================


class TestPriority:
    def test_three_or_more_steps_is_5(self):
        assert _priority(3, 0) == 5
        assert _priority(4, 0) == 5
        assert _priority(3, 5) == 5

    def test_two_steps_is_4(self):
        assert _priority(2, 0) == 4
        assert _priority(2, 10) == 4

    def test_one_step_with_challenge_is_3(self):
        assert _priority(1, 1) == 3
        assert _priority(1, 5) == 3

    def test_one_step_no_challenge_is_2(self):
        assert _priority(1, 0) == 2

    def test_zero_steps_is_1(self):
        assert _priority(0, 0) == 1
        assert _priority(0, 3) == 1


# ===========================================================================
# _recommendation_id()
# ===========================================================================


class TestRecommendationId:
    def test_basic(self):
        rid = _recommendation_id("learner-01", "exception handling")
        assert rid == "rec-learner-01-exception-handling"

    def test_special_chars_replaced(self):
        rid = _recommendation_id("l1", "Python syntax and semantics")
        assert rid == "rec-l1-python-syntax-and-semantics"

    def test_slash_replaced(self):
        rid = _recommendation_id("l1", "LangChain / LangGraph")
        assert rid == "rec-l1-langchain-langgraph"

    def test_uppercase_normalized(self):
        rid = _recommendation_id("l1", "AI Ethics")
        assert rid.startswith("rec-l1-ai-ethics")


# ===========================================================================
# _build_recommendation()
# ===========================================================================


class TestBuildRecommendation:
    """Tests for all six branches of _build_recommendation."""

    # --- Branch: 1 step, 1+ challenges → priority 3, type LEARNING_PATH ---

    def test_one_step_one_challenge_priority_3(self):
        step = _make_step(1, ["alpha"])
        path = _make_path("p1", "Python", Level.BEGINNER, ["alpha"], [step])
        ch = _make_challenge("ch1", "Python", Level.BEGINNER, ["alpha"])
        profile = _make_profile([], Level.BEGINNER)

        rec = _build_recommendation("alpha", path, [ch], profile)

        assert rec.priority == 3
        assert rec.recommendation_type == RecommendationType.LEARNING_PATH
        assert rec.target_id == "p1"
        assert "alpha" in rec.rationale
        assert "Challenge ch1" in rec.rationale
        assert rec.competencies_to_develop == ["alpha"]

    # --- Branch: 1 step, 0 challenges → priority 2, type LEARNING_PATH ---

    def test_one_step_no_challenge_priority_2(self):
        step = _make_step(1, ["beta"])
        path = _make_path("p1", "Python", Level.BEGINNER, ["beta"], [step])
        profile = _make_profile([], Level.BEGINNER)

        rec = _build_recommendation("beta", path, [], profile)

        assert rec.priority == 2
        assert rec.recommendation_type == RecommendationType.LEARNING_PATH
        assert rec.target_id == "p1"

    # --- Branch: 2 steps → priority 4 ---

    def test_two_steps_priority_4(self):
        s1 = _make_step(1, ["gamma"])
        s2 = _make_step(2, ["gamma"])
        path = _make_path("p1", "Python", Level.BEGINNER, ["gamma"], [s1, s2])
        profile = _make_profile([], Level.BEGINNER)

        rec = _build_recommendation("gamma", path, [], profile)

        assert rec.priority == 4
        assert rec.recommendation_type == RecommendationType.LEARNING_PATH

    # --- Branch: 3+ steps → priority 5 ---

    def test_three_steps_priority_5(self):
        steps = [_make_step(i, ["delta"]) for i in range(1, 4)]
        path = _make_path("p1", "Python", Level.BEGINNER, ["delta"], steps)
        profile = _make_profile([], Level.BEGINNER)

        rec = _build_recommendation("delta", path, [], profile)

        assert rec.priority == 5

    # --- Branch: 0 steps, 1+ challenges → priority 1, type CHALLENGE ---

    def test_no_step_with_challenge_priority_1_type_challenge(self):
        path = _make_path("p1", "Python", Level.BEGINNER, ["epsilon"], [])
        ch = _make_challenge("ch1", "Python", Level.BEGINNER, ["epsilon"])
        profile = _make_profile([], Level.BEGINNER)

        rec = _build_recommendation("epsilon", path, [ch], profile)

        assert rec.priority == 1
        assert rec.recommendation_type == RecommendationType.CHALLENGE
        assert rec.target_id == "ch1"

    # --- Branch: 0 steps, 0 challenges → priority 1, type LEARNING_PATH ---

    def test_no_step_no_challenge_priority_1_type_path(self):
        path = _make_path("p1", "Python", Level.BEGINNER, ["zeta"], [])
        profile = _make_profile([], Level.BEGINNER)

        rec = _build_recommendation("zeta", path, [], profile)

        assert rec.priority == 1
        assert rec.recommendation_type == RecommendationType.LEARNING_PATH
        assert rec.target_id == "p1"
        assert "não possui etapa ou desafio" in rec.rationale

    # --- Rationale language: must NOT claim verified mastery ---

    def test_rationale_does_not_claim_mastery(self):
        step = _make_step(1, ["alpha"])
        path = _make_path("p1", "Python", Level.BEGINNER, ["alpha"], [step])
        profile = _make_profile([], Level.BEGINNER)

        rec = _build_recommendation("alpha", path, [], profile)

        rationale_lower = rec.rationale.lower()
        assert "domina" not in rationale_lower
        assert "não foi declarada" in rec.rationale

    # --- Original casing preserved in competencies_to_develop ---

    def test_original_casing_in_competencies_to_develop(self):
        step = _make_step(1, ["Python Basics"])
        path = _make_path("p1", "Python", Level.BEGINNER, ["Python Basics"], [step])
        profile = _make_profile([], Level.BEGINNER)

        rec = _build_recommendation("Python Basics", path, [], profile)

        assert rec.competencies_to_develop == ["Python Basics"]  # NOT "python basics"


# ===========================================================================
# Challenge proximity / deterministic selection
# ===========================================================================


class TestChallengeProximity:
    """Tests for the level-distance challenge selection when n_steps == 0."""

    def _path_no_step(self, tech: str = "Python") -> LearningPath:
        return _make_path("p1", tech, Level.BEGINNER, ["comp-x"], [])

    def test_beginner_learner_prefers_beginner_challenge(self):
        path = self._path_no_step()
        ch_beg = _make_challenge("ch-beg", "Python", Level.BEGINNER, ["comp-x"])
        ch_int = _make_challenge("ch-int", "Python", Level.INTERMEDIATE, ["comp-x"])
        profile = _make_profile([], Level.BEGINNER)

        rec = _build_recommendation("comp-x", path, [ch_beg, ch_int], profile)

        assert rec.target_id == "ch-beg"

    def test_intermediate_learner_equidistant_uses_id_asc(self):
        """INTERMEDIATE learner: BEGINNER(dist=1) and ADVANCED(dist=1) → pick by id ASC."""
        path = self._path_no_step()
        ch_adv = _make_challenge("ch-adv", "Python", Level.ADVANCED, ["comp-x"])
        ch_beg = _make_challenge("ch-beg", "Python", Level.BEGINNER, ["comp-x"])
        profile = _make_profile([], Level.INTERMEDIATE)

        rec = _build_recommendation("comp-x", path, [ch_adv, ch_beg], profile)

        # Both have distance 1; "ch-adv" < "ch-beg" lexicographically
        assert rec.target_id == "ch-adv"

    def test_advanced_learner_only_beginner_available(self):
        """Only BEGINNER challenge available → must be selected without crash."""
        path = self._path_no_step()
        ch = _make_challenge("ch-beg", "Python", Level.BEGINNER, ["comp-x"])
        profile = _make_profile([], Level.ADVANCED)

        rec = _build_recommendation("comp-x", path, [ch], profile)

        assert rec.target_id == "ch-beg"

    def test_rationale_lists_all_challenges_even_when_target_is_closest(self):
        """target_id is closest, but ALL challenges appear in rationale."""
        path = self._path_no_step()
        ch1 = _make_challenge("ch-beg", "Python", Level.BEGINNER, ["comp-x"])
        ch2 = _make_challenge("ch-int", "Python", Level.INTERMEDIATE, ["comp-x"])
        profile = _make_profile([], Level.BEGINNER)

        rec = _build_recommendation("comp-x", path, [ch1, ch2], profile)

        # target = closest = ch-beg (beginner learner)
        assert rec.target_id == "ch-beg"
        # Both titles must appear in rationale
        assert "Challenge ch-beg" in rec.rationale
        assert "Challenge ch-int" in rec.rationale

    def test_different_technology_challenges_excluded(self):
        """Challenges for a different technology must not be candidates."""
        path = self._path_no_step("Python")
        ch_py = _make_challenge("ch-py", "Python", Level.BEGINNER, ["comp-x"])
        ch_ai = _make_challenge("ch-ai", "Artificial Intelligence", Level.BEGINNER, ["comp-x"])
        profile = _make_profile([], Level.BEGINNER)

        rec = _build_recommendation("comp-x", path, [ch_py, ch_ai], profile)

        assert rec.target_id == "ch-py"


# ===========================================================================
# _build_analysis() — set comparisons
# ===========================================================================


class TestBuildAnalysis:
    def _basic_setup(self):
        step1 = _make_step(1, ["A", "B"])
        step2 = _make_step(2, ["C"])
        path = _make_path("p1", "Python", Level.BEGINNER, ["A", "B", "C"], [step1, step2])
        return path

    def test_full_match(self):
        path = self._basic_setup()
        profile = _make_profile(["A", "B", "C"])

        analysis = _build_analysis(profile, path, [])

        assert set(analysis.matched_competencies) == {"A", "B", "C"}
        assert analysis.missing_competencies == []
        assert analysis.extra_competencies == []
        assert analysis.coverage_index == pytest.approx(1.0)
        assert analysis.recommendations == []

    def test_zero_match(self):
        path = self._basic_setup()
        profile = _make_profile([])

        analysis = _build_analysis(profile, path, [])

        assert analysis.matched_competencies == []
        assert set(analysis.missing_competencies) == {"A", "B", "C"}
        assert analysis.extra_competencies == []
        assert analysis.coverage_index == pytest.approx(0.0)
        assert len(analysis.recommendations) == 3

    def test_partial_match(self):
        path = self._basic_setup()
        profile = _make_profile(["A", "X"])

        analysis = _build_analysis(profile, path, [])

        assert analysis.matched_competencies == ["A"]
        assert set(analysis.missing_competencies) == {"B", "C"}
        assert analysis.extra_competencies == ["X"]
        assert analysis.coverage_index == pytest.approx(1 / 3)

    def test_extra_competencies(self):
        path = self._basic_setup()
        profile = _make_profile(["A", "B", "C", "D", "E"])

        analysis = _build_analysis(profile, path, [])

        assert set(analysis.extra_competencies) == {"D", "E"}

    def test_empty_path_competencies_no_division_by_zero(self):
        path = _make_path("p1", "Python", Level.BEGINNER, [], [])
        profile = _make_profile(["A"])

        analysis = _build_analysis(profile, path, [])

        assert analysis.coverage_index == pytest.approx(0.0)
        assert analysis.missing_competencies == []
        assert analysis.matched_competencies == []

    def test_one_recommendation_per_missing_competency(self):
        """Exactly N recommendations for N missing competencies."""
        path = self._basic_setup()
        profile = _make_profile([])

        analysis = _build_analysis(profile, path, [])

        assert len(analysis.recommendations) == len(analysis.missing_competencies)

    def test_no_duplicate_recommendations(self):
        """Even when a competency appears in multiple steps, only one rec."""
        s1 = _make_step(1, ["shared", "A"])
        s2 = _make_step(2, ["shared", "B"])
        path = _make_path("p1", "Python", Level.BEGINNER, ["shared", "A", "B"], [s1, s2])
        profile = _make_profile([])

        analysis = _build_analysis(profile, path, [])

        comp_names = [r.competencies_to_develop[0] for r in analysis.recommendations]
        assert len(comp_names) == len(set(comp_names))  # no duplicates

    # --- Name preservation ---

    def test_matched_uses_path_original_casing(self):
        step = _make_step(1, ["Python Basics"])
        path = _make_path("p1", "Python", Level.BEGINNER, ["Python Basics"], [step])
        profile = _make_profile(["python basics"])  # lower-case in profile

        analysis = _build_analysis(profile, path, [])

        # matched should use path's name, not profile's
        assert "Python Basics" in analysis.matched_competencies
        assert "python basics" not in analysis.matched_competencies

    def test_missing_uses_path_original_casing(self):
        step = _make_step(1, ["Python Basics"])
        path = _make_path("p1", "Python", Level.BEGINNER, ["Python Basics"], [step])
        profile = _make_profile([])

        analysis = _build_analysis(profile, path, [])

        assert "Python Basics" in analysis.missing_competencies

    def test_extra_uses_profile_original_casing(self):
        path = _make_path("p1", "Python", Level.BEGINNER, ["A"], [_make_step(1, ["A"])])
        profile = _make_profile(["A", "My Custom Skill"])

        analysis = _build_analysis(profile, path, [])

        assert "My Custom Skill" in analysis.extra_competencies

    # --- Recommendation ordering ---

    def test_recommendations_ordered_priority_desc(self):
        """Higher-priority recommendations come first."""
        s1 = _make_step(1, ["alpha", "beta"])  # alpha in 1 step, beta in 1 step
        s2 = _make_step(2, ["alpha"])           # alpha now in 2 steps → priority 4
        path = _make_path("p1", "Python", Level.BEGINNER, ["alpha", "beta"], [s1, s2])
        profile = _make_profile([])

        analysis = _build_analysis(profile, path, [])

        priorities = [r.priority for r in analysis.recommendations]
        assert priorities == sorted(priorities, reverse=True)

    def test_same_priority_ordered_by_first_step_asc(self):
        """Within same priority, earlier first step comes first."""
        s1 = _make_step(1, ["early"])
        s2 = _make_step(3, ["late"])
        path = _make_path("p1", "Python", Level.BEGINNER, ["early", "late"], [s1, s2])
        profile = _make_profile([])

        analysis = _build_analysis(profile, path, [])

        # Both have priority 2 (1 step, no challenges); "early" step order < "late"
        rec_comps = [r.competencies_to_develop[0] for r in analysis.recommendations]
        assert rec_comps.index("early") < rec_comps.index("late")

    def test_no_step_sentinel_sorts_after_steps(self):
        """Competencies with no associated step sort after those with steps."""
        s1 = _make_step(1, ["with-step"])
        # "orphan" has no step
        path = _make_path("p1", "Python", Level.BEGINNER, ["with-step", "orphan"], [s1])
        profile = _make_profile([])

        analysis = _build_analysis(profile, path, [])

        rec_comps = [r.competencies_to_develop[0] for r in analysis.recommendations]
        # "with-step" has priority 2 (1 step, no challenge); "orphan" has priority 1
        # Higher priority comes first
        assert rec_comps.index("with-step") < rec_comps.index("orphan")


# ===========================================================================
# analyze_profile() — technology filtering
# ===========================================================================


class TestAnalyzeProfile:
    def _two_paths(self):
        p1 = _make_path("py-p", "Python", Level.BEGINNER, ["A"], [_make_step(1, ["A"])])
        p2 = _make_path("ai-p", "Artificial Intelligence", Level.INTERMEDIATE, ["B"],
                        [_make_step(1, ["B"])])
        return p1, p2

    def test_no_interests_analyses_all_paths(self):
        p1, p2 = self._two_paths()
        profile = _make_profile([], interests=[])

        results = analyze_profile(profile, [p1, p2], [])

        assert len(results) == 2
        path_ids = {r.path.id for r in results}
        assert path_ids == {"py-p", "ai-p"}

    def test_with_interest_filters_to_matching_path(self):
        p1, p2 = self._two_paths()
        profile = _make_profile([], interests=["Python"])

        results = analyze_profile(profile, [p1, p2], [])

        assert len(results) == 1
        assert results[0].path.id == "py-p"

    def test_interest_matching_is_case_insensitive(self):
        p1, _ = self._two_paths()
        profile = _make_profile([], interests=["python"])  # lower-case

        results = analyze_profile(profile, [p1], [])

        assert len(results) == 1

    def test_interest_with_no_matching_path_returns_empty(self):
        p1, _ = self._two_paths()
        profile = _make_profile([], interests=["n8n"])

        results = analyze_profile(profile, [p1], [])

        assert results == []

    def test_returns_competency_analysis_instances(self):
        p1, _ = self._two_paths()
        profile = _make_profile(["A"], interests=["Python"])

        results = analyze_profile(profile, [p1], [])

        assert all(isinstance(r, CompetencyAnalysis) for r in results)

    def test_input_not_mutated(self):
        p1, _ = self._two_paths()
        original_comps = ["A", "extra"]
        profile = _make_profile(list(original_comps), interests=["Python"])

        analyze_profile(profile, [p1], [])

        assert profile.current_competencies == original_comps

    def test_multiple_interests_analyses_all_matching(self):
        p1, p2 = self._two_paths()
        profile = _make_profile([], interests=["Python", "Artificial Intelligence"])

        results = analyze_profile(profile, [p1, p2], [])

        assert len(results) == 2


# ===========================================================================
# Integration: real data files
# ===========================================================================


class TestIntegrationRealData:
    """Smoke tests that load the actual JSON files and run a full analysis."""

    @pytest.fixture(autouse=True)
    def _load_data(self):
        from core.data_loader import load_learning_paths
        from commands.desafio import load_challenges
        self.paths = load_learning_paths()
        self.challenges = load_challenges()

    def test_virtual_environments_has_priority_4_in_python_path(self):
        """Real-data audit confirmed virtual_environments appears in 2 Python steps."""
        profile = _make_profile([], interests=["Python"])
        results = analyze_profile(profile, self.paths, self.challenges)
        assert results, "Expected Python path analysis"
        python_analysis = results[0]

        rec_map = {
            r.competencies_to_develop[0]: r
            for r in python_analysis.recommendations
        }
        assert "virtual environments" in rec_map, "Expected 'virtual environments' to be missing"
        assert rec_map["virtual environments"].priority == 4

    def test_one_rec_per_missing_competency_real_data(self):
        """For every path, #recommendations == #missing_competencies."""
        profile = _make_profile([])
        results = analyze_profile(profile, self.paths, self.challenges)
        for analysis in results:
            assert len(analysis.recommendations) == len(analysis.missing_competencies), (
                f"Mismatch for path {analysis.path.id}"
            )

    def test_full_match_python_learner_no_recommendations(self):
        """A learner who declares all Python path competencies gets zero recommendations."""
        python_path = next(p for p in self.paths if p.technology == "Python")
        profile = _make_profile(
            list(python_path.competencies),
            interests=["Python"],
        )
        results = analyze_profile(profile, self.paths, self.challenges)
        assert results[0].recommendations == []
        assert results[0].coverage_index == pytest.approx(1.0)

    def test_original_casing_preserved_in_results(self):
        """Competency names in results match the original casing from JSON."""
        python_path = next(p for p in self.paths if p.technology == "Python")
        profile = _make_profile([], interests=["Python"])
        results = analyze_profile(profile, self.paths, self.challenges)
        analysis = results[0]
        # missing competencies should come directly from path.competencies
        for comp in analysis.missing_competencies:
            assert comp in python_path.competencies, (
                f"'{comp}' not in original path.competencies — casing may have changed"
            )

    def test_exception_handling_challenge_rationale_lists_all_challenges(self):
        """
        'exception handling' in Python has 4 challenges in real data.
        The rationale for that recommendation must mention all 4 titles.
        """
        profile = _make_profile([], interests=["Python"])
        results = analyze_profile(profile, self.paths, self.challenges)
        python_analysis = results[0]
        rec_map = {
            r.competencies_to_develop[0]: r
            for r in python_analysis.recommendations
        }
        # exception handling appears in a step (Step 3) so it won't be type CHALLENGE,
        # but all challenge titles should appear in the rationale
        assert "exception handling" in rec_map
        rec = rec_map["exception handling"]
        # All 4 challenge titles must appear in rationale
        expected_titles = [
            "Build a To-Do List CLI",
            "CSV Grade Analyser",
            "REST API Wrapper with Caching",
            "Async Web Scraper with Rate Limiting",
        ]
        for title in expected_titles:
            assert title in rec.rationale, (
                f"Expected challenge title '{title}' in rationale"
            )
