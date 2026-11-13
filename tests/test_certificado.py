"""
tests/test_certificado.py
-------------------------
Automated tests for commands/certificado.py — Etapa 8 of Geo-Explorer.

Coverage
~~~~~~~~
- Correct certificate generation (all required fields present).
- Unique identifier per certificate.
- Issue date: today (default) and a custom date.
- Competencies are preserved exactly.
- Mandatory field validation (empty participant / empty activity).
- Fictional-certificate disclaimer is always present.
- Display formatting: all sections visible in printed output.
- Independence between separately generated certificates.

Run with:
    python -m unittest discover -s tests -v
"""

import unittest
from datetime import date
from io import StringIO
from unittest.mock import patch

from commands.certificado import (
    DISCLAIMER,
    build_certificate,
    display_certificate,
    generate_certificate,
)


# ---------------------------------------------------------------------------
# Shared helpers / fixtures
# ---------------------------------------------------------------------------

_PARTICIPANT = "Ana Paula Souza"
_ACTIVITY = "Python Foundations"
_TECHNOLOGY = "Python"
_LEVEL = "beginner"
_COMPETENCIES = [
    "Python syntax and semantics",
    "control flow",
    "file I/O",
    "exception handling",
    "classes and objects",
]
_FIXED_DATE = date(2024, 6, 15)


def _make_cert(**kwargs) -> dict:
    """Return a certificate built with sensible defaults, overridable via kwargs."""
    defaults = dict(
        participant=_PARTICIPANT,
        activity=_ACTIVITY,
        technology=_TECHNOLOGY,
        level=_LEVEL,
        competencies=list(_COMPETENCIES),
        issued_on=_FIXED_DATE,
    )
    defaults.update(kwargs)
    return build_certificate(**defaults)


def _capture_display(cert: dict) -> str:
    """Call display_certificate and return everything printed to stdout."""
    buf = StringIO()
    with patch("sys.stdout", buf):
        display_certificate(cert)
    return buf.getvalue()


def _capture_generate(**kwargs) -> str:
    """Call generate_certificate and return everything printed to stdout."""
    defaults = dict(
        participant=_PARTICIPANT,
        activity=_ACTIVITY,
        technology=_TECHNOLOGY,
        level=_LEVEL,
        competencies=list(_COMPETENCIES),
        issued_on=_FIXED_DATE,
    )
    defaults.update(kwargs)
    buf = StringIO()
    with patch("sys.stdout", buf):
        generate_certificate(**defaults)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Group 1 — build_certificate: correct generation
# ---------------------------------------------------------------------------


class TestBuildCertificateCorrectGeneration(unittest.TestCase):
    """Verifies that every mandatory field is present and correctly populated."""

    @classmethod
    def setUpClass(cls):
        cls.cert = _make_cert()

    def test_returns_a_dict(self):
        self.assertIsInstance(self.cert, dict)

    def test_has_id_key(self):
        self.assertIn("id", self.cert)

    def test_has_participant_key(self):
        self.assertIn("participant", self.cert)

    def test_has_activity_key(self):
        self.assertIn("activity", self.cert)

    def test_has_technology_key(self):
        self.assertIn("technology", self.cert)

    def test_has_level_key(self):
        self.assertIn("level", self.cert)

    def test_has_issued_on_key(self):
        self.assertIn("issued_on", self.cert)

    def test_has_competencies_key(self):
        self.assertIn("competencies", self.cert)

    def test_has_disclaimer_key(self):
        self.assertIn("disclaimer", self.cert)

    def test_has_recognition_key(self):
        self.assertIn("recognition", self.cert)

    def test_participant_value(self):
        self.assertEqual(self.cert["participant"], _PARTICIPANT)

    def test_activity_value(self):
        self.assertEqual(self.cert["activity"], _ACTIVITY)

    def test_technology_value(self):
        self.assertEqual(self.cert["technology"], _TECHNOLOGY)

    def test_level_value(self):
        self.assertEqual(self.cert["level"], _LEVEL)

    def test_issued_on_is_date(self):
        self.assertIsInstance(self.cert["issued_on"], date)

    def test_issued_on_value(self):
        self.assertEqual(self.cert["issued_on"], _FIXED_DATE)

    def test_competencies_is_list(self):
        self.assertIsInstance(self.cert["competencies"], list)

    def test_disclaimer_value(self):
        self.assertEqual(self.cert["disclaimer"], DISCLAIMER)

    def test_recognition_is_non_empty_string(self):
        self.assertIsInstance(self.cert["recognition"], str)
        self.assertTrue(self.cert["recognition"].strip())

    def test_recognition_contains_participant_name(self):
        self.assertIn(_PARTICIPANT, self.cert["recognition"])

    def test_recognition_contains_activity_name(self):
        self.assertIn(_ACTIVITY, self.cert["recognition"])


