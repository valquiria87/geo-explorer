"""
tests/test_mcp_tools.py
-----------------------
Tests for the Geo-Explorer MCP server layer (Etapa 11).

Structure
~~~~~~~~~
Group A — Unit tests (direct calls to *_impl functions, no transport)
  TestFormatters                 — mcp_server/formatters.py
  TestGetLearningPathTool        — mcp_server/tools/trilha.py
  TestGetChallengeTool           — mcp_server/tools/desafio.py
  TestGenerateCertificateTool    — mcp_server/tools/certificado.py
  TestAnalyzeCompetenciesTool    — mcp_server/tools/analise.py

Group B — Integration tests (Client(mcp) in-process via MCP protocol)
  TestMCPProtocolIntegration     — registration, discovery, live tool calls

Run with:
    python -m pytest tests/test_mcp_tools.py -v
"""

from __future__ import annotations

import json
from datetime import date

import pytest

from core.models import Level, LearningPath, LearningStep, Challenge, CompetencyAnalysis
from mcp_server.formatters import (
    format_certificate,
    format_challenge,
    format_competency_analysis,
    format_learning_path,
)
from mcp_server.tools.analise import analyze_competencies_impl
from mcp_server.tools.certificado import generate_certificate_impl
from mcp_server.tools.desafio import get_challenge_impl
from mcp_server.tools.trilha import get_learning_path_impl
from mcp_server.server import create_server


# ===========================================================================
# Shared fixtures
# ===========================================================================


def _make_path() -> LearningPath:
    """Return a minimal LearningPath fixture."""
    step = LearningStep(
        title="Step One",
        description="Do something.",
        competencies_developed=["comp-a", "comp-b"],
        order=1,
    )
    return LearningPath(
        id="test-path-01",
        title="Test Path",
        technology="TestTech",
        level=Level.BEGINNER,
        steps=[step],
        competencies=["comp-a", "comp-b", "comp-c"],
        description="A test path.",
    )


def _make_challenge() -> Challenge:
    """Return a minimal Challenge fixture."""
    return Challenge(
        id="challenge-test-01",
        title="Test Challenge",
        technology="TestTech",
        level=Level.BEGINNER,
        description="Do the test.",
        evaluation_criteria=["Criterion 1", "Criterion 2"],
        competencies_assessed=["comp-a"],
        estimated_hours=2.0,
    )


def _make_cert() -> dict:
    """Return a minimal certificate dict (as built_certificate would return)."""
    return {
        "id": "abc-123",
        "participant": "Ana",
        "activity": "Python Foundations",
        "technology": "Python",
        "level": "beginner",
        "issued_on": date(2024, 6, 15),
        "competencies": ["control flow", "file I/O"],
        "disclaimer": "CERTIFICADO FICTÍCIO — SEM VALIDADE OFICIAL",
        "recognition": "Reconhecemos que Ana...",
    }


# ===========================================================================
# Group A — Unit tests: Formatters
# ===========================================================================


