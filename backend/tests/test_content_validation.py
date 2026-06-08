"""Comprehensive tests for content validation and error handling."""

import tempfile
from pathlib import Path

from app.content import ContentValidationError, load_exercises_from_directory


class TestInvalidYAMLSyntax:
    """Tests for invalid YAML syntax handling."""

    def test_malformed_yaml_structure(self):
        """Test handling of malformed YAML syntax."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yaml_file = Path(tmpdir) / "invalid.yaml"
            # Invalid YAML: inconsistent indentation
            yaml_file.write_text("""
exercises:
  - id: test-001
    type: single_choice
  invalid indentation here
    exam: associate
""")

            exercises, error_count, error_log = load_exercises_from_directory(tmpdir)

            assert error_count == 1
            assert len(error_log) == 1
            assert error_log[0].error_type == "yaml_syntax_error"
            assert "test-001" not in [e.id for e in exercises]

    def test_invalid_yaml_with_tabs(self):
        """Test YAML with invalid tab characters."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yaml_file = Path(tmpdir) / "tabs.yaml"
            # Write with actual tabs (yaml.safe_load should reject this)
            content = "exercises:\n\t- id: test\n\t\ttype: single_choice\n"
            yaml_file.write_bytes(content.encode())

            exercises, error_count, error_log = load_exercises_from_directory(tmpdir)

            # Tabs are invalid for YAML indentation -> a syntax error, handled
            # gracefully (recorded, not raised) and no exercises loaded.
            assert error_count == 1
            assert len(error_log) == 1
            assert error_log[0].error_type == "yaml_syntax_error"
            assert exercises == []

    def test_missing_exercises_key(self):
        """Test YAML file without 'exercises' key."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yaml_file = Path(tmpdir) / "no_exercises.yaml"
            yaml_file.write_text("""
questions:
  - id: test-001
    type: single_choice
""")

            exercises, error_count, error_log = load_exercises_from_directory(tmpdir)

            assert error_count == 1
            assert len(error_log) == 1
            assert error_log[0].error_type == "missing_exercises_key"


class TestMissingRequiredFields:
    """Tests for missing required fields validation."""

    def test_missing_id_field(self):
        """Test exercise missing id field."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yaml_file = Path(tmpdir) / "missing_id.yaml"
            yaml_file.write_text("""
exercises:
  - type: single_choice
    exam: associate
    domain: "Databricks Intelligence Platform"
    difficulty: easy
    question: "Test question?"
    explanation: "Test explanation"
    options:
      - id: a
        text: "Option A"
        correct: true
    answer: [a]
""")

            exercises, error_count, error_log = load_exercises_from_directory(tmpdir)

            assert error_count == 1
            assert len(error_log) == 1
            assert error_log[0].error_type == "validation_error"
            assert "id" in error_log[0].message.lower()

    def test_missing_type_field(self):
        """Test exercise missing type field - defaults to single_choice."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yaml_file = Path(tmpdir) / "missing_type.yaml"
            yaml_file.write_text("""
exercises:
  - id: test-001
    exam: associate
    domain: "Databricks Intelligence Platform"
    difficulty: easy
    question: "Test question?"
    explanation: "Test explanation"
    options:
      - id: a
        text: "Option A"
        correct: true
      - id: b
        text: "Option B"
        correct: false
      - id: c
        text: "Option C"
        correct: false
      - id: d
        text: "Option D"
        correct: false
    answer: [a]
""")

            exercises, error_count, error_log = load_exercises_from_directory(tmpdir)

            # Type field has a default value, so it doesn't error
            assert error_count == 0
            assert len(exercises) == 1
            assert exercises[0].type.value == "single_choice"

    def test_missing_domain_field(self):
        """Test exercise missing domain field."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yaml_file = Path(tmpdir) / "missing_domain.yaml"
            yaml_file.write_text("""
exercises:
  - id: test-001
    type: single_choice
    exam: associate
    difficulty: easy
    question: "Test question?"
    explanation: "Test explanation"
    options:
      - id: a
        text: "Option A"
        correct: true
    answer: [a]
""")

            exercises, error_count, error_log = load_exercises_from_directory(tmpdir)

            assert error_count == 1
            assert error_log[0].error_type == "validation_error"

    def test_missing_question_field(self):
        """Test exercise missing question field."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yaml_file = Path(tmpdir) / "missing_question.yaml"
            yaml_file.write_text("""