# ---------------------------------------------------------------------------
# Group 2 — build_certificate: unique identifier
# ---------------------------------------------------------------------------


class TestBuildCertificateUniqueId(unittest.TestCase):
    """Verifies that every generated certificate receives a unique ID."""

    def test_id_is_a_non_empty_string(self):
        cert = _make_cert()
        self.assertIsInstance(cert["id"], str)
        self.assertTrue(cert["id"].strip())

    def test_two_certificates_have_different_ids(self):
        cert_a = _make_cert()
        cert_b = _make_cert()
        self.assertNotEqual(cert_a["id"], cert_b["id"])

    def test_ten_certificates_all_unique(self):
        ids = {_make_cert()["id"] for _ in range(10)}
        self.assertEqual(len(ids), 10)

    def test_id_is_uuid_format(self):
        import uuid
        cert = _make_cert()
        # Should not raise
        parsed = uuid.UUID(cert["id"])
        self.assertEqual(str(parsed), cert["id"])


# ---------------------------------------------------------------------------
# Group 3 — build_certificate: issue date
# ---------------------------------------------------------------------------


class TestBuildCertificateDate(unittest.TestCase):
    """Verifies correct handling of issue dates."""

    def test_custom_date_is_preserved(self):
        custom = date(2023, 1, 20)
        cert = _make_cert(issued_on=custom)
        self.assertEqual(cert["issued_on"], custom)

    def test_none_defaults_to_today(self):
        today = date.today()
        cert = _make_cert(issued_on=None)
        self.assertEqual(cert["issued_on"], today)

    def test_different_custom_dates_are_independent(self):
        d1 = date(2023, 3, 10)
        d2 = date(2024, 9, 25)
        cert1 = _make_cert(issued_on=d1)
        cert2 = _make_cert(issued_on=d2)
        self.assertEqual(cert1["issued_on"], d1)
        self.assertEqual(cert2["issued_on"], d2)
        self.assertNotEqual(cert1["issued_on"], cert2["issued_on"])

    def test_issued_on_type_is_date(self):
        cert = _make_cert(issued_on=_FIXED_DATE)
        self.assertIsInstance(cert["issued_on"], date)


# ---------------------------------------------------------------------------
# Group 4 — build_certificate: competencies preservation
# ---------------------------------------------------------------------------


class TestBuildCertificateCompetencies(unittest.TestCase):
    """Verifies that competencies are stored correctly and independently."""

    def test_competencies_match_input(self):
        cert = _make_cert()
        self.assertEqual(cert["competencies"], _COMPETENCIES)

    def test_competencies_count_matches(self):
        cert = _make_cert()
        self.assertEqual(len(cert["competencies"]), len(_COMPETENCIES))

    def test_each_competency_present(self):
        cert = _make_cert()
        for c in _COMPETENCIES:
            self.assertIn(c, cert["competencies"],
                          msg=f"Missing competency: {c!r}")

    def test_single_competency(self):
        cert = _make_cert(competencies=["machine learning"])
        self.assertEqual(cert["competencies"], ["machine learning"])

    def test_empty_competencies_list_allowed(self):
        cert = _make_cert(competencies=[])
        self.assertEqual(cert["competencies"], [])

    def test_competencies_is_a_copy(self):
        """Mutating the original list must not affect the stored certificate."""
        original = ["competency A", "competency B"]
        cert = _make_cert(competencies=original)
        original.append("competency C")
        self.assertNotIn("competency C", cert["competencies"])

    def test_mutating_cert_competencies_does_not_affect_original(self):
        """Mutating the certificate's list must not affect the source."""
        original = ["competency X"]
        cert = _make_cert(competencies=original)
        cert["competencies"].append("competency Y")
        self.assertNotIn("competency Y", original)