class TestFormatters:
    """format_* functions produce correct JSON-safe dicts."""

    def test_format_learning_path_keys(self):
        path = _make_path()
        result = format_learning_path(path)
        assert set(result.keys()) == {
            "id", "title", "technology", "level",
            "description", "steps", "competencies",
        }

    def test_format_learning_path_level_is_string(self):
        result = format_learning_path(_make_path())
        assert result["level"] == "beginner"
        assert isinstance(result["level"], str)

    def test_format_learning_path_steps_sorted(self):
        step1 = LearningStep("S2", "d", ["x"], order=2)
        step2 = LearningStep("S1", "d", ["y"], order=1)
        path = LearningPath(
            id="p", title="T", technology="X", level=Level.BEGINNER,
            steps=[step1, step2], competencies=["x", "y"],
        )
        result = format_learning_path(path)
        assert result["steps"][0]["order"] == 1
        assert result["steps"][1]["order"] == 2

    def test_format_learning_path_competencies_are_list(self):
        result = format_learning_path(_make_path())
        assert isinstance(result["competencies"], list)

    def test_format_challenge_keys(self):
        result = format_challenge(_make_challenge())
        assert set(result.keys()) == {
            "id", "title", "technology", "level", "description",
            "evaluation_criteria", "competencies_assessed", "estimated_hours",
        }

    def test_format_challenge_level_is_string(self):
        result = format_challenge(_make_challenge())
        assert result["level"] == "beginner"

    def test_format_challenge_estimated_hours_present(self):
        result = format_challenge(_make_challenge())
        assert result["estimated_hours"] == 2.0

    def test_format_challenge_estimated_hours_none(self):
        ch = _make_challenge()
        ch.estimated_hours = None
        result = format_challenge(ch)
        assert result["estimated_hours"] is None

    def test_format_certificate_issued_on_is_iso_string(self):
        result = format_certificate(_make_cert())
        assert result["issued_on"] == "2024-06-15"
        assert isinstance(result["issued_on"], str)

    def test_format_certificate_preserves_all_fields(self):
        result = format_certificate(_make_cert())
        assert result["participant"] == "Ana"
        assert result["disclaimer"] == "CERTIFICADO FICTÍCIO — SEM VALIDADE OFICIAL"
        assert result["competencies"] == ["control flow", "file I/O"]

    def test_format_competency_analysis_keys(self):
        from core.competency_analyzer import _build_analysis
        path = _make_path()
        from core.models import LearnerProfile
        profile = LearnerProfile(
            id="t", name=None, current_competencies=["comp-a"],
            current_level=Level.BEGINNER, professional_goal="",
        )
        analysis = _build_analysis(profile, path, [])
        result = format_competency_analysis(analysis)
        assert set(result.keys()) == {
            "path", "coverage_index", "matched_competencies",
            "missing_competencies", "extra_competencies", "recommendations",
        }

    def test_format_competency_analysis_coverage_index_float(self):
        from core.competency_analyzer import _build_analysis
        from core.models import LearnerProfile
        path = _make_path()
        profile = LearnerProfile(
            id="t", name=None, current_competencies=["comp-a"],
            current_level=Level.BEGINNER, professional_goal="",
        )
        analysis = _build_analysis(profile, path, [])
        result = format_competency_analysis(analysis)
        assert isinstance(result["coverage_index"], float)
        assert 0.0 <= result["coverage_index"] <= 1.0

    def test_format_competency_analysis_recommendations_list(self):
        from core.competency_analyzer import _build_analysis
        from core.models import LearnerProfile
        path = _make_path()
        profile = LearnerProfile(
            id="t", name=None, current_competencies=[],
            current_level=Level.BEGINNER, professional_goal="",
        )
        analysis = _build_analysis(profile, path, [])
        result = format_competency_analysis(analysis)
        assert isinstance(result["recommendations"], list)
        for rec in result["recommendations"]:
            assert "id" in rec
            assert "priority" in rec
            assert "recommendation_type" in rec


# ===========================================================================
# Group A — Unit tests: get_learning_path_impl
# ===========================================================================


