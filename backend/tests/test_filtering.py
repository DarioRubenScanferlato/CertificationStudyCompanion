"""Comprehensive tests for exercise filtering functionality."""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    """Fixture providing a test client for the FastAPI app."""
    return TestClient(app)


class TestDomainFiltering:
    """Test filtering by domain."""

    def test_filter_by_databricks_lakehouse_platform(self, client):
        """Test filtering by Databricks Intelligence Platform domain."""
        response = client.get("/api/exercises?domain=Databricks%20Intelligence%20Platform")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["error"] is None
        assert isinstance(data["data"], list)

        if len(data["data"]) > 0:
            for exercise in data["data"]:
                assert exercise["domain"] == "Databricks Intelligence Platform"

    def test_filter_by_elt_spark(self, client):
        """Test filtering by Data Transformation and Modeling domain."""
        response = client.get("/api/exercises?domain=Data%20Transformation%20and%20Modeling")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["error"] is None

        if len(data["data"]) > 0:
            for exercise in data["data"]:
                assert exercise["domain"] == "Data Transformation and Modeling"

    def test_filter_by_incremental_processing(self, client):
        """Test filtering by Data Ingestion and Loading domain."""
        response = client.get("/api/exercises?domain=Data%20Ingestion%20and%20Loading")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["error"] is None

        if len(data["data"]) > 0:
            for exercise in data["data"]:
                assert exercise["domain"] == "Data Ingestion and Loading"

    def test_filter_by_production_pipelines(self, client):
        """Test filtering by Working with Lakeflow Jobs domain."""
        response = client.get("/api/exercises?domain=Working%20with%20Lakeflow%20Jobs")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["error"] is None

        if len(data["data"]) > 0:
            for exercise in data["data"]:
                assert exercise["domain"] == "Working with Lakeflow Jobs"

    def test_filter_by_data_governance(self, client):
        """Test filtering by Data Governance domain."""
        response = client.get("/api/exercises?domain=Data%20Governance")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["error"] is None

        if len(data["data"]) > 0:
            for exercise in data["data"]:
                assert exercise["domain"] == "Data Governance"

    def test_filter_by_domain_case_insensitive(self, client):
        """Test that domain filtering is case-insensitive."""
        # Test with lowercase
        response_lower = client.get("/api/exercises?domain=databricks%20lakehouse%20platform")
        assert response_lower.status_code == 200

        # Test with mixed case
        response_mixed = client.get("/api/exercises?domain=DataBricks%20Lakehouse%20Platform")
        assert response_mixed.status_code == 200

        # Both should return exercises from the same domain
        data_lower = response_lower.json()["data"]
        data_mixed = response_mixed.json()["data"]

        if len(data_lower) > 0 and len(data_mixed) > 0:
            assert len(data_lower) == len(data_mixed)

    def test_filter_by_invalid_domain(self, client):
        """Test filtering with invalid domain name returns error."""
        response = client.get("/api/exercises?domain=InvalidDomain")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert data["error"] is not None
        assert "Invalid domain" in data["error"]
        assert "InvalidDomain" in data["error"]
        assert isinstance(data["data"], list)
        assert len(data["data"]) == 0


class TestEnumValidation:
    """Test enum validation for filter parameters."""

    def test_invalid_domain_returns_error(self, client):
        """Test that invalid domain returns error message."""
        response = client.get("/api/exercises?domain=NonexistentDomain")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "Invalid domain" in data["error"]
        assert "Valid domains are:" in data["error"]

    def test_invalid_difficulty_returns_error(self, client):
        """Test that invalid difficulty returns error message."""
        response = client.get("/api/exercises?difficulty=impossible")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "Invalid difficulty" in data["error"]

    def test_invalid_exam_returns_error(self, client):
        """Test that invalid exam type returns error message."""
        response = client.get("/api/exercises?exam=master")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "Invalid exam type" in data["error"]

    def test_invalid_exercise_type_returns_error(self, client):
        """Test that invalid exercise type returns error message."""
        response = client.get("/api/exercises?exercise_type=essay_question")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "Invalid exercise type" in data["error"]

    def test_multiple_invalid_filters_returns_multiple_errors(self, client):
        """Test that multiple invalid filters produce multiple error messages."""
        response = client.get("/api/exercises?domain=BadDomain&difficulty=impossible&exam=expert")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        # Should contain all three error messages
        assert "Invalid domain" in data["error"]
        assert "Invalid difficulty" in data["error"]
        assert "Invalid exam type" in data["error"]

    def test_error_response_has_empty_data_array(self, client):
        """Test that error response has empty data array."""
        response = client.get("/api/exercises?domain=InvalidDomain")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert data["data"] == []
        assert data["error"] is not None


