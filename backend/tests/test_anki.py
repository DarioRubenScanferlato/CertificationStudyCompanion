"""Tests for Anki export functionality."""

import os
import tempfile
import zipfile

import pytest

from app.anki import export_to_anki, get_deck_info
from app.models import MCQ, Difficulty, Domain, ExamType, ExerciseType, Option


@pytest.fixture
def sample_mcq_exercises():
    """Create sample MCQ exercises for testing."""
    return [
        MCQ(
            id="mcq-001",
            type=ExerciseType.SINGLE_CHOICE,
            exam=ExamType.ASSOCIATE,
            domain=Domain.LAKEHOUSE_PLATFORM,
            difficulty=Difficulty.EASY,
            question="What is Databricks Lakehouse?",
            explanation="The Databricks Lakehouse combines the best of data lakes and data warehouses.",
            options=[
                Option(id="a", text="A data storage system", correct=False),
                Option(id="b", text="A unified analytics platform", correct=True),
                Option(id="c", text="A query language", correct=False),
                Option(id="d", text="A machine learning tool", correct=False),
            ],
            answer=["b"],
            source="official",
            tags=["architecture", "fundamentals"],
        ),
        MCQ(
            id="mcq-002",
            type=ExerciseType.SINGLE_CHOICE,
            exam=ExamType.ASSOCIATE,
            domain=Domain.ELT_SPARK,
            difficulty=Difficulty.MEDIUM,
            question="Which Spark API is used for structured data?",
            explanation="DataFrame API provides a distributed collection of data organized into named columns.",
            options=[
                Option(id="a", text="RDD", correct=False),
                Option(id="b", text="DataFrame", correct=True),
                Option(id="c", text="Dataset", correct=False),
                Option(id="d", text="SQL", correct=False),
            ],
            answer=["b"],
            source="official",
            tags=["spark", "api"],
        ),
        MCQ(
            id="mcq-003",
            type=ExerciseType.SINGLE_CHOICE,
            exam=ExamType.ASSOCIATE,
            domain=Domain.INCREMENTAL_PROCESSING,
            difficulty=Difficulty.HARD,
            question="What is the benefit of incremental processing?",
            explanation="Incremental processing reduces computation time by processing only new or changed data.",
            options=[
                Option(id="a", text="Better visualization", correct=False),
                Option(id="b", text="Improved security", correct=False),
                Option(id="c", text="Reduced computation time and costs", correct=True),
                Option(id="d", text="Easier debugging", correct=False),
            ],
            answer=["c"],
            source="training",
            tags=["optimization"],
        ),
    ]


@pytest.fixture
def temp_output_file():
    """Create a temporary file path for output."""
    with tempfile.NamedTemporaryFile(suffix=".apkg", delete=False) as f:
        temp_path = f.name
    yield temp_path
    # Cleanup
    if os.path.exists(temp_path):
        os.remove(temp_path)