class TestGetLearningPathTool:
    """get_learning_path_impl: success, not found, invalid input."""

    def test_returns_dict_for_known_technology(self):
        result = get_learning_path_impl("Python")
        assert isinstance(result, dict)
        assert "error" not in result

    def test_returns_title_for_python(self):
        result = get_learning_path_impl("Python")
        assert result["title"] == "Python Foundations"

    def test_returns_technology_for_python(self):
        result = get_learning_path_impl("Python")
        assert result["technology"] == "Python"

    def test_returns_level_as_string(self):
        result = get_learning_path_impl("Python")
        assert result["level"] == "beginner"
        assert isinstance(result["level"], str)

    def test_steps_list_present(self):
        result = get_learning_path_impl("Python")
        assert "steps" in result
        assert isinstance(result["steps"], list)
        assert len(result["steps"]) == 5

    def test_steps_sorted_by_order(self):
        result = get_learning_path_impl("Python")
        orders = [s["order"] for s in result["steps"]]
        assert orders == sorted(orders)

    def test_competencies_list_present(self):
        result = get_learning_path_impl("Python")
        assert "competencies" in result
        assert isinstance(result["competencies"], list)
        assert len(result["competencies"]) == 14

    def test_case_insensitive_lowercase(self):
        result = get_learning_path_impl("python")
        assert result["title"] == "Python Foundations"

    def test_case_insensitive_uppercase(self):
        result = get_learning_path_impl("PYTHON")
        assert result["title"] == "Python Foundations"

    def test_case_insensitive_mixed(self):
        result = get_learning_path_impl("pYtHoN")
        assert result["title"] == "Python Foundations"

    def test_n8n_found(self):
        result = get_learning_path_impl("n8n")
        assert "error" not in result
        assert result["technology"] == "n8n"

    def test_ai_agents_found(self):
        result = get_learning_path_impl("AI Agents")
        assert "error" not in result

    def test_unknown_technology_returns_error(self):
        result = get_learning_path_impl("Rust")
        assert "error" in result
        assert "Rust" in result["error"]

    def test_empty_string_returns_error(self):
        result = get_learning_path_impl("")
        assert "error" in result

    def test_whitespace_only_returns_error(self):
        result = get_learning_path_impl("   ")
        assert "error" in result

    def test_unknown_no_steps_key(self):
        result = get_learning_path_impl("Rust")
        assert "steps" not in result


# ===========================================================================
# Group A — Unit tests: get_challenge_impl
# ===========================================================================


class TestGetChallengeTool:
    """get_challenge_impl: success, not found, invalid level, empty input."""

    def test_returns_dict_for_python_beginner(self):
        result = get_challenge_impl("Python", "beginner")
        assert isinstance(result, dict)
        assert "error" not in result

    def test_returns_all_required_keys(self):
        result = get_challenge_impl("Python", "beginner")
        for key in ("id", "title", "technology", "level", "description",
                    "evaluation_criteria", "competencies_assessed"):
            assert key in result, f"Missing key: {key}"

    def test_level_is_string_in_result(self):
        result = get_challenge_impl("Python", "beginner")
        assert isinstance(result["level"], str)
        assert result["level"] == "beginner"

    def test_technology_matches(self):
        result = get_challenge_impl("Python", "beginner")
        assert result["technology"].lower() == "python"

    def test_case_insensitive_technology(self):
        result = get_challenge_impl("python", "beginner")
        assert "error" not in result

    def test_case_insensitive_level(self):
        result = get_challenge_impl("Python", "BEGINNER")
        assert "error" not in result

    def test_intermediate_level(self):
        result = get_challenge_impl("Python", "intermediate")
        assert "error" not in result

    def test_advanced_level(self):
        result = get_challenge_impl("Python", "advanced")
        assert "error" not in result

    def test_estimated_hours_float_or_none(self):
        result = get_challenge_impl("Python", "beginner")
        assert result["estimated_hours"] is None or isinstance(result["estimated_hours"], float)

    def test_unknown_technology_returns_error(self):
        result = get_challenge_impl("Rust", "beginner")
        assert "error" in result
        assert "Rust" in result["error"]

    def test_unknown_technology_mentions_level(self):
        result = get_challenge_impl("Rust", "beginner")
        assert "beginner" in result["error"]

    def test_invalid_level_returns_error(self):
        result = get_challenge_impl("Python", "expert")
        assert "error" in result

    def test_invalid_level_mentions_valid_values(self):
        result = get_challenge_impl("Python", "expert")
        assert "beginner" in result["error"]
        assert "intermediate" in result["error"]
        assert "advanced" in result["error"]

    def test_empty_technology_returns_error(self):
        result = get_challenge_impl("", "beginner")
        assert "error" in result

    def test_whitespace_technology_returns_error(self):
        result = get_challenge_impl("   ", "beginner")
        assert "error" in result

    def test_n8n_beginner_found(self):
        result = get_challenge_impl("n8n", "beginner")
        assert "error" not in result

    def test_ai_agents_intermediate_found(self):
        result = get_challenge_impl("AI Agents", "intermediate")
        assert "error" not in result


# ===========================================================================
# Group A — Unit tests: generate_certificate_impl
# ===========================================================================


