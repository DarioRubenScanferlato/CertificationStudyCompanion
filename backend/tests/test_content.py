"""Tests for content loading and filtering."""

import pytest

from app.content import filter_exercises, load_exercises_from_directory
from app.models import ExerciseType


class TestContentLoader:
    """Tests for content loader."""

    def test_load_exercises_from_associate_directory(self):
        """Test loading exercises from the associate directory."""
        exercises, error_count, error_log = load_exercises_from_directory()

        # Should load the 72 MCQs from mcq-associate-batch-01.yaml
        assert len(exercises) > 0, "Should load at least some exercises"
        assert error_count == 0, "Should have no errors loading valid YAML"

        # Verify we loaded MCQs
        assert any(e.type == ExerciseType.SINGLE_CHOICE for e in exercises)

    def test_nonexistent_directory_returns_empty(self):
        """Test that nonexistent directory returns empty list."""
        exercises, error_count, error_log = load_exercises_from_directory("nonexistent")
        assert exercises == []
        assert error_count == 0  # Not an error, just no files


class TestFiltering:
    """Tests for exercise filtering."""

    @pytest.fixture
    def sample_exercises(self):
        """Load sample exercises for testing."""
        exercises, _, _ = load_exercises_from_directory()
        return exercises

    def test_filter_by_domain(self, sample_exercises):
        """Test filtering by domain."""
        if not sample_exercises:
            pytest.skip("No exercises loaded")

        # Get first exercise's domain
        first_domain = sample_exercises[0].domain
        filtered = filter_exercises(sample_exercises, domain=first_domain)

        assert len(filtered) > 0
        assert all(e.domain == first_domain for e in filtered)

    def test_filter_by_domain_case_insensitive(self, sample_exercises):
        """Test case-insensitive domain filtering."""
        if not sample_exercises:
            pytest.skip("No exercises loaded")

        first_domain = sample_exercises[0].domain
        domain_lower = first_domain.value.lower()

        filtered = filter_exercises(sample_exercises, domain=domain_lower)
        assert len(filtered) > 0

    def test_filter_by_difficulty(self, sample_exercises):
        """Test filtering by difficulty."""
        if not sample_exercises:
            pytest.skip("No exercises loaded")

        filtered = filter_exercises(sample_exercises, difficulty="easy")
        assert all(e.difficulty == "easy" for e in filtered)

    def test_filter_by_exam(self, sample_exercises):
        """Test filtering by exam."""
        if not sample_exercises:
            pytest.skip("No exercises loaded")

        filtered = filter_exercises(sample_exercises, exam="associate")
        assert all(e.exam == "associate" for e in filtered)

    def test_filter_combined(self, sample_exercises):
        """Test combined filters."""
        if not sample_exercises:
            pytest.skip("No exercises loaded")

        first_domain = sample_exercises[0].domain
        filtered = filter_exercises(sample_exercises, domain=first_domain, difficulty="medium")

        assert all(e.domain == first_domain and e.difficulty == "medium" for e in filtered)

    def test_filter_empty_result(self, sample_exercises):
        """Test filtering that returns empty result.

        Professional exercises never live in the Associate-only domain
        "Databricks Lakehouse Platform", so this combination is always empty.
        """
        filtered = filter_exercises(
            sample_exercises,
            exam="professional",
            domain="Databricks Lakehouse Platform",
        )
        assert filtered == []


class TestExerciseCount:
    """Tests to verify exercise counts by domain."""

    def test_all_exercises_loaded(self):
        """The corpus loads cleanly with both exams represented.

        Counts are intentionally NOT hard-coded — the content bank grows over
        time. We assert invariants (no load errors, both exams present, total
        is the sum of the exam splits) rather than a magic number.
        """
        exercises, error_count, error_log = load_exercises_from_directory()
        assert error_count == 0, f"content load errors: {error_log[:3]}"
        assert len(exercises) > 0

        by_exam = {}
        for ex in exercises:
            by_exam[ex.exam.value] = by_exam.get(ex.exam.value, 0) + 1
        # Both exam levels are seeded.
        assert by_exam.get("associate", 0) > 0
        assert by_exam.get("professional", 0) > 0
        assert sum(by_exam.values()) == len(exercises)

    def test_domain_distribution(self):
        """Every Associate and Professional domain is represented (count-agnostic)."""
        exercises, _, _ = load_exercises_from_directory()

        by_domain = {}
        for ex in exercises:
            domain = ex.domain.value
            by_domain[domain] = by_domain.get(domain, 0) + 1

        associate_domains = [
            "Databricks Lakehouse Platform",
            "ELT with Spark SQL and Python",
            "Incremental Data Processing",
            "Production Pipelines",
            "Data Governance",  # shared with Professional
        ]
        professional_only = [
            "Developing Code for Data Processing",
            "Data Ingestion & Acquisition",
            "Data Transformation, Cleansing, and Quality",
            "Data Sharing and Federation",
            "Monitoring and Alerting",
            "Cost & Performance Optimization",
            "Ensuring Data Security and Compliance",
            "Debugging and Deploying",
            "Data Modelling",
        ]
        for domain in associate_domains + professional_only:
            assert by_domain.get(domain, 0) > 0, f"no exercises in domain: {domain}"