exercises:
  - id: test-001
    type: single_choice
    exam: associate
    domain: "Databricks Intelligence Platform"
    difficulty: easy
    explanation: "Test explanation"
    options:
      - id: a
        text: "Option A"
        correct: true
    answer: [a]
""")

            exercises, error_count, error_log = load_exercises_from_directory(tmpdir)

            assert error_count == 1
            assert error_log[0].error_type == "validation_error"

    def test_missing_explanation_field(self):
        """Test exercise missing explanation field."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yaml_file = Path(tmpdir) / "missing_explanation.yaml"
            yaml_file.write_text("""
exercises:
  - id: test-001
    type: single_choice
    exam: associate
    domain: "Databricks Intelligence Platform"
    difficulty: easy
    question: "Test question?"
    options:
      - id: a
        text: "Option A"
        correct: true
    answer: [a]
""")

            exercises, error_count, error_log = load_exercises_from_directory(tmpdir)

            assert error_count == 1
            assert error_log[0].error_type == "validation_error"


class TestInvalidEnumValues:
    """Tests for invalid enum value validation."""

    def test_invalid_domain_value(self):
        """Test exercise with invalid domain."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yaml_file = Path(tmpdir) / "invalid_domain.yaml"
            yaml_file.write_text("""
exercises:
  - id: test-001
    type: single_choice
    exam: associate
    domain: "Invalid Domain"
    difficulty: easy
    question: "Test question?"
    explanation: "Test explanation"
    options:
      - id: a
        text: "Option A"
        correct: true
    answer: [a]
""")

            exercises, error_count, error_log = load_exercises_from_directory(tmpdir)

            assert error_count == 1
            assert error_log[0].error_type == "validation_error"
            assert "domain" in error_log[0].message.lower()

    def test_invalid_difficulty_value(self):
        """Test exercise with invalid difficulty."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yaml_file = Path(tmpdir) / "invalid_difficulty.yaml"
            yaml_file.write_text("""
exercises:
  - id: test-001
    type: single_choice
    exam: associate
    domain: "Databricks Intelligence Platform"
    difficulty: expert
    question: "Test question?"
    explanation: "Test explanation"
    options:
      - id: a
        text: "Option A"
        correct: true
    answer: [a]
""")

            exercises, error_count, error_log = load_exercises_from_directory(tmpdir)

            assert error_count == 1
            assert error_log[0].error_type == "validation_error"

    def test_invalid_exam_value(self):
        """Test exercise with invalid exam type."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yaml_file = Path(tmpdir) / "invalid_exam.yaml"
            yaml_file.write_text("""
exercises:
  - id: test-001
    type: single_choice
    exam: invalid_exam
    domain: "Databricks Intelligence Platform"
    difficulty: easy
    question: "Test question?"
    explanation: "Test explanation"
    options:
      - id: a
        text: "Option A"
        correct: true
    answer: [a]
""")

            exercises, error_count, error_log = load_exercises_from_directory(tmpdir)

            assert error_count == 1
            assert error_log[0].error_type == "validation_error"

    def test_invalid_exercise_type(self):
        """Test exercise with invalid type."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yaml_file = Path(tmpdir) / "invalid_type.yaml"
            yaml_file.write_text("""
exercises:
  - id: test-001
    type: invalid_type
    exam: associate
    domain: "Databricks Intelligence Platform"
    difficulty: easy
    question: "Test question?"
    explanation: "Test explanation"
    options:
      - id: a
        text: "Option A"
        correct: true
    answer: [a]
""")

            exercises, error_count, error_log = load_exercises_from_directory(tmpdir)

            # An explicitly-provided but unknown type is rejected as such,
            # rather than being silently coerced into an MCQ.
            assert error_count == 1
            assert error_log[0].error_type == "unknown_type"
            assert len(exercises) == 0


class TestMalformedMCQ:
    """Tests for malformed MCQ exercises."""

    def test_missing_options(self):
        """Test MCQ with missing options field."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yaml_file = Path(tmpdir) / "missing_options.yaml"
            yaml_file.write_text("""
exercises:
  - id: test-001
    type: single_choice
    exam: associate
    domain: "Databricks Intelligence Platform"
    difficulty: easy
    question: "Test question?"
    explanation: "Test explanation"
    answer: [a]