class TestGenerateCertificateTool:
    """generate_certificate_impl: success, empty fields, invalid level."""

    def test_returns_dict_on_success(self):
        result = generate_certificate_impl(
            "Ana", "Python Foundations", "Python", "beginner", ["control flow"]
        )
        assert isinstance(result, dict)
        assert "error" not in result

    def test_all_required_keys_present(self):
        result = generate_certificate_impl(
            "Ana", "Python Foundations", "Python", "beginner", []
        )
        for key in ("id", "participant", "activity", "technology", "level",
                    "issued_on", "competencies", "disclaimer", "recognition"):
            assert key in result, f"Missing key: {key}"

    def test_disclaimer_always_present(self):
        result = generate_certificate_impl(
            "Bob", "n8n Automation", "n8n", "beginner", []
        )
        assert "FICTÍCIO" in result["disclaimer"]
        assert "VALIDADE OFICIAL" in result["disclaimer"]

    def test_issued_on_is_iso_string(self):
        result = generate_certificate_impl(
            "Ana", "Python Foundations", "Python", "beginner", []
        )
        issued = result["issued_on"]
        assert isinstance(issued, str)
        # Must parse as a date
        parsed = date.fromisoformat(issued)
        assert parsed is not None

    def test_competencies_preserved(self):
        comps = ["control flow", "file I/O"]
        result = generate_certificate_impl(
            "Ana", "Python Foundations", "Python", "beginner", comps
        )
        assert result["competencies"] == comps

    def test_empty_competencies_allowed(self):
        result = generate_certificate_impl(
            "Ana", "Python Foundations", "Python", "beginner", []
        )
        assert result["competencies"] == []

    def test_participant_preserved_stripped(self):
        result = generate_certificate_impl(
            "  Ana  ", "Python Foundations", "Python", "beginner", []
        )
        assert result["participant"] == "Ana"

    def test_unique_id_per_call(self):
        r1 = generate_certificate_impl(
            "Ana", "Python Foundations", "Python", "beginner", []
        )
        r2 = generate_certificate_impl(
            "Ana", "Python Foundations", "Python", "beginner", []
        )
        assert r1["id"] != r2["id"]

    def test_empty_participant_returns_error(self):
        result = generate_certificate_impl(
            "", "Python Foundations", "Python", "beginner", []
        )
        assert "error" in result

    def test_whitespace_participant_returns_error(self):
        result = generate_certificate_impl(
            "   ", "Python Foundations", "Python", "beginner", []
        )
        assert "error" in result

    def test_empty_activity_returns_error(self):
        result = generate_certificate_impl(
            "Ana", "", "Python", "beginner", []
        )
        assert "error" in result

    def test_invalid_level_returns_error(self):
        result = generate_certificate_impl(
            "Ana", "Python Foundations", "Python", "expert", []
        )
        assert "error" in result

    def test_intermediate_level_accepted(self):
        result = generate_certificate_impl(
            "Ana", "AI Path", "AI Agents", "intermediate", []
        )
        assert "error" not in result

    def test_advanced_level_accepted(self):
        result = generate_certificate_impl(
            "Ana", "Advanced Path", "Python", "advanced", []
        )
        assert "error" not in result

    def test_recognition_mentions_participant(self):
        result = generate_certificate_impl(
            "Carlos", "n8n Automation", "n8n", "beginner", []
        )
        assert "Carlos" in result["recognition"]


# ===========================================================================
# Group A — Unit tests: analyze_competencies_impl
# ===========================================================================


