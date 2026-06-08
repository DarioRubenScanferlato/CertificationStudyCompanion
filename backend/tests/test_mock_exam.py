"""Tests for the Mock-Exam builder (Story 8.3, FR-27).

Covers the pure builder/weighting helpers (deterministic, synthetic corpus) and
the GET /api/sessions?mode=mock endpoint (sizing, duration stamping, exam
scoping, no unseen-first, leak-free, graceful short corpus).
"""

from collections import Counter

from app import store
from app.models import MCQ, Domain, ExamType
from app.session import (
    MOCK_EXAM_CONFIGS,
    _largest_remainder_targets,
    build_mock_session,
)


def _mcq(exercise_id: str, domain: Domain, exam: ExamType = ExamType.ASSOCIATE) -> MCQ:
    return MCQ(
        id=exercise_id,
        type="single_choice",
        exam=exam,
        domain=domain,
        difficulty="medium",
        question=f"Q {exercise_id}?",
        options=[
            {"id": "a", "text": "correct", "correct": True},
            {"id": "b", "text": "w1", "correct": False},
            {"id": "c", "text": "w2", "correct": False},
            {"id": "d", "text": "w3", "correct": False},
        ],
        explanation="because.",
    )


def _corpus(exam: ExamType, per_domain: int) -> list[MCQ]:
    """Build `per_domain` MCQs for every domain in the exam's mock config."""
    out: list[MCQ] = []
    for domain in MOCK_EXAM_CONFIGS[exam].domain_weights:
        for i in range(per_domain):
            out.append(_mcq(f"{exam.value}-{domain.name}-{i}", domain, exam))
    return out


class TestLargestRemainder:
    def test_sums_to_total_associate(self):
        cfg = MOCK_EXAM_CONFIGS[ExamType.ASSOCIATE]
        targets = _largest_remainder_targets(cfg.domain_weights, cfg.total_questions)
        assert sum(targets.values()) == cfg.total_questions == 45
        assert all(t >= 0 for t in targets.values())

    def test_sums_to_total_professional(self):
        cfg = MOCK_EXAM_CONFIGS[ExamType.PROFESSIONAL]
        targets = _largest_remainder_targets(cfg.domain_weights, cfg.total_questions)
        assert sum(targets.values()) == cfg.total_questions == 59

    def test_higher_weight_gets_more(self):
        cfg = MOCK_EXAM_CONFIGS[ExamType.ASSOCIATE]
        targets = _largest_remainder_targets(cfg.domain_weights, cfg.total_questions)
        # Data Transformation and Modeling (22%) > Databricks Intelligence Platform (6%)
        assert targets[Domain.DATA_TRANSFORMATION_MODELING] > targets[Domain.INTELLIGENCE_PLATFORM]


class TestBuildMockSession:
    def test_full_length_when_corpus_is_ample(self):
        corpus = _corpus(ExamType.ASSOCIATE, per_domain=50)
        session = build_mock_session(corpus, exam=ExamType.ASSOCIATE)
        assert len(session) == 45  # exactly the exam total

    def test_per_domain_counts_match_weight_targets(self):
        cfg = MOCK_EXAM_CONFIGS[ExamType.ASSOCIATE]
        targets = _largest_remainder_targets(cfg.domain_weights, cfg.total_questions)
        corpus = _corpus(ExamType.ASSOCIATE, per_domain=50)
        session = build_mock_session(corpus, exam=ExamType.ASSOCIATE)
        counts = Counter(e["domain"] for e in session)
        for domain, target in targets.items():
            assert counts[domain.value] == target

    def test_each_entry_four_flagless_options(self):
        corpus = _corpus(ExamType.PROFESSIONAL, per_domain=50)
        session = build_mock_session(corpus, exam=ExamType.PROFESSIONAL)
        assert len(session) == 59
        for entry in session:
            assert len(entry["displayedOptions"]) == 4
            for opt in entry["displayedOptions"]:
                assert set(opt.keys()) == {"id", "text"}  # no `correct`

    def test_short_corpus_caps_per_domain_no_crash(self):
        # Only 1 MCQ per domain -> session capped at (num domains), not total.
        corpus = _corpus(ExamType.ASSOCIATE, per_domain=1)
        session = build_mock_session(corpus, exam=ExamType.ASSOCIATE)
        assert len(session) == len(MOCK_EXAM_CONFIGS[ExamType.ASSOCIATE].domain_weights)

    def test_does_not_consult_attempt_store(self, tmp_path, monkeypatch):
        # Record attempts for everything; mock must still return the full set
        # (unseen-first is NOT applied to mock).
        monkeypatch.setenv("ATTEMPT_DB_PATH", str(tmp_path / "m.db"))
        store.init_db()
        corpus = _corpus(ExamType.ASSOCIATE, per_domain=50)
        for mcq in corpus:
            store.record_attempt(mcq.id, exam=mcq.exam.value, domain=mcq.domain.value, correct=True)
        session = build_mock_session(corpus, exam=ExamType.ASSOCIATE)
        assert len(session) == 45


class TestMockEndpoint:
    def test_associate_mock_stamps_duration_90(self, client):
        resp = client.get("/api/sessions?mode=mock&exam=associate")
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert body["durationMinutes"] == 90
        assert isinstance(body["data"], list) and len(body["data"]) > 0
        # exam-scoping: only the 7 Associate sections appear
        assoc = {d.value for d in MOCK_EXAM_CONFIGS[ExamType.ASSOCIATE].domain_weights}
        assert all(e["domain"] in assoc for e in body["data"])
        # leak-free
        for e in body["data"]:
            for opt in e["displayedOptions"]:
                assert "correct" not in opt

    def test_professional_mock_stamps_duration_120(self, client):
        resp = client.get("/api/sessions?mode=mock&exam=professional")
        body = resp.json()
        assert body["success"] is True
        assert body["durationMinutes"] == 120
        pro = {d.value for d in MOCK_EXAM_CONFIGS[ExamType.PROFESSIONAL].domain_weights}
        assert all(e["domain"] in pro for e in body["data"])

    def test_mock_requires_exam(self, client):
        resp = client.get("/api/sessions?mode=mock")
        body = resp.json()
        assert body["success"] is False
        assert "exam" in body["error"].lower()

    def test_non_mock_mode_is_normal_session(self, client):
        # An unrecognized/absent mode behaves like the normal runner (no duration).
        resp = client.get("/api/sessions?exam=associate")
        body = resp.json()
        assert body["success"] is True
        assert "durationMinutes" not in body