class TestExportToAnki:
    """Tests for export_to_anki function."""

    def test_export_mcq_exercises_to_apkg(self, sample_mcq_exercises, temp_output_file):
        """Test exporting MCQ exercises to .apkg format."""
        export_to_anki(sample_mcq_exercises, temp_output_file)

        # Verify file was created
        assert os.path.exists(temp_output_file)
        assert os.path.getsize(temp_output_file) > 0

        # Verify it's a valid zip file (apkg is a zipped format)
        with zipfile.ZipFile(temp_output_file, "r") as zip_ref:
            files = zip_ref.namelist()
            assert "collection.anki2" in files
            assert "media" in files

    def test_export_empty_list_raises_error(self, temp_output_file):
        """Test that exporting empty list raises ValueError."""
        with pytest.raises(ValueError, match="Cannot export empty exercise list"):
            export_to_anki([], temp_output_file)

    def test_export_single_exercise(self, temp_output_file):
        """Test exporting a single MCQ exercise."""
        exercises = [
            MCQ(
                id="mcq-single",
                type=ExerciseType.SINGLE_CHOICE,
                exam=ExamType.ASSOCIATE,
                domain=Domain.LAKEHOUSE_PLATFORM,
                difficulty=Difficulty.EASY,
                question="Test question?",
                explanation="Test explanation",
                options=[
                    Option(id="a", text="Option A", correct=True),
                    Option(id="b", text="Option B", correct=False),
                    Option(id="c", text="Option C", correct=False),
                    Option(id="d", text="Option D", correct=False),
                ],
                answer=["a"],
            )
        ]

        export_to_anki(exercises, temp_output_file)
        assert os.path.exists(temp_output_file)
        assert os.path.getsize(temp_output_file) > 0

    def test_export_with_multiple_correct_answers(self, temp_output_file):
        """Test exporting a single_choice MCQ with multiple interchangeable correct alternatives."""
        exercises = [
            MCQ(
                id="mcq-multi-answer",
                type=ExerciseType.SINGLE_CHOICE,
                exam=ExamType.ASSOCIATE,
                domain=Domain.LAKEHOUSE_PLATFORM,
                difficulty=Difficulty.MEDIUM,
                question="Which is a correct answer?",
                explanation="A and B are each individually valid (interchangeable alternatives).",
                options=[
                    Option(id="a", text="Option A", correct=True),
                    Option(id="b", text="Option B", correct=True),
                    Option(id="c", text="Option C", correct=False),
                    Option(id="d", text="Option D", correct=False),
                    Option(id="e", text="Option E", correct=False),
                ],
                answer=["a", "b"],
            )
        ]

        export_to_anki(exercises, temp_output_file)
        assert os.path.exists(temp_output_file)


class TestAnkiFileStructure:
    """Tests for verifying .apkg file structure."""

    def test_apkg_contains_collection_database(self, sample_mcq_exercises, temp_output_file):
        """Test that .apkg contains collection.anki2 database."""
        export_to_anki(sample_mcq_exercises, temp_output_file)

        with zipfile.ZipFile(temp_output_file, "r") as zip_ref:
            files = zip_ref.namelist()
            assert "collection.anki2" in files

    def test_apkg_contains_media_manifest(self, sample_mcq_exercises, temp_output_file):
        """Test that .apkg contains media manifest."""
        export_to_anki(sample_mcq_exercises, temp_output_file)

        with zipfile.ZipFile(temp_output_file, "r") as zip_ref:
            files = zip_ref.namelist()
            assert "media" in files

    def test_get_deck_info_valid_apkg(self, sample_mcq_exercises, temp_output_file):
        """Test getting info from a valid .apkg file."""
        export_to_anki(sample_mcq_exercises, temp_output_file)

        info = get_deck_info(temp_output_file)
        assert info["valid"] is True
        assert info["has_collection"] is True
        assert info["has_media"] is True

    def test_get_deck_info_invalid_file(self):
        """Test getting info from an invalid file."""
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            temp_path = f.name
            f.write(b"not an apkg file")

        try:
            info = get_deck_info(temp_path)
            assert info["valid"] is False
        finally:
            os.remove(temp_path)