""")

            exercises, error_count, error_log = load_exercises_from_directory(tmpdir)

            assert error_count == 1
            assert error_log[0].error_type == "validation_error"

    def test_empty_options_list(self):
        """Test MCQ with empty options list."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yaml_file = Path(tmpdir) / "empty_options.yaml"
            yaml_file.write_text("""
exercises:
  - id: test-001
    type: single_choice
    exam: associate
    domain: "Databricks Intelligence Platform"
    difficulty: easy
    question: "Test question?"
    explanation: "Test explanation"
    options: []
    answer: [a]
""")

            exercises, error_count, error_log = load_exercises_from_directory(tmpdir)

            assert error_count == 1
            assert error_log[0].error_type == "validation_error"

    def test_option_missing_fields(self):
        """Test option with missing required fields."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yaml_file = Path(tmpdir) / "option_missing_id.yaml"
            yaml_file.write_text("""
exercises:
  - id: test-001
    type: single_choice
    exam: associate
    domain: "Databricks Intelligence Platform"
    difficulty: easy
    question: "Test question?"
    explanation: "Test explanation"
    options:
      - text: "Option A"
        correct: true
    answer: [a]
""")

            exercises, error_count, error_log = load_exercises_from_directory(tmpdir)

            assert error_count == 1
            assert error_log[0].error_type == "validation_error"

    def test_missing_answer_field_is_derived(self):
        """A missing answer field is valid: answer is derived from correct flags."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yaml_file = Path(tmpdir) / "missing_answer.yaml"
            yaml_file.write_text("""
exercises:
  - id: test-001
    type: single_choice
    exam: associate
    domain: "Databricks Intelligence Platform"
    difficulty: easy
    question: "Test question?"
    explanation: "Test explanation"
    options:
      - id: a
        text: "Option A"
        correct: true
      - id: b
        text: "Option B"
        correct: false
      - id: c
        text: "Option C"
        correct: false
      - id: d
        text: "Option D"
        correct: false
""")

            exercises, error_count, error_log = load_exercises_from_directory(tmpdir)

            assert error_count == 0
            assert len(exercises) == 1
            assert exercises[0].answer == ["a"]

    def test_no_correct_option_errors(self):
        """An MCQ with no option marked correct is a validation error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yaml_file = Path(tmpdir) / "no_correct.yaml"
            yaml_file.write_text("""
exercises:
  - id: test-001
    type: single_choice
    exam: associate
    domain: "Databricks Intelligence Platform"
    difficulty: easy
    question: "Test question?"
    explanation: "Test explanation"
    options:
      - id: a
        text: "Option A"
        correct: false
      - id: b
        text: "Option B"
        correct: false
""")

            exercises, error_count, error_log = load_exercises_from_directory(tmpdir)

            assert error_count == 1
            assert error_log[0].error_type == "validation_error"
            assert "correct" in error_log[0].message.lower()

    def test_answer_input_ignored_uses_correct_flags(self):
        """Any author-supplied answer is ignored; answer comes from correct flags."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yaml_file = Path(tmpdir) / "answer_ignored.yaml"
            yaml_file.write_text("""
exercises:
  - id: test-001
    type: single_choice
    exam: associate
    domain: "Databricks Intelligence Platform"
    difficulty: easy
    question: "Test question?"
    explanation: "Test explanation"
    options:
      - id: a
        text: "Option A"
        correct: true
      - id: b
        text: "Option B"
        correct: false
      - id: c
        text: "Option C"
        correct: false
      - id: d
        text: "Option D"
        correct: false
    answer: [c]
""")

            exercises, error_count, error_log = load_exercises_from_directory(tmpdir)

            # Bogus answer: [c] is ignored; answer is derived as [a].
            assert error_count == 0
            assert len(exercises) == 1
            assert exercises[0].answer == ["a"]


class TestInvalidCodeCompletion:
    """Tests for invalid CodeCompletion exercises."""

    def test_missing_language_field(self):
        """Test CodeCompletion missing language field."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yaml_file = Path(tmpdir) / "missing_language.yaml"
            yaml_file.write_text("""
exercises:
  - id: test-001
    type: code_completion
    exam: associate
    domain: "Databricks Intelligence Platform"
    difficulty: easy
    question: "Complete the code"
    explanation: "Test explanation"
    template: "SELECT * FROM ___"
    answer: "table"
""")

            exercises, error_count, error_log = load_exercises_from_directory(tmpdir)

            assert error_count == 1
            assert error_log[0].error_type == "validation_error"

    def test_missing_template_field(self):
        """Test CodeCompletion missing template field."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yaml_file = Path(tmpdir) / "missing_template.yaml"
            yaml_file.write_text("""
exercises:
  - id: test-001
    type: code_completion
    exam: associate
    domain: "Databricks Intelligence Platform"
    difficulty: easy
    question: "Complete the code"
    explanation: "Test explanation"
    language: sql
    answer: "table"
""")

            exercises, error_count, error_log = load_exercises_from_directory(tmpdir)

            assert error_count == 1
            assert error_log[0].error_type == "validation_error"

    def test_missing_answer_field_code(self):
        """Test CodeCompletion missing answer field."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yaml_file = Path(tmpdir) / "missing_code_answer.yaml"
            yaml_file.write_text("""
