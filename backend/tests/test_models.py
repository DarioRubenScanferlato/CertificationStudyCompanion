"""Tests for Pydantic exercise models."""

import pytest

from app.models import MCQ, CodeCompletion, Difficulty, Domain, ExamType, ExerciseType, Option


class TestMCQModel:
    """Tests for MCQ model."""

    def test_create_valid_mcq(self):
        """Test creating a valid MCQ."""
        mcq = MCQ(
            id="dbx-de-0001",
            type=ExerciseType.SINGLE_CHOICE,
            exam=ExamType.ASSOCIATE,
            domain=Domain.LAKEHOUSE_PLATFORM,
            difficulty=Difficulty.EASY,
            question="What is Delta Lake?",
            options=[
                Option(id="a", text="A data format", correct=True),
                Option(id="b", text="A database", correct=False),
            ],
            answer=["a"],
            explanation="Delta Lake is a storage format with ACID guarantees.",
        )
        assert mcq.id == "dbx-de-0001"
        assert mcq.type == ExerciseType.SINGLE_CHOICE
        assert len(mcq.options) == 2

    def test_mcq_requires_at_least_one_option(self):
        """Test that MCQ requires at least one option."""
        with pytest.raises(ValueError, match="at least one option"):
            MCQ(
                id="test",
                exam=ExamType.ASSOCIATE,
                domain=Domain.LAKEHOUSE_PLATFORM,
                difficulty=Difficulty.EASY,
                question="Test?",
                options=[],
                answer=["a"],
                explanation="Test",
            )

    def test_mcq_requires_at_least_one_correct_option(self):
        """Test that MCQ requires at least one option marked correct."""
        with pytest.raises(ValueError, match="at least one option marked correct"):
            MCQ(
                id="test",
                exam=ExamType.ASSOCIATE,
                domain=Domain.LAKEHOUSE_PLATFORM,
                difficulty=Difficulty.EASY,
                question="Test?",
                options=[Option(id="a", text="Option", correct=False)],
                explanation="Test",
            )

    def test_mcq_answer_derived_from_correct_flags(self):
        """Answer is derived from option correct flags; provided answer is ignored."""
        mcq = MCQ(
            id="test",
            exam=ExamType.ASSOCIATE,
            domain=Domain.LAKEHOUSE_PLATFORM,
            difficulty=Difficulty.EASY,
            question="Test?",
            options=[
                Option(id="a", text="Right", correct=True),
                Option(id="b", text="Wrong", correct=False),
            ],
            answer=["x", "b"],  # bogus/author-supplied input, must be ignored
            explanation="Test",
        )
        assert mcq.answer == ["a"]

    def test_single_choice_rejects_multiple_correct(self):
        """A single_choice exercise must have exactly one correct option."""
        with pytest.raises(ValueError, match="exactly one correct option"):
            MCQ(
                id="test",
                type=ExerciseType.SINGLE_CHOICE,
                exam=ExamType.ASSOCIATE,
                domain=Domain.LAKEHOUSE_PLATFORM,
                difficulty=Difficulty.EASY,
                question="Test?",
                options=[
                    Option(id="a", text="One", correct=True),
                    Option(id="b", text="Two", correct=True),
                ],
                explanation="Test",
            )

    def test_mcq_multi_choice(self):
        """Test creating a multi-choice MCQ."""
        mcq = MCQ(
            id="dbx-de-0002",
            type=ExerciseType.MULTI_CHOICE,
            exam=ExamType.ASSOCIATE,
            domain=Domain.ELT_SPARK,
            difficulty=Difficulty.MEDIUM,
            question="Which are true? (Select all)",
            options=[
                Option(id="a", text="First", correct=True),
                Option(id="b", text="Second", correct=True),
                Option(id="c", text="Third", correct=False),
            ],
            answer=["a", "b"],
            explanation="Both A and B are correct.",
        )
        assert mcq.type == ExerciseType.MULTI_CHOICE
        assert len(mcq.answer) == 2


