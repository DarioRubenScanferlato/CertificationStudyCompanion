"""Tests for the sidecar feedback store (Story 11.1, FR-32 / AR-21)."""

import pytest
import yaml

from app import feedback_store


@pytest.fixture
def fb_path(tmp_path):
    # Dedicated subdir so the "sole artifact" assertion isn't polluted by other
    # fixtures' tmp files (e.g. the SQLite store's test progress.db).
    return tmp_path / "content" / "feedback.yaml"


class TestAddNote:
    def test_creates_file_and_records_entry(self, fb_path):
        assert not fb_path.exists()
        entry = feedback_store.add_note("dbx-de-0142", "Option b and d are the same.", path=fb_path)
        assert fb_path.exists()
        assert entry["note"] == "Option b and d are the same."
        assert entry["resolved"] is False
        assert entry["created_at"].endswith("Z")  # ISO 8601 UTC

    def test_appends_multiple_notes_for_same_exercise(self, fb_path):
        feedback_store.add_note("q1", "first", path=fb_path)
        feedback_store.add_note("q1", "second", path=fb_path)
        notes = feedback_store.notes_for("q1", path=fb_path)
        assert [n["note"] for n in notes] == ["first", "second"]

    def test_trims_whitespace(self, fb_path):
        entry = feedback_store.add_note("q1", "  spaced  ", path=fb_path)
        assert entry["note"] == "spaced"

    def test_rejects_empty_or_whitespace_note(self, fb_path):
        for bad in ("", "   ", "\n\t"):
            with pytest.raises(ValueError):
                feedback_store.add_note("q1", bad, path=fb_path)
        # Nothing written.
        assert not fb_path.exists()

    def test_does_not_touch_a_preexisting_sibling_file(self, fb_path):
        # FR-32 guarantee: writing feedback never modifies authored content files.
        # Simulate an authored file beside the sidecar and assert it's byte-unchanged.
        fb_path.parent.mkdir(parents=True, exist_ok=True)
        sibling = fb_path.parent / "exercise.yaml"
        original = "exercises:\n  - id: q1\n    question: keep me\n"
        sibling.write_text(original)
        feedback_store.add_note("q1", "note", path=fb_path)
        assert sibling.read_text() == original  # authored file untouched
        assert fb_path.exists()  # only the sidecar was written


class TestQueries:
    def test_notes_for_unknown_exercise_is_empty(self, fb_path):
        assert feedback_store.notes_for("nope", path=fb_path) == []

    def test_open_notes_filters_resolved(self, fb_path):
        feedback_store.add_note("q1", "open one", path=fb_path)
        feedback_store.add_note("q2", "will resolve", path=fb_path)
        feedback_store.mark_resolved("q2", path=fb_path)
        opened = feedback_store.open_notes(path=fb_path)
        assert "q1" in opened
        assert "q2" not in opened  # fully resolved -> excluded

    def test_open_notes_includes_partially_unresolved(self, fb_path):
        feedback_store.add_note("q1", "a", path=fb_path)
        feedback_store.mark_resolved("q1", path=fb_path)
        feedback_store.add_note("q1", "b (new, open)", path=fb_path)
        opened = feedback_store.open_notes(path=fb_path)
        assert "q1" in opened
        assert [n["note"] for n in opened["q1"]] == ["b (new, open)"]


class TestMarkResolved:
    def test_marks_all_open_and_returns_count(self, fb_path):
        feedback_store.add_note("q1", "a", path=fb_path)
        feedback_store.add_note("q1", "b", path=fb_path)
        changed = feedback_store.mark_resolved("q1", path=fb_path)
        assert changed == 2
        assert all(n["resolved"] for n in feedback_store.notes_for("q1", path=fb_path))
        # Idempotent: re-resolving changes nothing.
        assert feedback_store.mark_resolved("q1", path=fb_path) == 0

    def test_persists_resolution_to_disk(self, fb_path):
        feedback_store.add_note("q1", "a", path=fb_path)
        feedback_store.mark_resolved("q1", path=fb_path)
        on_disk = yaml.safe_load(fb_path.read_text())
        assert on_disk["q1"][0]["resolved"] is True


class TestRobustness:
    """Code-review hardening (2026-06-10): corrupt/malformed sidecar + atomic write."""

    def test_corrupt_yaml_raises_clear_error_without_clobbering(self, fb_path):
        fb_path.parent.mkdir(parents=True, exist_ok=True)
        fb_path.write_text("{ this is: not: valid yaml: [")
        for call in (
            lambda: feedback_store.notes_for("q1", path=fb_path),
            lambda: feedback_store.open_notes(path=fb_path),
            lambda: feedback_store.mark_resolved("q1", path=fb_path),
            lambda: feedback_store.add_note("q1", "note", path=fb_path),
        ):
            with pytest.raises(feedback_store.FeedbackStoreError):
                call()
        # add_note must NOT have overwritten the (recoverable) corrupt file.
        assert fb_path.read_text() == "{ this is: not: valid yaml: ["

    def test_malformed_values_do_not_crash(self, fb_path):
        fb_path.parent.mkdir(parents=True, exist_ok=True)
        fb_path.write_text(
            "q1: just a string\n"
            "q2: null\n"
            "q3:\n"
            "  - 42\n"  # non-dict entry mixed with a real one
            "  - note: real\n"
            "    resolved: false\n"
        )
        assert feedback_store.notes_for("q1", path=fb_path) == []  # scalar -> []
        assert feedback_store.notes_for("q2", path=fb_path) == []  # null -> []
        opened = feedback_store.open_notes(path=fb_path)
        assert [n["note"] for n in opened["q3"]] == ["real"]  # non-dict skipped
        assert feedback_store.mark_resolved("q1", path=fb_path) == 0  # scalar -> no-op
        assert feedback_store.mark_resolved("q3", path=fb_path) == 1  # only the real entry

    def test_rejects_overlong_note(self, fb_path):
        too_long = "x" * (feedback_store.MAX_NOTE_LENGTH + 1)
        with pytest.raises(ValueError):
            feedback_store.add_note("q1", too_long, path=fb_path)
        assert not fb_path.exists()

    def test_save_leaves_no_temp_files(self, fb_path):
        feedback_store.add_note("q1", "note", path=fb_path)
        leftovers = [p.name for p in fb_path.parent.iterdir() if p.name != "feedback.yaml"]
        assert leftovers == []