exercises:
  - id: test-001
    type: code_completion
    exam: associate
    domain: "Databricks Intelligence Platform"
    difficulty: easy
    question: "Complete the code"
    explanation: "Test explanation"
    language: sql
    template: "SELECT * FROM ___"
""")

            exercises, error_count, error_log = load_exercises_from_directory(tmpdir)

            assert error_count == 1
            assert error_log[0].error_type == "validation_error"

    def test_template_missing_blank(self):
        """Test CodeCompletion template without blank (___) marker."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yaml_file = Path(tmpdir) / "no_blank.yaml"
            yaml_file.write_text("""
exercises:
  - id: test-001
    type: code_completion
    exam: associate
    domain: "Databricks Intelligence Platform"
    difficulty: easy
    question: "Complete the code"
    explanation: "Test explanation"
    language: sql
    template: "SELECT * FROM table"
    answer: "WHERE id = 1"
""")

            exercises, error_count, error_log = load_exercises_from_directory(tmpdir)

            assert error_count == 1
            assert error_log[0].error_type == "validation_error"
            assert "blank" in error_log[0].message.lower() or "___" in error_log[0].message

    def test_empty_code_answer(self):
        """Test CodeCompletion with empty answer."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yaml_file = Path(tmpdir) / "empty_code_answer.yaml"
            yaml_file.write_text("""
exercises:
  - id: test-001
    type: code_completion
    exam: associate
    domain: "Databricks Intelligence Platform"
    difficulty: easy
    question: "Complete the code"
    explanation: "Test explanation"
    language: sql
    template: "SELECT * FROM ___"
    answer: ""
""")

            exercises, error_count, error_log = load_exercises_from_directory(tmpdir)

            assert error_count == 1
            assert error_log[0].error_type == "validation_error"

    def test_whitespace_only_answer(self):
        """Test CodeCompletion with whitespace-only answer."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yaml_file = Path(tmpdir) / "whitespace_answer.yaml"
            yaml_file.write_text("""
exercises:
  - id: test-001
    type: code_completion
    exam: associate
    domain: "Databricks Intelligence Platform"
    difficulty: easy
    question: "Complete the code"
    explanation: "Test explanation"
    language: sql
    template: "SELECT * FROM ___"
    answer: "   "
""")

            exercises, error_count, error_log = load_exercises_from_directory(tmpdir)

            assert error_count == 1
            assert error_log[0].error_type == "validation_error"


class TestErrorLogging:
    """Tests for error logging and reporting."""

    def test_error_log_structure(self):
        """Test that error_log contains detailed error information."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yaml_file = Path(tmpdir) / "invalid.yaml"
            yaml_file.write_text("""
exercises:
  - id: test-001
    type: single_choice
    exam: bad_exam
    domain: "Databricks Intelligence Platform"
    difficulty: easy
    question: "Test?"
    explanation: "Test"
    options:
      - id: a
        text: "Option A"
        correct: true
    answer: [a]
""")

            exercises, error_count, error_log = load_exercises_from_directory(tmpdir)

            assert len(error_log) > 0
            error = error_log[0]
            assert isinstance(error, ContentValidationError)
            assert error.file_path
            assert error.error_type
            assert error.message or error.details

    def test_error_log_continues_on_multiple_errors(self):
        """Test that loader continues after errors and logs all of them."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yaml_file = Path(tmpdir) / "multi_error.yaml"
            yaml_file.write_text("""
exercises:
  - id: test-001
    type: invalid_type
    exam: associate
    domain: "Databricks Intelligence Platform"
    difficulty: easy
    question: "Test?"
    explanation: "Test"
    options:
      - id: a
        text: "Option A"
        correct: true
    answer: [a]
  - id: test-002
    type: single_choice
    exam: bad_value
    domain: "Databricks Intelligence Platform"
    difficulty: easy
    question: "Test?"
    explanation: "Test"
    options:
      - id: a
        text: "Option A"
        correct: true
    answer: [a]
""")

            exercises, error_count, error_log = load_exercises_from_directory(tmpdir)

            # Both exercises should fail
            assert error_count == 2
            assert len(error_log) == 2

    def test_valid_exercise_loads_with_other_errors(self):
        """Test that valid exercises load even when other exercises have errors."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yaml_file = Path(tmpdir) / "mixed.yaml"
            yaml_file.write_text("""
