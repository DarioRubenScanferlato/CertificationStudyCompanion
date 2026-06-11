"""Tests for the per-Certification config registry (Story 9.1).

Covers: the seed config loads + validates; lookup helpers; malformed configs
fail loudly; and the **parity test** — the anchor asserting the seed matches the
current hardcoded ``MOCK_EXAM_CONFIGS`` + ``Domain`` enum + ``READINESS_THRESHOLD``
exactly, so Story 9.2 can switch the runtime over without behavior change.
"""

import textwrap
from pathlib import Path

import pytest

from app.certifications import (
    CertificationConfigError,
    domain_weights,
    exam_params,
    get_certification,
    load_certifications,
)
from app.models import Domain, ExamType
from app.session import MOCK_EXAM_CONFIGS
from app.store import READINESS_THRESHOLD


def _write(tmp_path: Path, body: str) -> Path:
    """Write a config YAML (dedented) to a temp file and return its path."""
    path = tmp_path / "certifications.yaml"
    path.write_text(textwrap.dedent(body))
    return path


# A minimal valid single-certification config used as a base for malformed cases.
_VALID_BODY = """\
    providers:
      - id: acme
        name: "Acme"
        certifications:
          - id: foundations
            name: "Acme Foundations"
            total_questions: 10
            duration_minutes: 20
            pass_bar: 0.70
            domains:
              - { name: "Alpha", weight: 60 }
              - { name: "Beta", weight: 40 }
"""


class TestSeedLoads:
    """The real seed config (config/certifications.yaml) loads + validates."""

    def test_seed_loads_and_validates(self):
        registry = load_certifications()
        assert len(registry.providers) == 1
        provider = registry.providers[0]
        assert provider.id == "databricks"
        assert len(provider.certifications) == 2
        ids = {c.id for c in provider.certifications}
        assert ids == {"associate", "professional"}


class TestHelpers:
    """Lookup helpers, keyed by exam id (case-insensitive)."""

    def test_exam_params_associate(self):
        registry = load_certifications()
        params = exam_params(registry, "associate")
        assert params == {"total_questions": 45, "duration_minutes": 90, "pass_bar": 0.70}

    def test_domain_weights_professional_sums_to_100(self):
        registry = load_certifications()
        weights = domain_weights(registry, "professional")
        assert sum(weights.values()) == 100

    def test_lookup_is_case_insensitive(self):
        registry = load_certifications()
        cert = get_certification(registry, "ASSOCIATE")
        assert cert.id == "associate"

    def test_unknown_exam_id_fails_loudly(self):
        registry = load_certifications()
        with pytest.raises(CertificationConfigError, match="No certification configured"):
            get_certification(registry, "nonexistent")


class TestMalformedConfigsFailLoudly:
    """Every malformed/invalid config raises CertificationConfigError."""

    def test_weights_not_summing_to_100(self, tmp_path):
        path = _write(
            tmp_path,
            _VALID_BODY.replace("weight: 40 }", "weight: 50 }"),
        )
        with pytest.raises(CertificationConfigError, match="sum to 100"):
            load_certifications(path=path)

    def test_missing_required_field(self, tmp_path):
        # Drop total_questions from the certification.
        path = _write(
            tmp_path,
            _VALID_BODY.replace("            total_questions: 10\n", ""),
        )
        with pytest.raises(CertificationConfigError):
            load_certifications(path=path)

    def test_duplicate_certification_id(self, tmp_path):
        path = _write(
            tmp_path,
            """\
            providers:
              - id: acme
                name: "Acme"
                certifications:
                  - id: dup
                    name: "First"
                    total_questions: 10
                    duration_minutes: 20
                    pass_bar: 0.70
                    domains:
                      - { name: "Alpha", weight: 100 }
              - id: other
                name: "Other"
                certifications:
                  - id: DUP
                    name: "Second (case-variant dup)"
                    total_questions: 10
                    duration_minutes: 20
                    pass_bar: 0.70
                    domains:
                      - { name: "Beta", weight: 100 }
            """,
        )
        with pytest.raises(CertificationConfigError, match="duplicate certification id"):
            load_certifications(path=path)

    def test_empty_domains(self, tmp_path):
        path = _write(
            tmp_path,
            """\
            providers:
              - id: acme
                name: "Acme"
                certifications:
                  - id: foundations
                    name: "Acme Foundations"
                    total_questions: 10
                    duration_minutes: 20
                    pass_bar: 0.70
                    domains: []
            """,
        )
        with pytest.raises(CertificationConfigError):
            load_certifications(path=path)

    def test_nonexistent_file(self, tmp_path):
        path = tmp_path / "does-not-exist.yaml"
        with pytest.raises(CertificationConfigError, match="not found"):
            load_certifications(path=path)

    def test_bad_yaml(self, tmp_path):
        path = tmp_path / "certifications.yaml"
        # Unbalanced brackets / bad indentation -> YAMLError.
        path.write_text("providers: [ - id: acme\n  name: oops\n")
        with pytest.raises(CertificationConfigError):
            load_certifications(path=path)

    def test_not_a_mapping(self, tmp_path):
        path = tmp_path / "certifications.yaml"
        path.write_text("- just\n- a\n- list\n")
        with pytest.raises(CertificationConfigError, match="must be a YAML mapping"):
            load_certifications(path=path)


class TestParityWithHardcodedValues:
    """The anchor: the seed must match today's hardcoded blueprints EXACTLY."""

    def test_seed_matches_mock_exam_configs_and_domain_enum(self):
        registry = load_certifications()

        for exam in ExamType:
            config = MOCK_EXAM_CONFIGS[exam]
            cert = get_certification(registry, exam.value)

            # Exam parameters.
            assert cert.total_questions == config.total_questions
            assert cert.duration_minutes == config.duration_minutes

            # pass_bar == the readiness planning heuristic threshold.
            assert cert.pass_bar == READINESS_THRESHOLD

            # Domain name->weight map matches the hardcoded config exactly.
            seed_map = domain_weights(registry, exam.value)
            expected_map = {d.value: w for d, w in config.domain_weights.items()}
            assert seed_map == expected_map

            # Every seed domain name is a valid Domain enum value.
            valid_domain_values = {d.value for d in Domain}
            for name in seed_map:
                assert name in valid_domain_values, f"'{name}' is not a Domain enum value"