# ---------------------------------------------------------------------------
# Group 5 — build_certificate: mandatory field validation
# ---------------------------------------------------------------------------


class TestBuildCertificateValidation(unittest.TestCase):
    """Verifies that invalid inputs are rejected with ValueError."""

    def test_empty_participant_raises(self):
        with self.assertRaises(ValueError):
            _make_cert(participant="")

    def test_whitespace_participant_raises(self):
        with self.assertRaises(ValueError):
            _make_cert(participant="   ")

    def test_newline_participant_raises(self):
        with self.assertRaises(ValueError):
            _make_cert(participant="\n")

    def test_empty_activity_raises(self):
        with self.assertRaises(ValueError):
            _make_cert(activity="")

    def test_whitespace_activity_raises(self):
        with self.assertRaises(ValueError):
            _make_cert(activity="   ")

    def test_newline_activity_raises(self):
        with self.assertRaises(ValueError):
            _make_cert(activity="\n")

    def test_valid_inputs_do_not_raise(self):
        # Should complete without exception
        cert = _make_cert()
        self.assertIsNotNone(cert)

    def test_participant_is_stripped_in_output(self):
        cert = _make_cert(participant="  Bob  ")
        self.assertEqual(cert["participant"], "Bob")

    def test_activity_is_stripped_in_output(self):
        cert = _make_cert(activity="  Python Foundations  ")
        self.assertEqual(cert["activity"], "Python Foundations")


# ---------------------------------------------------------------------------
# Group 6 — disclaimer: always present and correct
# ---------------------------------------------------------------------------


class TestCertificateDisclaimer(unittest.TestCase):
    """Verifies that the fictitious-certificate disclaimer is always present."""

    def test_disclaimer_constant_contains_ficticio(self):
        self.assertIn("FICTÍCIO", DISCLAIMER)

    def test_disclaimer_constant_contains_sem_validade(self):
        self.assertIn("SEM VALIDADE", DISCLAIMER)

    def test_cert_disclaimer_equals_constant(self):
        cert = _make_cert()
        self.assertEqual(cert["disclaimer"], DISCLAIMER)

    def test_disclaimer_not_empty(self):
        self.assertTrue(DISCLAIMER.strip())

    def test_all_certs_have_same_disclaimer(self):
        certs = [_make_cert() for _ in range(5)]
        for cert in certs:
            self.assertEqual(cert["disclaimer"], DISCLAIMER)

    def test_no_professional_credential_claim(self):
        cert = _make_cert()
        # The recognition text must not assert a professional certification
        recognition = cert["recognition"].lower()
        for forbidden in ("certificação profissional", "credencial reconhecida",
                          "reconhecido oficialmente"):
            self.assertNotIn(forbidden, recognition,
                             msg=f"Forbidden phrase found: {forbidden!r}")


# ---------------------------------------------------------------------------
# Group 7 — display_certificate: formatting
# ---------------------------------------------------------------------------


class TestDisplayCertificateFormatting(unittest.TestCase):
    """Verifies that display_certificate prints all expected sections."""

    @classmethod
    def setUpClass(cls):
        cls.cert = _make_cert()
        cls.output = _capture_display(cls.cert)

    def test_output_is_non_empty(self):
        self.assertTrue(self.output.strip())

    def test_disclaimer_in_output(self):
        self.assertIn(DISCLAIMER, self.output)

    def test_participant_in_output(self):
        self.assertIn(_PARTICIPANT, self.output)

    def test_activity_in_output(self):
        self.assertIn(_ACTIVITY, self.output)

    def test_technology_in_output(self):
        self.assertIn(_TECHNOLOGY, self.output)

    def test_level_in_output(self):
        self.assertIn(_LEVEL, self.output)

    def test_formatted_date_in_output(self):
        # Fixed date 2024-06-15 should appear as 15/06/2024
        self.assertIn("15/06/2024", self.output)

    def test_id_in_output(self):
        self.assertIn(self.cert["id"], self.output)

    def test_all_competencies_in_output(self):
        for competency in _COMPETENCIES:
            self.assertIn(competency, self.output,
                          msg=f"Competency missing from output: {competency!r}")

    def test_competencies_section_label_in_output(self):
        self.assertIn("Competências", self.output)

    def test_recognition_text_in_output(self):
        self.assertIn(self.cert["recognition"], self.output)

    def test_border_present(self):
        # Display must include a visual separator
        self.assertIn("=", self.output)

    def test_certificate_label_present(self):
        self.assertIn("Certificado", self.output)