exercises:
  - id: test-001
    type: single_choice
    exam: associate
    domain: "Databricks Intelligence Platform"
    difficulty: easy
    question: "What is the Lakehouse?"
    explanation: "It combines lakes and warehouses"
    options:
      - id: a
        text: "A data architecture"
        correct: true
      - id: b
        text: "Only a data lake"
        correct: false
      - id: c
        text: "Only a data warehouse"
        correct: false
      - id: d
        text: "A BI dashboard tool"
        correct: false
    answer: [a]
  - id: test-002
    type: invalid_type
    exam: associate
    domain: "Databricks Intelligence Platform"
    difficulty: easy
    question: "Bad exercise"
    explanation: "This will fail"
    options:
      - id: a
        text: "Option A"
        correct: true
    answer: [a]
  - id: test-003
    type: code_completion
    exam: associate
    domain: "Databricks Intelligence Platform"
    difficulty: medium
    question: "Complete this SQL"
    explanation: "Fill in the blank"
    language: sql
    template: "SELECT * FROM ___"
    answer: "users"
""")

            exercises, error_count, error_log = load_exercises_from_directory(tmpdir)

            # Should load 2 valid exercises
            assert len(exercises) == 2
            # Should have 1 error
            assert error_count == 1
            assert len(error_log) == 1
            # Valid exercises should have correct IDs
            loaded_ids = {e.id for e in exercises}
            assert "test-001" in loaded_ids
            assert "test-003" in loaded_ids
            assert "test-002" not in loaded_ids


class TestValidExercises:
    """Tests for successfully loading valid exercises."""

    def test_valid_mcq_exercise(self):
        """Test successfully loading a valid MCQ exercise."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yaml_file = Path(tmpdir) / "valid_mcq.yaml"
            yaml_file.write_text("""
exercises:
  - id: test-001
    type: single_choice
    exam: associate
    domain: "Databricks Intelligence Platform"
    difficulty: easy
    question: "What is the Lakehouse?"
    explanation: "It combines lakes and warehouses"
    options:
      - id: a
        text: "A data architecture"
        correct: true
      - id: b
        text: "Only a data lake"
        correct: false
      - id: c
        text: "Only a data warehouse"
        correct: false
      - id: d
        text: "A proprietary file format"
        correct: false
    answer: [a]
""")

            exercises, error_count, error_log = load_exercises_from_directory(tmpdir)

            assert error_count == 0
            assert len(exercises) == 1
            assert exercises[0].id == "test-001"
            assert exercises[0].type.value == "single_choice"

    def test_valid_code_completion_exercise(self):
        """Test successfully loading a valid CodeCompletion exercise."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yaml_file = Path(tmpdir) / "valid_code.yaml"
            yaml_file.write_text("""
exercises:
  - id: test-001
    type: code_completion
    exam: associate
    domain: "Databricks Intelligence Platform"
    difficulty: medium
    question: "Complete this SQL query"
    explanation: "Use the users table"
    language: sql
    template: "SELECT * FROM ___"
    answer: "users"
    accepted: ["users_table", "User"]
""")

            exercises, error_count, error_log = load_exercises_from_directory(tmpdir)

            assert error_count == 0
            assert len(exercises) == 1
            assert exercises[0].id == "test-001"
            assert exercises[0].type.value == "code_completion"

    def test_multi_choice_rejected(self):
        """multi_choice is removed (PRD rev 2): loading one is a validation error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yaml_file = Path(tmpdir) / "multi_choice.yaml"
            yaml_file.write_text("""
exercises:
  - id: test-001
    type: multi_choice
    exam: associate
    domain: "Databricks Intelligence Platform"
    difficulty: hard
    question: "Which are benefits of Lakehouse? (select all)"
    explanation: "All are true"
    options:
      - id: a
        text: "Cost efficient"
        correct: true
      - id: b
        text: "Reliable"
        correct: true
      - id: c
        text: "Flexible"
        correct: true
      - id: d
        text: "No schema needed"
        correct: false
    answer: [a, b, c]
""")

            exercises, error_count, error_log = load_exercises_from_directory(tmpdir)

            # multi_choice is no longer a supported type.
            assert error_count == 1
            assert len(exercises) == 0
            assert error_log[0].error_type in ("validation_error", "unknown_type")