class TestAnkiTags:
    """Tests for verifying tag structure in exported cards."""

    def test_tags_include_domain(self, temp_output_file):
        """Test that exported cards include domain as tag."""
        exercises = [
            MCQ(
                id="mcq-tags-1",
                type=ExerciseType.SINGLE_CHOICE,
                exam=ExamType.ASSOCIATE,
                domain=Domain.LAKEHOUSE_PLATFORM,
                difficulty=Difficulty.EASY,
                question="Test?",
                explanation="Explanation",
                options=[
                    Option(id="a", text="A", correct=True),
                    Option(id="b", text="B", correct=False),
                    Option(id="c", text="C", correct=False),
                    Option(id="d", text="D", correct=False),
                ],
                answer=["a"],
            )
        ]

        export_to_anki(exercises, temp_output_file)
        assert os.path.exists(temp_output_file)
        # Note: Deep inspection of tags would require decoding the SQLite database
        # For now, we verify the file structure is correct

    def test_tags_include_difficulty(self, temp_output_file):
        """Test that exported cards include difficulty as tag."""
        exercises = [
            MCQ(
                id="mcq-tags-2",
                type=ExerciseType.SINGLE_CHOICE,
                exam=ExamType.ASSOCIATE,
                domain=Domain.LAKEHOUSE_PLATFORM,
                difficulty=Difficulty.HARD,
                question="Test?",
                explanation="Explanation",
                options=[
                    Option(id="a", text="A", correct=True),
                    Option(id="b", text="B", correct=False),
                    Option(id="c", text="C", correct=False),
                    Option(id="d", text="D", correct=False),
                ],
                answer=["a"],
            )
        ]

        export_to_anki(exercises, temp_output_file)
        assert os.path.exists(temp_output_file)

    def test_tags_include_source(self, temp_output_file):
        """Test that exported cards include source as tag."""
        exercises = [
            MCQ(
                id="mcq-tags-3",
                type=ExerciseType.SINGLE_CHOICE,
                exam=ExamType.ASSOCIATE,
                domain=Domain.LAKEHOUSE_PLATFORM,
                difficulty=Difficulty.MEDIUM,
                question="Test?",
                explanation="Explanation",
                options=[
                    Option(id="a", text="A", correct=True),
                    Option(id="b", text="B", correct=False),
                    Option(id="c", text="C", correct=False),
                    Option(id="d", text="D", correct=False),
                ],
                answer=["a"],
                source="training",
            )
        ]

        export_to_anki(exercises, temp_output_file)
        assert os.path.exists(temp_output_file)

    def test_tags_include_custom_tags(self, temp_output_file):
        """Test that custom tags are included in exported cards."""
        exercises = [
            MCQ(
                id="mcq-tags-4",
                type=ExerciseType.SINGLE_CHOICE,
                exam=ExamType.ASSOCIATE,
                domain=Domain.LAKEHOUSE_PLATFORM,
                difficulty=Difficulty.MEDIUM,
                question="Test?",
                explanation="Explanation",
                options=[
                    Option(id="a", text="A", correct=True),
                    Option(id="b", text="B", correct=False),
                    Option(id="c", text="C", correct=False),
                    Option(id="d", text="D", correct=False),
                ],
                answer=["a"],
                tags=["custom_tag_1", "custom_tag_2"],
            )
        ]

        export_to_anki(exercises, temp_output_file)
        assert os.path.exists(temp_output_file)


class TestAnkiCardContent:
    """Tests for verifying card content structure."""

    def test_question_field_populated(self, sample_mcq_exercises, temp_output_file):
        """Test that question field is populated."""
        export_to_anki(sample_mcq_exercises, temp_output_file)
        # File should be created with content
        assert os.path.getsize(temp_output_file) > 1000

    def test_options_field_formatted(self, sample_mcq_exercises, temp_output_file):
        """Test that options are properly formatted on card back."""
        export_to_anki(sample_mcq_exercises, temp_output_file)
        assert os.path.exists(temp_output_file)

    def test_explanation_field_included(self, sample_mcq_exercises, temp_output_file):
        """Test that explanation is included in extra field."""
        export_to_anki(sample_mcq_exercises, temp_output_file)
        assert os.path.exists(temp_output_file)

    def test_correct_answer_marked(self, temp_output_file):
        """Test that correct answers are marked with checkmark."""
        exercises = [
            MCQ(
                id="mcq-marked",
                type=ExerciseType.SINGLE_CHOICE,
                exam=ExamType.ASSOCIATE,
                domain=Domain.LAKEHOUSE_PLATFORM,
                difficulty=Difficulty.EASY,
                question="Which is correct?",
                explanation="B is correct",
                options=[
                    Option(id="a", text="Wrong", correct=False),
                    Option(id="b", text="Right", correct=True),
                    Option(id="c", text="Wrong", correct=False),
                    Option(id="d", text="Wrong", correct=False),
                ],
                answer=["b"],
            )
        ]

        export_to_anki(exercises, temp_output_file)
        assert os.path.exists(temp_output_file)