class TestDifficultyFiltering:
    """Test filtering by difficulty."""

    def test_filter_by_easy_difficulty(self, client):
        """Test filtering by easy difficulty."""
        response = client.get("/api/exercises?difficulty=easy")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["error"] is None

        if len(data["data"]) > 0:
            for exercise in data["data"]:
                assert exercise["difficulty"] == "easy"

    def test_filter_by_medium_difficulty(self, client):
        """Test filtering by medium difficulty."""
        response = client.get("/api/exercises?difficulty=medium")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["error"] is None

        if len(data["data"]) > 0:
            for exercise in data["data"]:
                assert exercise["difficulty"] == "medium"

    def test_filter_by_hard_difficulty(self, client):
        """Test filtering by hard difficulty."""
        response = client.get("/api/exercises?difficulty=hard")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["error"] is None

        if len(data["data"]) > 0:
            for exercise in data["data"]:
                assert exercise["difficulty"] == "hard"

    def test_filter_by_invalid_difficulty(self, client):
        """Test filtering with invalid difficulty value."""
        response = client.get("/api/exercises?difficulty=expert")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "Invalid difficulty" in data["error"]
        assert isinstance(data["data"], list)
        assert len(data["data"]) == 0


class TestExamTypeFiltering:
    """Test filtering by exam type."""

    def test_filter_by_associate_exam(self, client):
        """Test filtering by associate exam."""
        response = client.get("/api/exercises?exam=associate")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["error"] is None

        if len(data["data"]) > 0:
            for exercise in data["data"]:
                assert exercise["exam"] == "associate"

    def test_filter_by_professional_exam(self, client):
        """Test filtering by professional exam."""
        response = client.get("/api/exercises?exam=professional")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["error"] is None

        if len(data["data"]) > 0:
            for exercise in data["data"]:
                assert exercise["exam"] == "professional"

    def test_filter_by_invalid_exam_type(self, client):
        """Test filtering with invalid exam type."""
        response = client.get("/api/exercises?exam=master")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "Invalid exam type" in data["error"]
        assert isinstance(data["data"], list)
        assert len(data["data"]) == 0


class TestExerciseTypeFiltering:
    """Test filtering by exercise type."""

    def test_filter_by_single_choice(self, client):
        """Test filtering by single choice exercises."""
        response = client.get("/api/exercises?exercise_type=single_choice")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["error"] is None

        if len(data["data"]) > 0:
            for exercise in data["data"]:
                assert exercise["type"] == "single_choice"

    def test_filter_by_multi_choice(self, client):
        """Test filtering by multi choice exercises."""
        response = client.get("/api/exercises?exercise_type=multi_choice")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["error"] is None

        if len(data["data"]) > 0:
            for exercise in data["data"]:
                assert exercise["type"] == "multi_choice"

    def test_filter_by_code_completion(self, client):
        """Test filtering by code completion exercises."""
        response = client.get("/api/exercises?exercise_type=code_completion")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["error"] is None

        if len(data["data"]) > 0:
            for exercise in data["data"]:
                assert exercise["type"] == "code_completion"

    def test_filter_by_invalid_exercise_type(self, client):
        """Test filtering with invalid exercise type."""
        response = client.get("/api/exercises?exercise_type=essay")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "Invalid exercise type" in data["error"]
        assert isinstance(data["data"], list)
        assert len(data["data"]) == 0


