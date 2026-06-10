"""Tests for Code-Completion session delivery (Story 4.1, FR-13).

The session builder previously SKIPPED code-completion exercises; Story 4.1
makes ``build_session`` emit a code-completion session entry (flag-less, no
``displayedOptions``, carrying template/answer/accepted/language so the client
can grade locally — FR-14 is client-side). ``build_mock_session`` stays
MCQ-only by design.
"""

import pytest

from app import store
from app.models import MCQ, CodeCompletion, Difficulty, Domain, ExamType, ExerciseType, Option
from app.session import (
    build_code_completion_entry,
    build_mock_session,
    build_session,
)


@pytest.fixture(autouse=True)
def temp_attempt_db(tmp_path, monkeypatch):
    """Fresh, empty attempt store per test (unseen-first ordering determinism)."""
    monkeypatch.setenv("ATTEMPT_DB_PATH", str(tmp_path / "progress.db"))
    store.init_db()
    return tmp_path


def make_mcq(exercise_id: str = "dbx-de-0001") -> MCQ:
    return MCQ(
        id=exercise_id,
        type=ExerciseType.SINGLE_CHOICE,
        exam=ExamType.ASSOCIATE,
        domain=Domain.DATA_INGESTION_LOADING,
        difficulty=Difficulty.MEDIUM,
        question="What is Auto Loader?",
        options=[
            Option(id="a", text="Correct A", correct=True),
            Option(id="b", text="Wrong B", correct=False),
            Option(id="c", text="Wrong C", correct=False),
            Option(id="d", text="Wrong D", correct=False),
        ],
        explanation="because.",
    )


def make_code_completion(exercise_id: str = "dbx-de-0148") -> CodeCompletion:
    return CodeCompletion(
        id=exercise_id,
        type=ExerciseType.CODE_COMPLETION,
        exam=ExamType.ASSOCIATE,
        domain=Domain.DATA_INGESTION_LOADING,
        difficulty=Difficulty.MEDIUM,
        question="Configure Auto Loader to infer schema",
        language="python",
        template='spark.readStream.format("cloudFiles").option("cloudFiles.___", "json")',
        answer="format",
        accepted=["format", "Format"],
        case_sensitive=True,
        ignore_whitespace=True,
        explanation="cloudFiles.format sets the source format.",
        references=["https://docs.databricks.com/en/ingestion/auto-loader/"],
    )


class TestCodeCompletionEntry:
    def test_entry_shape_has_template_answer_no_displayed_options(self):
        cc = make_code_completion()
        entry = build_code_completion_entry(cc)
        assert entry["exerciseId"] == cc.id
        assert entry["type"] == "code_completion"
        assert entry["domain"] == cc.domain.value
        assert entry["difficulty"] == cc.difficulty.value
        assert entry["language"] == "python"
        assert entry["prompt"] == cc.question
        assert entry["template"] == cc.template
        assert entry["answer"] == "format"
        assert entry["accepted"] == ["format", "Format"]
        assert entry["caseSensitive"] is True
        assert entry["ignoreWhitespace"] is True
        assert entry["explanation"] == cc.explanation
        assert entry["references"] == cc.references
        # Code-completion entries have NO MCQ-shaped options.
        assert "displayedOptions" not in entry


class TestBuildSessionMixedTypes:
    def test_build_session_includes_code_completion(self):
        cc = make_code_completion()
        session = build_session([cc])
        assert len(session) == 1
        assert session[0]["type"] == "code_completion"
        assert session[0]["exerciseId"] == cc.id

    def test_build_session_mixes_mcq_and_code_completion(self):
        mcq = make_mcq("dbx-de-0001")
        cc = make_code_completion("dbx-de-0148")
        session = build_session([mcq, cc])
        by_id = {e["exerciseId"]: e for e in session}
        assert len(session) == 2
        # MCQ entry keeps its 4 flag-less displayed options.
        assert by_id["dbx-de-0001"]["type"] == "single_choice"
        assert len(by_id["dbx-de-0001"]["displayedOptions"]) == 4
        for opt in by_id["dbx-de-0001"]["displayedOptions"]:
            assert set(opt.keys()) == {"id", "text"}
        # Code-completion entry is delivered alongside it.
        assert by_id["dbx-de-0148"]["type"] == "code_completion"
        assert "displayedOptions" not in by_id["dbx-de-0148"]

    def test_code_completion_never_leaks_correct_flags_in_mcq_shape(self):
        # The code-completion answer IS delivered (client-side feedback), but it
        # is an explicit `answer` field, never an MCQ `correct`-flagged option.
        cc = make_code_completion()
        entry = build_session([cc])[0]
        assert "options" not in entry
        assert "displayedOptions" not in entry
        assert entry["answer"] == "format"


class TestMockSessionStaysMcqOnly:
    def test_mock_session_excludes_code_completion(self):
        # A corpus of only code-completion items yields an empty mock (MCQ-only).
        ccs = [make_code_completion(f"dbx-de-020{i}") for i in range(3)]
        session = build_mock_session(ccs, exam=ExamType.ASSOCIATE)
        assert session == []


class TestEndpointDeliversCodeCompletion:
    def test_get_sessions_returns_code_completion_when_present(self, client, monkeypatch):
        from app.main import app

        mcq = make_mcq("dbx-de-0001")
        cc = make_code_completion("dbx-de-0148")
        monkeypatch.setattr(app.state, "exercises", [mcq, cc])

        resp = client.get("/api/sessions?exam=associate")
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        types = {e["type"] for e in body["data"]}
        assert "code_completion" in types
        cc_entry = next(e for e in body["data"] if e["type"] == "code_completion")
        # Leak model: the answer rides along (client-side feedback), but no
        # MCQ-style flag-less option list is present.
        assert "displayedOptions" not in cc_entry
        assert cc_entry["answer"] == "format"
        assert cc_entry["template"].count("___") == 1
