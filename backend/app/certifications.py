"""Per-Certification config registry: models + file-based loader (Story 9.1).

Each certification's blueprint — Provider, canonical domain list + weights, and
exam parameters (``total_questions`` / ``duration_minutes`` / ``pass_bar``) — is
declared in ``config/certifications.yaml`` and loaded + validated at startup.
This is the **unblocker for Epic 9** (Multi-Provider / Multi-Certification,
PRD §4.7 / FR-29; architecture rev 6 / AR-19): it makes "add a certification"
a content + config change rather than a code change.

This module is **additive only**. It does NOT touch ``models.py``'s
``ExamType`` / ``Domain`` enums, ``session.py``'s ``MOCK_EXAM_CONFIGS``, or any
runtime behavior — Story 9.2 does the rewiring. A parity test asserts this
seed's certifications/domains/weights/params match the current hardcoded values
exactly, so 9.2 can switch over provably without a Databricks DE regression.

A certification's ``id`` IS the existing ``exam`` value (decision-log #36):
``associate`` / ``professional``. Validation is **fail-loud** (matching the
content-loader stance): a malformed/invalid config raises a clear error naming
the file rather than starting with silently-wrong blueprints.
"""

import logging
from pathlib import Path
from typing import TYPE_CHECKING

import yaml
from pydantic import BaseModel, Field, conint, root_validator, validator

# Strict int aliases: Pydantic v1's lax int coercion would otherwise truncate a float
# (e.g. weight 100.9 -> 100) or accept a bool / YAML-yes (weight: true -> 1) BEFORE the
# ge/gt + sum-to-100 checks run, silently defeating this module's fail-loud contract.
# conint(strict=True, ...) rejects non-int input AND enforces the bound (a bare StrictInt
# does not enforce Field(ge=) under v1).
# conint() returns a value, not a type, so static checkers reject it in an annotation;
# expose it as ``int`` to the type checker while keeping the constrained type at runtime.
if TYPE_CHECKING:
    _StrictNonNegInt = int
    _StrictPosInt = int
else:
    _StrictNonNegInt = conint(strict=True, ge=0)
    _StrictPosInt = conint(strict=True, gt=0)

logger = logging.getLogger(__name__)

# Default config file name, resolved via a project-root walk (see
# ``load_certifications``) mirroring how ``content.py`` finds ``exercises/``.
CONFIG_DIRNAME = "config"
CONFIG_FILENAME = "certifications.yaml"


class CertificationConfigError(Exception):
    """Raised when the certification config is missing, malformed, or invalid.

    Carries a message naming the offending file so a bad config fails loudly at
    startup instead of being silently swallowed (FR-3 spirit / content-loader
    fail-loud stance).
    """


class CertificationDomain(BaseModel):
    """A single weighted domain within a certification's blueprint."""

    name: str = Field(..., min_length=1, description="Domain name (matches the Domain enum value)")
    weight: _StrictNonNegInt = Field(..., description="Domain weight in percent (set sums to 100)")


class Certification(BaseModel):
    """One certification blueprint — ``id`` is the existing ``exam`` value."""

    id: str = Field(..., description="Certification id == the existing `exam` value")
    name: str = Field(..., min_length=1, description="Human-readable certification name")
    total_questions: _StrictPosInt = Field(..., description="Full-length exam question count")
    duration_minutes: _StrictPosInt = Field(..., description="Exam clock in minutes")
    pass_bar: float = Field(..., gt=0, le=1, description="Pass threshold as a fraction (0,1]")
    domains: list[CertificationDomain] = Field(..., description="Weighted domain list")

    @validator("pass_bar", pre=True)
    def pass_bar_not_bool(cls, v):
        """Reject a bool for pass_bar (bool is an int subclass; True would -> 1.0)."""
        if isinstance(v, bool):
            raise ValueError("pass_bar must be a number in (0, 1], not a bool")
        return v

    @validator("id")
    def id_not_empty(cls, v):
        """A certification id (== the `exam` value) must be non-empty; stored stripped.

        Returning the stripped value canonicalizes the stored id so it matches the
        normalized key used by ``get_certification`` and the duplicate-id check
        (otherwise ``id: " associate "`` would store with whitespace yet look up fine,
        an inconsistency between storage and dedup/lookup).
        """
        if not v or not v.strip():
            raise ValueError("certification 'id' must be non-empty")
        return v.strip()

    @validator("domains")
    def domains_non_empty_and_weights_sum_to_100(cls, v):
        """Require at least one domain, unique names, and weights summing to 100."""
        if not v:
            raise ValueError("certification must declare at least one domain")
        # Reject duplicate domain names: domain_weights builds {name: weight}, so a
        # duplicate would silently collapse — dropping a weight and breaking the
        # sum-to-100 invariant on the helper's actual output.
        names = [d.name for d in v]
        dupe_names = sorted({n for n in names if names.count(n) > 1})
        if dupe_names:
            raise ValueError(f"duplicate domain name(s): {', '.join(dupe_names)}")
        total = sum(d.weight for d in v)
        if total != 100:
            raise ValueError(f"domain weights must sum to 100, got {total}")
        return v