class TestCombinedFiltering:
    """Test combined filters."""

    def test_filter_by_domain_and_difficulty(self, client):
        """Test combined filtering: domain + difficulty."""
        response = client.get(
            "/api/exercises?domain=Databricks%20Intelligence%20Platform&difficulty=easy"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["error"] is None

        if len(data["data"]) > 0:
            for exercise in data["data"]:
                assert exercise["domain"] == "Databricks Intelligence Platform"
                assert exercise["difficulty"] == "easy"

    def test_filter_by_domain_and_exam(self, client):
        """Test combined filtering: domain + exam."""
        response = client.get(
            "/api/exercises?domain=Databricks%20Intelligence%20Platform&exam=associate"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["error"] is None

        if len(data["data"]) > 0:
            for exercise in data["data"]:
                assert exercise["domain"] == "Databricks Intelligence Platform"
                assert exercise["exam"] == "associate"

    def test_filter_by_domain_difficulty_and_exam(self, client):
        """Test combined filtering: domain + difficulty + exam."""
        response = client.get(
            "/api/exercises?domain=Databricks%20Intelligence%20Platform&difficulty=easy&exam=associate"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["error"] is None

        if len(data["data"]) > 0:
            for exercise in data["data"]:
                assert exercise["domain"] == "Databricks Intelligence Platform"
                assert exercise["difficulty"] == "easy"
                assert exercise["exam"] == "associate"

    def test_filter_by_all_parameters(self, client):
        """Test combined filtering: all parameters."""
        response = client.get(
            "/api/exercises?domain=Databricks%20Intelligence%20Platform&difficulty=easy&exam=associate&exercise_type=single_choice"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["error"] is None

        if len(data["data"]) > 0:
            for exercise in data["data"]:
                assert exercise["domain"] == "Databricks Intelligence Platform"
                assert exercise["difficulty"] == "easy"
                assert exercise["exam"] == "associate"
                assert exercise["type"] == "single_choice"


class TestResponseFormat:
    """Test response format validation."""

    def test_response_format_structure(self, client):
        """Test that response has correct structure."""
        response = client.get("/api/exercises")
        assert response.status_code == 200
        data = response.json()

        # Check required fields
        assert "success" in data
        assert "data" in data
        assert "error" in data

        # Check types
        assert isinstance(data["success"], bool)
        assert isinstance(data["data"], list)
        assert data["error"] is None or isinstance(data["error"], str)

    def test_response_format_with_filters(self, client):
        """Test response format with filters applied."""
        response = client.get("/api/exercises?domain=Databricks%20Intelligence%20Platform")
        assert response.status_code == 200
        data = response.json()

        assert isinstance(data["success"], bool)
        assert data["success"] is True
        assert isinstance(data["data"], list)
        assert data["error"] is None

    def test_exercise_fields_in_response(self, client):
        """Test that exercise objects have required fields."""
        response = client.get(
            "/api/exercises?domain=Databricks%20Intelligence%20Platform&difficulty=easy"
        )
        assert response.status_code == 200
        data = response.json()

        if len(data["data"]) > 0:
            exercise = data["data"][0]
            required_fields = [
                "id",
                "type",
                "exam",
                "domain",
                "difficulty",
                "question",
                "explanation",
            ]
            for field in required_fields:
                assert field in exercise


class TestEmptyResults:
    """Test scenarios with empty results."""

    def test_empty_results_with_no_matching_domain(self, client):
        """Test error response when domain is invalid."""
        response = client.get("/api/exercises?domain=NonexistentDomain")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert data["data"] == []
        assert data["error"] is not None
        assert "Invalid domain" in data["error"]

    def test_empty_results_with_combined_filters_no_match(self, client):
        """Test empty results when combined filters have no matches."""
        # Try to find professional exam exercises (probably don't exist yet)
        response = client.get("/api/exercises?exam=professional&difficulty=hard")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)
        assert data["error"] is None


class TestEndpointValidation:
    """Test endpoint validation and error handling."""

    def test_get_all_exercises_no_filters(self, client):
        """Test getting all exercises without filters."""
        response = client.get("/api/exercises")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["error"] is None
        assert isinstance(data["data"], list)
        assert len(data["data"]) > 0

    def test_endpoint_returns_json(self, client):
        """Test that endpoint returns valid JSON."""
        response = client.get("/api/exercises")
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("application/json")

    def test_multiple_query_parameters(self, client):
        """Test endpoint accepts multiple query parameters."""
        response = client.get(
            "/api/exercises?domain=Databricks%20Intelligence%20Platform&difficulty=easy&exam=associate&exercise_type=single_choice"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)