class TestCodeCompletionModel:
    """Tests for CodeCompletion model."""

    def test_create_valid_code_completion(self):
        """Test creating a valid code completion exercise."""
        cc = CodeCompletion(
            id="dbx-code-0001",
            exam=ExamType.ASSOCIATE,
            domain=Domain.ELT_SPARK,
            difficulty=Difficulty.EASY,
            language="pyspark",
            question="Read a Delta table",
            template='df = spark.read.format("___").table("events")',
            answer="delta",
            explanation="Delta is the default format.",
        )
        assert cc.id == "dbx-code-0001"
        assert cc.language == "pyspark"
        assert "___" in cc.template

    def test_code_completion_requires_blank_in_template(self):
        """Test that template must contain ___."""
        with pytest.raises(ValueError, match="must contain"):
            CodeCompletion(
                id="test",
                exam=ExamType.ASSOCIATE,
                domain=Domain.ELT_SPARK,
                difficulty=Difficulty.EASY,
                language="pyspark",
                question="Test?",
                template="df = spark.read.format()",  # Missing ___
                answer="delta",
                explanation="Test",
            )

    def test_code_completion_requires_non_empty_answer(self):
        """Test that answer must not be empty."""
        with pytest.raises(ValueError, match="must not be empty"):
            CodeCompletion(
                id="test",
                exam=ExamType.ASSOCIATE,
                domain=Domain.ELT_SPARK,
                difficulty=Difficulty.EASY,
                language="pyspark",
                question="Test?",
                template="x = ___",
                answer="",
                explanation="Test",
            )

    def test_code_completion_with_accepted_alternatives(self):
        """Test code completion with alternative accepted answers."""
        cc = CodeCompletion(
            id="dbx-code-0002",
            exam=ExamType.ASSOCIATE,
            domain=Domain.ELT_SPARK,
            difficulty=Difficulty.MEDIUM,
            language="sql",
            question="Filter rows",
            template="SELECT * FROM table WHERE ___",
            answer="age > 18",
            accepted=["age >= 18", "age > 17"],
            explanation="Both conditions work.",
        )
        assert len(cc.accepted) == 2


class TestDomainEnum:
    """Tests for Domain enum."""

    def test_all_domains_present(self):
        """Test that all 5 Associate domains are defined."""
        domains = [d.value for d in Domain]
        assert len(domains) == 5
        assert "Databricks Lakehouse Platform" in domains
        assert "ELT with Spark SQL and Python" in domains
        assert "Incremental Data Processing" in domains
        assert "Production Pipelines" in domains
        assert "Data Governance" in domains

    def test_domain_values(self):
        """Test domain string values match blueprint."""
        assert Domain.LAKEHOUSE_PLATFORM.value == "Databricks Lakehouse Platform"
        assert Domain.ELT_SPARK.value == "ELT with Spark SQL and Python"
        assert Domain.INCREMENTAL_PROCESSING.value == "Incremental Data Processing"
        assert Domain.PRODUCTION_PIPELINES.value == "Production Pipelines"
        assert Domain.DATA_GOVERNANCE.value == "Data Governance"


class TestExerciseFromYAML:
    """Tests for loading exercises from YAML (implicit via models)."""

    def test_mcq_with_all_fields(self):
        """Test MCQ creation with all optional fields."""
        mcq = MCQ(
            id="dbx-de-full",
            type=ExerciseType.SINGLE_CHOICE,
            exam=ExamType.ASSOCIATE,
            domain=Domain.DATA_GOVERNANCE,
            difficulty=Difficulty.HARD,
            question="Advanced governance question?",
            options=[Option(id="a", text="Yes", correct=True)],
            answer=["a"],
            explanation="Full explanation here.",
            references=["https://docs.databricks.com/"],
            tags=["governance", "advanced"],
            source="original",
        )
        assert mcq.references == ["https://docs.databricks.com/"]
        assert "governance" in mcq.tags
        assert mcq.source == "original"

    def test_defaults_applied(self):
        """Test that defaults are applied correctly."""
        mcq = MCQ(
            id="test",
            exam=ExamType.ASSOCIATE,
            domain=Domain.LAKEHOUSE_PLATFORM,
            difficulty=Difficulty.MEDIUM,
            question="Q?",
            options=[Option(id="a", text="A", correct=True)],
            answer=["a"],
            explanation="Explained.",
        )
        assert mcq.references == []
        assert mcq.tags == []
        assert mcq.source == "original"
        assert mcq.type == ExerciseType.SINGLE_CHOICE  # Default for MCQ


class TestExerciseValidation:
    """Integration tests for exercise validation."""

    def test_json_serialization(self):
        """Test that exercises can be serialized to JSON."""
        mcq = MCQ(
            id="dbx-json",
            exam=ExamType.ASSOCIATE,
            domain=Domain.LAKEHOUSE_PLATFORM,
            difficulty=Difficulty.EASY,
            question="Q?",
            options=[Option(id="a", text="A", correct=True)],
            answer=["a"],
            explanation="E",
        )
        json_data = mcq.dict()
        assert json_data["id"] == "dbx-json"
        assert json_data["domain"] == "Databricks Lakehouse Platform"  # Enum value
        assert json_data["type"] == "single_choice"  # Enum value