class Provider(BaseModel):
    """A certification provider (e.g. Databricks) with >=1 certification."""

    id: str = Field(..., description="Provider id (e.g. 'databricks')")
    name: str = Field(..., min_length=1, description="Human-readable provider name")
    certifications: list[Certification] = Field(..., description="This provider's certifications")

    @validator("certifications")
    def certifications_non_empty(cls, v):
        """A provider must declare at least one certification."""
        if not v:
            raise ValueError("provider must declare at least one certification")
        return v


class CertificationRegistry(BaseModel):
    """The full registry: all providers and their certifications."""

    providers: list[Provider] = Field(..., description="All configured providers")

    @validator("providers")
    def providers_non_empty(cls, v):
        """The registry must declare at least one provider."""
        if not v:
            raise ValueError("registry must declare at least one provider")
        return v

    @root_validator(skip_on_failure=True)
    def certification_ids_globally_unique(cls, values):
        """Certification ids must be unique across ALL providers.

        The id is the ``exam`` value used everywhere downstream; a duplicate
        would make ``get_certification`` ambiguous.
        """
        providers = values.get("providers") or []
        first_by_key: dict[str, str] = {}
        dupes: set[str] = set()
        for provider in providers:
            for cert in provider.certifications:
                key = cert.id.strip().lower()
                if key in first_by_key:
                    # Surface BOTH the first and the colliding id, not just the latter.
                    dupes.add(first_by_key[key])
                    dupes.add(cert.id)
                else:
                    first_by_key[key] = cert.id
        if dupes:
            raise ValueError(
                f"duplicate certification id(s) across providers: {', '.join(sorted(dupes))}"
            )
        return values


def _resolve_config_path() -> Path:
    """Resolve ``config/certifications.yaml`` via a project-root walk.

    Mirrors ``content.load_exercises_from_directory``: walk up from this file
    looking for ``config/certifications.yaml`` and return it when found. Matching on
    the file itself (not merely a directory named ``config``) means an unrelated
    ``config/`` dir up-tree — or a non-directory named ``config`` — never shadows the
    real config and produces a misleading "not found" pointing at the wrong path.
    Falls back to the relative ``config/...`` path if nothing is found on the way up.
    """
    current_dir = Path(__file__).parent
    while current_dir != current_dir.parent:
        candidate = current_dir.parent / CONFIG_DIRNAME / CONFIG_FILENAME
        if candidate.is_file():
            return candidate
        current_dir = current_dir.parent
    return Path(CONFIG_DIRNAME) / CONFIG_FILENAME


def load_certifications(path: Path | None = None) -> CertificationRegistry:
    """Load + validate the certification registry from a YAML file.

    Args:
        path: Explicit path to the config YAML. If ``None``, resolves
            ``config/certifications.yaml`` via the project-root walk.

    Returns:
        A validated :class:`CertificationRegistry`.

    Raises:
        CertificationConfigError: if the file is missing, is not valid YAML, is
            not a mapping, or fails model validation. The message names the file
            and the problem so the failure is loud and diagnosable.
    """
    config_path = Path(path) if path is not None else _resolve_config_path()

    if not config_path.exists():
        raise CertificationConfigError(f"Certification config file not found: {config_path}")

    try:
        with open(config_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise CertificationConfigError(
            f"Failed to parse certification config {config_path}: {e}"
        ) from e

    if not isinstance(data, dict):
        raise CertificationConfigError(
            f"Certification config {config_path} must be a YAML mapping with a "
            f"'providers' key, got {type(data).__name__}"
        )

    try:
        registry = CertificationRegistry(**data)
    except Exception as e:  # pydantic ValidationError (+ defensive catch-all)
        raise CertificationConfigError(f"Invalid certification config {config_path}: {e}") from e

    return registry


def get_certification(registry: CertificationRegistry, exam_id: str) -> Certification:
    """Look up a certification by its ``exam`` id (case-insensitive).

    Raises:
        CertificationConfigError: if ``exam_id`` is empty/None, or no certification
            matches it.
    """
    # Guard empty/None up front so the documented CertificationConfigError contract
    # holds (otherwise ``None.strip()`` would raise a raw AttributeError that
    # downstream callers catching CertificationConfigError would miss).
    if not exam_id or not exam_id.strip():
        raise CertificationConfigError("exam id must be a non-empty string")
    exam_norm = exam_id.strip().lower()
    for provider in registry.providers:
        for cert in provider.certifications:
            if cert.id.strip().lower() == exam_norm:
                return cert
    raise CertificationConfigError(f"No certification configured for exam id '{exam_id}'")


def domain_weights(registry: CertificationRegistry, exam_id: str) -> dict[str, int]:
    """Return ``{domain_name: weight}`` for the given exam id (case-insensitive)."""
    cert = get_certification(registry, exam_id)
    return {d.name: d.weight for d in cert.domains}


def exam_params(registry: CertificationRegistry, exam_id: str) -> dict[str, object]:
    """Return ``{total_questions, duration_minutes, pass_bar}`` for the exam id."""
    cert = get_certification(registry, exam_id)
    return {
        "total_questions": cert.total_questions,
        "duration_minutes": cert.duration_minutes,
        "pass_bar": cert.pass_bar,
    }