class TestAnalyzeCompetenciesTool:
    """analyze_competencies_impl: success, no match, invalid level."""

    def test_returns_dict_with_analyses_key(self):
        result = analyze_competencies_impl([], "beginner", "", ["Python"])
        assert "analyses" in result

    def test_returns_total_key(self):
        result = analyze_competencies_impl([], "beginner", "", ["Python"])
        assert "total" in result

    def test_total_matches_analyses_length(self):
        result = analyze_competencies_impl([], "beginner", "", ["Python"])
        assert result["total"] == len(result["analyses"])

    def test_single_path_for_python(self):
        result = analyze_competencies_impl([], "beginner", "", ["Python"])
        assert result["total"] == 1

    def test_all_paths_when_no_interests(self):
        result = analyze_competencies_impl([], "beginner", "", [])
        assert result["total"] > 1

    def test_analysis_has_required_keys(self):
        result = analyze_competencies_impl([], "beginner", "", ["Python"])
        analysis = result["analyses"][0]
        for key in ("path", "coverage_index", "matched_competencies",
                    "missing_competencies", "extra_competencies", "recommendations"):
            assert key in analysis, f"Missing key: {key}"

    def test_coverage_index_in_valid_range(self):
        result = analyze_competencies_impl([], "beginner", "", ["Python"])
        ci = result["analyses"][0]["coverage_index"]
        assert 0.0 <= ci <= 1.0

    def test_full_match_coverage_index_is_one(self):
        """Providing all Python path competencies should give coverage 1.0."""
        from core.data_loader import load_learning_paths
        from commands.trilha import find_learning_path
        paths = load_learning_paths()
        path = find_learning_path("Python", paths)
        all_comps = list(path.competencies)
        result = analyze_competencies_impl(all_comps, "beginner", "", ["Python"])
        assert result["analyses"][0]["coverage_index"] == 1.0

    def test_empty_comps_zero_coverage(self):
        result = analyze_competencies_impl([], "beginner", "", ["Python"])
        assert result["analyses"][0]["coverage_index"] == 0.0

    def test_matched_competencies_listed(self):
        result = analyze_competencies_impl(
            ["Python syntax and semantics", "control flow"],
            "beginner", "", ["Python"]
        )
        matched = result["analyses"][0]["matched_competencies"]
        assert "Python syntax and semantics" in matched
        assert "control flow" in matched

    def test_missing_competencies_listed(self):
        result = analyze_competencies_impl([], "beginner", "", ["Python"])
        assert len(result["analyses"][0]["missing_competencies"]) > 0

    def test_recommendations_present_when_missing(self):
        result = analyze_competencies_impl([], "beginner", "", ["Python"])
        recs = result["analyses"][0]["recommendations"]
        assert len(recs) > 0

    def test_recommendations_sorted_by_priority_desc(self):
        result = analyze_competencies_impl([], "beginner", "", ["Python"])
        priorities = [r["priority"] for r in result["analyses"][0]["recommendations"]]
        assert priorities == sorted(priorities, reverse=True)

    def test_recommendations_have_required_keys(self):
        result = analyze_competencies_impl([], "beginner", "", ["Python"])
        for rec in result["analyses"][0]["recommendations"]:
            for key in ("id", "priority", "recommendation_type", "target_id", "rationale"):
                assert key in rec, f"Missing key: {key}"

    def test_unknown_technology_interest_returns_empty(self):
        result = analyze_competencies_impl([], "beginner", "", ["Rust"])
        assert result["analyses"] == []
        assert result["total"] == 0
        assert "message" in result

    def test_invalid_level_returns_error(self):
        result = analyze_competencies_impl([], "expert", "", [])
        assert "error" in result

    def test_invalid_level_mentions_valid_values(self):
        result = analyze_competencies_impl([], "guru", "", [])
        assert "beginner" in result["error"]

    def test_intermediate_level_accepted(self):
        result = analyze_competencies_impl([], "intermediate", "", ["Python"])
        assert "error" not in result

    def test_goal_stored_but_does_not_break(self):
        result = analyze_competencies_impl(
            [], "beginner", "Become a backend developer", ["Python"]
        )
        assert "error" not in result

    def test_multiple_interests(self):
        result = analyze_competencies_impl([], "beginner", "", ["Python", "n8n"])
        assert result["total"] == 2


# ===========================================================================
# Group B — Integration tests via MCP protocol (Client in-process)
# ===========================================================================


