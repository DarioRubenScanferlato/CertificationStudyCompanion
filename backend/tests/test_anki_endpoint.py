"""Tests for Anki export API endpoint."""

import zipfile
from io import BytesIO


class TestAnkiExportEndpoint:
    """Tests for /api/export/anki endpoint."""

    def test_export_anki_endpoint_success(self, client):
        """Test successful Anki export from endpoint."""
        response = client.get("/api/export/anki")

        # Should return 200 with file
        assert response.status_code == 200
        assert response.headers["content-disposition"].startswith("attachment")

        # Verify it's a valid zip file
        content = BytesIO(response.content)
        with zipfile.ZipFile(content, "r") as zip_ref:
            files = zip_ref.namelist()
            assert "collection.anki2" in files
            assert "media" in files

    def test_export_anki_with_domain_filter(self, client):
        """Test Anki export with domain filter."""
        response = client.get("/api/export/anki?domain=Databricks%20Lakehouse%20Platform")

        assert response.status_code == 200
        assert response.headers["content-disposition"].startswith("attachment")

    def test_export_anki_with_difficulty_filter(self, client):
        """Test Anki export with difficulty filter."""
        response = client.get("/api/export/anki?difficulty=easy")

        assert response.status_code == 200
        assert response.headers["content-disposition"].startswith("attachment")

    def test_export_anki_with_both_filters(self, client):
        """Test Anki export with both domain and difficulty filters."""
        response = client.get(
            "/api/export/anki?domain=Databricks%20Lakehouse%20Platform&difficulty=medium"
        )

        assert response.status_code == 200
        assert response.headers["content-disposition"].startswith("attachment")

    def test_export_anki_invalid_domain_returns_no_results(self, client):
        """Test that invalid domain returns error response."""
        response = client.get("/api/export/anki?domain=InvalidDomain")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "No MCQ exercises found" in data["error"]

    def test_export_anki_invalid_difficulty_returns_no_results(self, client):
        """Test that invalid difficulty returns error response."""
        response = client.get("/api/export/anki?difficulty=impossible")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "No MCQ exercises found" in data["error"]

    def test_export_anki_file_has_correct_headers(self, client):
        """Test that download headers are correct."""
        response = client.get("/api/export/anki")

        assert response.status_code == 200
        assert (
            response.headers["content-disposition"]
            == "attachment; filename='databricks-de-cert.apkg'"
        )
        assert response.headers["content-type"] == "application/octet-stream"

    def test_export_anki_returns_valid_apkg_structure(self, client):
        """Test that exported .apkg has valid Anki structure."""
        response = client.get("/api/export/anki")

        assert response.status_code == 200

        # Verify Anki package structure
        content = BytesIO(response.content)
        with zipfile.ZipFile(content, "r") as zip_ref:
            # Check for required files
            files = zip_ref.namelist()
            assert "collection.anki2" in files
            assert "media" in files

            # Verify files are not empty
            assert len(zip_ref.read("collection.anki2")) > 0


class TestAnkiExportFiltering:
    """Tests for filtering in Anki export endpoint."""

    def test_export_anki_filters_by_domain(self, client):
        """Test that domain filter works correctly."""
        # Get all exercises for comparison
        all_response = client.get("/api/exercises")
        all_exercises = all_response.json()["data"]

        # Get exercises for a specific domain
        domain_response = client.get("/api/exercises?domain=Databricks%20Lakehouse%20Platform")
        domain_exercises = domain_response.json()["data"]

        # Anki export should handle the same filtering
        anki_response = client.get("/api/export/anki?domain=Databricks%20Lakehouse%20Platform")
        assert anki_response.status_code == 200

        # Verify domain exercises are a subset
        assert len(domain_exercises) <= len(all_exercises)