# ---------------------------------------------------------------------------
# Group 8 — generate_certificate: end-to-end + independence
# ---------------------------------------------------------------------------


class TestGenerateCertificateEndToEnd(unittest.TestCase):
    """Verifies the high-level generate_certificate function."""

    def test_output_contains_disclaimer(self):
        output = _capture_generate()
        self.assertIn(DISCLAIMER, output)

    def test_output_contains_participant(self):
        output = _capture_generate()
        self.assertIn(_PARTICIPANT, output)

    def test_output_contains_activity(self):
        output = _capture_generate()
        self.assertIn(_ACTIVITY, output)

    def test_output_contains_technology(self):
        output = _capture_generate()
        self.assertIn(_TECHNOLOGY, output)

    def test_output_contains_level(self):
        output = _capture_generate()
        self.assertIn(_LEVEL, output)

    def test_output_contains_date(self):
        output = _capture_generate()
        self.assertIn("15/06/2024", output)

    def test_empty_participant_raises(self):
        with self.assertRaises(ValueError):
            _capture_generate(participant="")

    def test_empty_activity_raises(self):
        with self.assertRaises(ValueError):
            _capture_generate(activity="")

    def test_today_date_used_when_not_provided(self):
        today_str = date.today().strftime("%d/%m/%Y")
        buf = StringIO()
        with patch("sys.stdout", buf):
            generate_certificate(
                participant=_PARTICIPANT,
                activity=_ACTIVITY,
                technology=_TECHNOLOGY,
                level=_LEVEL,
                competencies=_COMPETENCIES,
            )
        self.assertIn(today_str, buf.getvalue())


class TestCertificateIndependence(unittest.TestCase):
    """Verifies that separately generated certificates are independent."""

    def test_two_certs_have_different_ids(self):
        cert_a = _make_cert()
        cert_b = _make_cert()
        self.assertNotEqual(cert_a["id"], cert_b["id"])

    def test_different_participants_stay_separate(self):
        cert_a = _make_cert(participant="Alice")
        cert_b = _make_cert(participant="Bob")
        self.assertEqual(cert_a["participant"], "Alice")
        self.assertEqual(cert_b["participant"], "Bob")

    def test_different_activities_stay_separate(self):
        cert_a = _make_cert(activity="Python Foundations")
        cert_b = _make_cert(activity="AI Agents Challenge")
        self.assertEqual(cert_a["activity"], "Python Foundations")
        self.assertEqual(cert_b["activity"], "AI Agents Challenge")

    def test_different_dates_stay_separate(self):
        d1 = date(2023, 1, 1)
        d2 = date(2025, 12, 31)
        cert_a = _make_cert(issued_on=d1)
        cert_b = _make_cert(issued_on=d2)
        self.assertEqual(cert_a["issued_on"], d1)
        self.assertEqual(cert_b["issued_on"], d2)

    def test_mutating_one_cert_does_not_affect_another(self):
        cert_a = _make_cert(competencies=["skill A"])
        cert_b = _make_cert(competencies=["skill B"])
        cert_a["competencies"].append("extra")
        self.assertNotIn("extra", cert_b["competencies"])

    def test_five_independent_certs_all_unique_ids(self):
        certs = [_make_cert() for _ in range(5)]
        ids = [c["id"] for c in certs]
        self.assertEqual(len(ids), len(set(ids)))


if __name__ == "__main__":
    unittest.main()