class TestMCPProtocolIntegration:
    """
    Full MCP protocol round-trips using ``Client(create_server())`` in-process.
    No stdio transport is opened — the SDK's direct-dispatch path is used.
    Async tests run via ``@pytest.mark.anyio`` (anyio pytest plugin).
    """

    @pytest.mark.anyio
    async def test_four_tools_are_registered(self):
        """tools/list returns exactly the four expected tool names."""
        from mcp import Client
        async with Client(create_server()) as client:
            result = await client.list_tools()
            names = {t.name for t in result.tools}
        assert names == {
            "get_learning_path",
            "get_challenge",
            "generate_certificate",
            "analyze_competencies",
        }

    @pytest.mark.anyio
    async def test_tool_list_has_descriptions(self):
        """Each registered tool exposes a non-empty description in the manifest."""
        from mcp import Client
        async with Client(create_server()) as client:
            result = await client.list_tools()
        for tool in result.tools:
            assert tool.description, f"Tool '{tool.name}' has no description"

    @pytest.mark.anyio
    async def test_get_learning_path_via_protocol(self):
        """get_learning_path returns valid JSON with 'title' via the MCP protocol."""
        from mcp import Client
        async with Client(create_server()) as client:
            result = await client.call_tool(
                "get_learning_path", {"technology": "Python"}
            )
        data = json.loads(result.content[0].text)
        assert "title" in data
        assert data["title"] == "Python Foundations"

    @pytest.mark.anyio
    async def test_get_challenge_via_protocol(self):
        """get_challenge returns a challenge dict with required keys."""
        from mcp import Client
        async with Client(create_server()) as client:
            result = await client.call_tool(
                "get_challenge", {"technology": "Python", "level": "beginner"}
            )
        data = json.loads(result.content[0].text)
        assert "error" not in data
        assert "title" in data
        assert "evaluation_criteria" in data

    @pytest.mark.anyio
    async def test_generate_certificate_via_protocol(self):
        """generate_certificate returns a cert dict with disclaimer via MCP."""
        from mcp import Client
        async with Client(create_server()) as client:
            result = await client.call_tool(
                "generate_certificate",
                {
                    "participant": "Test User",
                    "activity": "Python Foundations",
                    "technology": "Python",
                    "level": "beginner",
                    "competencies": ["control flow"],
                },
            )
        data = json.loads(result.content[0].text)
        assert "error" not in data
        assert "disclaimer" in data
        assert "FICTÍCIO" in data["disclaimer"]

    @pytest.mark.anyio
    async def test_analyze_competencies_via_protocol(self):
        """analyze_competencies returns analyses list with coverage_index."""
        from mcp import Client
        async with Client(create_server()) as client:
            result = await client.call_tool(
                "analyze_competencies",
                {
                    "competencies": ["Python syntax and semantics"],
                    "level": "beginner",
                    "goal": "Become a developer",
                    "technologies_of_interest": ["Python"],
                },
            )
        data = json.loads(result.content[0].text)
        assert "analyses" in data
        assert data["total"] == 1
        assert 0.0 <= data["analyses"][0]["coverage_index"] <= 1.0

    @pytest.mark.anyio
    async def test_error_response_via_protocol_not_found(self):
        """Unknown technology returns an error dict, not an exception."""
        from mcp import Client
        async with Client(create_server()) as client:
            result = await client.call_tool(
                "get_learning_path", {"technology": "Rust"}
            )
        data = json.loads(result.content[0].text)
        assert "error" in data

    @pytest.mark.anyio
    async def test_error_response_invalid_level_via_protocol(self):
        """Invalid level string returns an error dict, not an exception."""
        from mcp import Client
        async with Client(create_server()) as client:
            result = await client.call_tool(
                "get_challenge", {"technology": "Python", "level": "expert"}
            )
        data = json.loads(result.content[0].text)
        assert "error" in data

    @pytest.mark.anyio
    async def test_create_server_is_idempotent(self):
        """Two independent create_server() calls produce independent instances."""
        from mcp import Client
        server_a = create_server()
        server_b = create_server()
        async with Client(server_a) as ca, Client(server_b) as cb:
            r_a = await ca.list_tools()
            r_b = await cb.list_tools()
        assert {t.name for t in r_a.tools} == {t.name for t in r_b.tools}
