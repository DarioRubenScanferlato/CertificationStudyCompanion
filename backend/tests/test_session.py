"""Tests for the server-side session randomizer (Story 5.3, Story 7.3)."""

import pytest

from app import store
from app.models import MCQ, Difficulty, Domain, ExamType, ExerciseType, Option
from app.session import (
    build_displayed_options,
    build_session,
    build_session_entry,
)


@pytest.fixture(autouse=True)
def temp_attempt_db(tmp_path, monkeypatch):
    """Point the attempt store at a fresh temp DB for every test.

    ``build_session`` reads the store for unseen-first ordering (Story 7.3), so
    every test must use an isolated, empty DB (no rows => everything unseen)
    unless it records attempts itself. ``ATTEMPT_DB_PATH`` is honored by all
    store helpers (see store._resolve_path).
    """
    db_path = tmp_path / "progress.db"
    monkeypatch.setenv("ATTEMPT_DB_PATH", str(db_path))
    store.init_db()
    return db_path


def make_mcq(
    exercise_id: str = "dbx-de-0001",
    *,
    extra_correct: bool = False,
    extra_incorrect: bool = False,
) -> MCQ:
    """Build a valid Option Pool MCQ for testing.

    By default: 1 correct + 3 incorrect. ``extra_correct`` adds a second correct
    alternative; ``extra_incorrect`` adds extra distractors so the pool is
    larger than 4 (forces real sampling).
    """
    options = [
        Option(id="a", text="Correct A", correct=True),
        Option(id="b", text="Wrong B", correct=False),
        Option(id="c", text="Wrong C", correct=False),
        Option(id="d", text="Wrong D", correct=False),
    ]
    if extra_correct:
        options.append(Option(id="e", text="Correct E", correct=True))
    if extra_incorrect:
        options.append(Option(id="f", text="Wrong F", correct=False))
        options.append(Option(id="g", text="Wrong G", correct=False))

    return MCQ(
        id=exercise_id,
        type=ExerciseType.SINGLE_CHOICE,
        exam=ExamType.ASSOCIATE,
        domain=Domain.INTELLIGENCE_PLATFORM,
        difficulty=Difficulty.EASY,
        question=f"Question for {exercise_id}?",
        options=options,
        explanation="Because.",
    )


class TestBuildDisplayedOptions:
    """Tests for build_displayed_options."""

    def test_returns_exactly_four_options(self):
        displayed = build_displayed_options(make_mcq(extra_incorrect=True))
        assert len(displayed) == 4

    def test_no_correct_key_leaked(self):
        """Displayed options must NOT carry the `correct` flag."""
        for _ in range(50):
            displayed = build_displayed_options(make_mcq(extra_incorrect=True))
            for opt in displayed:
                assert "correct" not in opt
                assert set(opt.keys()) == {"id", "text"}

    def test_exactly_one_correct_three_incorrect(self):
        """Exactly 1 correct + 3 incorrect across the 4 displayed options."""
        mcq = make_mcq(extra_incorrect=True)
        correct_ids = {o.id for o in mcq.options if o.correct}
        incorrect_ids = {o.id for o in mcq.options if not o.correct}

        for _ in range(200):
            displayed = build_displayed_options(mcq)
            shown_ids = [o["id"] for o in displayed]
            n_correct = sum(1 for i in shown_ids if i in correct_ids)
            n_incorrect = sum(1 for i in shown_ids if i in incorrect_ids)
            assert n_correct == 1
            assert n_incorrect == 3

    def test_displayed_ids_are_subset_of_pool_ids(self):
        mcq = make_mcq(extra_incorrect=True)
        pool_ids = {o.id for o in mcq.options}
        for _ in range(100):
            displayed = build_displayed_options(mcq)
            shown_ids = [o["id"] for o in displayed]
            # ids preserved (never renumbered) and a subset of the pool.
            assert set(shown_ids).issubset(pool_ids)
            # No duplicate ids within a single display.
            assert len(shown_ids) == len(set(shown_ids))

    def test_text_matches_original_id(self):
        """A displayed id must carry its original authored text."""
        mcq = make_mcq(extra_incorrect=True)
        id_to_text = {o.id: o.text for o in mcq.options}
        for _ in range(50):
            for opt in build_displayed_options(mcq):
                assert opt["text"] == id_to_text[opt["id"]]

    def test_order_varies_across_calls(self):
        """Repeated calls vary in order and/or selection (uniform random)."""
        mcq = make_mcq(extra_incorrect=True)
        observed = set()
        for _ in range(200):
            displayed = build_displayed_options(mcq)
            observed.add(tuple(o["id"] for o in displayed))
        # With sampling from a 6-option pool + shuffling, many distinct
        # outcomes are expected over 200 iterations.
        assert len(observed) > 1

    def test_extra_correct_alternative_still_one_correct(self):
        """A pool with extra correct alternatives still shows exactly 1 correct."""
        mcq = make_mcq(extra_correct=True)
        correct_ids = {o.id for o in mcq.options if o.correct}
        assert len(correct_ids) == 2  # sanity: pool really has 2 correct

        seen_correct = set()
        for _ in range(200):
            displayed = build_displayed_options(mcq)
            shown_correct = [o["id"] for o in displayed if o["id"] in correct_ids]
            assert len(shown_correct) == 1
            seen_correct.update(shown_correct)
        # Over many iterations both correct alternatives should appear,
        # confirming uniform sampling of the correct option.
        assert seen_correct == correct_ids


class TestBuildSessionEntry:
    """Tests for build_session_entry."""

    def test_entry_shape(self):
        mcq = make_mcq()
        entry = build_session_entry(mcq)
        assert entry["exerciseId"] == mcq.id
        assert entry["type"] == "single_choice"
        assert entry["domain"] == Domain.INTELLIGENCE_PLATFORM.value
        assert entry["difficulty"] == Difficulty.EASY.value
        assert entry["question"] == mcq.question
        assert entry["codeContext"] is None
        assert len(entry["displayedOptions"]) == 4
        for opt in entry["displayedOptions"]:
            assert set(opt.keys()) == {"id", "text"}


class TestBuildSession:
    """Tests for build_session."""

    def test_returns_entry_per_mcq(self):
        exercises = [make_mcq(f"dbx-de-{i:04d}") for i in range(5)]
        session = build_session(exercises)
        assert len(session) == 5
        ids = {e["exerciseId"] for e in session}
        assert ids == {ex.id for ex in exercises}

    def test_order_is_randomized_over_many_iterations(self):
        exercises = [make_mcq(f"dbx-de-{i:04d}") for i in range(6)]
        observed = set()
        for _ in range(200):
            session = build_session(exercises)
            observed.add(tuple(e["exerciseId"] for e in session))
        # With 6 exercises there are 720 permutations; over 200 runs we expect
        # many distinct orderings.
        assert len(observed) > 1

    def test_does_not_mutate_input(self):
        exercises = [make_mcq(f"dbx-de-{i:04d}") for i in range(5)]
        original_order = [ex.id for ex in exercises]
        build_session(exercises)
        assert [ex.id for ex in exercises] == original_order

    def test_each_mcq_carries_displayed_options(self):
        exercises = [make_mcq(f"dbx-de-{i:04d}", extra_incorrect=True) for i in range(3)]
        session = build_session(exercises)
        for entry in session:
            assert len(entry["displayedOptions"]) == 4
            for opt in entry["displayedOptions"]:
                assert "correct" not in opt


class TestUnseenFirstOrdering:
    """Tests for unseen-first session ordering (Story 7.3, FR-24)."""

    def test_unseen_served_before_any_seen(self):
        """All unseen exercises are ordered before any seen one."""
        exercises = [make_mcq(f"dbx-de-{i:04d}") for i in range(6)]
        seen_ids = {"dbx-de-0001", "dbx-de-0003", "dbx-de-0004"}
        for eid in seen_ids:
            store.record_attempt(eid, answered_at="2026-01-01T00:00:00+00:00")

        unseen_ids = {ex.id for ex in exercises} - seen_ids

        # Run repeatedly: the unseen-group is shuffled, so the partition
        # boundary must hold regardless of the random within-group order.
        for _ in range(50):
            session = build_session(exercises)
            ordered_ids = [e["exerciseId"] for e in session]
            # All exercises still returned (no drops).
            assert set(ordered_ids) == {ex.id for ex in exercises}
            # The first len(unseen) entries are exactly the unseen set, and the
            # remainder are exactly the seen set => every unseen precedes every seen.
            head = set(ordered_ids[: len(unseen_ids)])
            tail = ordered_ids[len(unseen_ids) :]
            assert head == unseen_ids
            assert set(tail) == seen_ids

    def test_unseen_group_order_is_randomized(self):
        """Within the unseen group, order varies across calls."""
        exercises = [make_mcq(f"dbx-de-{i:04d}") for i in range(6)]
        # Nothing attempted => all unseen.
        observed = set()
        for _ in range(200):
            session = build_session(exercises)
            observed.add(tuple(e["exerciseId"] for e in session))
        assert len(observed) > 1

    def test_all_seen_fallback_least_recently_seen_first(self):
        """When everything is seen, all are returned, oldest-last-seen first."""
        exercises = [make_mcq(f"dbx-de-{i:04d}") for i in range(4)]
        # Record attempts with strictly increasing timestamps so last-seen order
        # is unambiguous: 0000 oldest ... 0003 most recent.
        timestamps = {
            "dbx-de-0000": "2026-01-01T00:00:00+00:00",
            "dbx-de-0001": "2026-02-01T00:00:00+00:00",
            "dbx-de-0002": "2026-03-01T00:00:00+00:00",
            "dbx-de-0003": "2026-04-01T00:00:00+00:00",
        }
        for eid, ts in timestamps.items():
            store.record_attempt(eid, answered_at=ts)

        # Deterministic when all-seen: no unseen group to shuffle.
        session = build_session(exercises)
        ordered_ids = [e["exerciseId"] for e in session]

        # No empty/blocked state: every exercise is still present.
        assert set(ordered_ids) == set(timestamps)
        # Least-recently-seen first: oldest timestamp leads, most-recent trails.
        assert ordered_ids == [
            "dbx-de-0000",
            "dbx-de-0001",
            "dbx-de-0002",
            "dbx-de-0003",
        ]
        # Spot-check the load-bearing invariant: oldest before most-recent.
        assert ordered_ids.index("dbx-de-0000") < ordered_ids.index("dbx-de-0003")

    def test_last_seen_uses_most_recent_attempt(self):
        """An exercise's position uses its MOST RECENT attempt timestamp."""
        exercises = [make_mcq("dbx-de-0000"), make_mcq("dbx-de-0001")]
        # 0000: first attempt old, then a very recent re-attempt.
        store.record_attempt("dbx-de-0000", answered_at="2026-01-01T00:00:00+00:00")
        store.record_attempt("dbx-de-0000", answered_at="2026-05-01T00:00:00+00:00")
        # 0001: single attempt, between the two above.
        store.record_attempt("dbx-de-0001", answered_at="2026-03-01T00:00:00+00:00")

        session = build_session(exercises)
        ordered_ids = [e["exerciseId"] for e in session]
        # 0001 (last seen 2026-03) is less recent than 0000 (last seen 2026-05),
        # so 0001 comes first.
        assert ordered_ids == ["dbx-de-0001", "dbx-de-0000"]

    def test_prioritize_unseen_false_is_history_independent(self):
        """prioritize_unseen=False keeps the prior pure-random ordering."""
        exercises = [make_mcq(f"dbx-de-{i:04d}") for i in range(6)]
        # Mark a subset seen; it must NOT affect ordering when the flag is off.
        for eid in ("dbx-de-0001", "dbx-de-0003"):
            store.record_attempt(eid, answered_at="2026-01-01T00:00:00+00:00")

        observed = set()
        boundary_violations = 0
        seen_ids = {"dbx-de-0001", "dbx-de-0003"}
        for _ in range(200):
            session = build_session(exercises, prioritize_unseen=False)
            ordered_ids = [e["exerciseId"] for e in session]
            assert set(ordered_ids) == {ex.id for ex in exercises}
            observed.add(tuple(ordered_ids))
            # Count runs where a seen id lands before some unseen id — under
            # history-independent random ordering this should frequently happen.
            first_seen_pos = min(ordered_ids.index(s) for s in seen_ids)
            last_unseen_pos = max(ordered_ids.index(i) for i in ordered_ids if i not in seen_ids)
            if first_seen_pos < last_unseen_pos:
                boundary_violations += 1

        # Random ordering => many distinct permutations...
        assert len(observed) > 1
        # ...and history is ignored: seen ids routinely appear before unseen ones
        # (unseen-first would make boundary_violations == 0).
        assert boundary_violations > 0

    def test_option_sampling_still_random_under_unseen_first(self):
        """Per-MCQ sampling stays random: exactly 1 correct + 3 incorrect, varies."""
        exercises = [make_mcq("dbx-de-0000", extra_incorrect=True)]
        mcq = exercises[0]
        correct_ids = {o.id for o in mcq.options if o.correct}
        incorrect_ids = {o.id for o in mcq.options if not o.correct}

        observed = set()
        for _ in range(200):
            session = build_session(exercises)
            assert len(session) == 1
            displayed = session[0]["displayedOptions"]
            shown_ids = [o["id"] for o in displayed]
            assert sum(1 for i in shown_ids if i in correct_ids) == 1
            assert sum(1 for i in shown_ids if i in incorrect_ids) == 3
            for opt in displayed:
                assert set(opt.keys()) == {"id", "text"}
            observed.add(tuple(shown_ids))
        # Sampling from a 6-option pool + shuffle => many distinct outcomes.
        assert len(observed) > 1


class TestSeenFlag:
    """Tests for the per-entry ``seen`` flag (Story 7.6).

    Each session entry carries ``seen``: ``True`` when the exercise has >=1
    recorded attempt in the store, ``False`` otherwise. The flag is derived from
    the same ``store.attempted_ids()`` signal that drives unseen-first ordering,
    and is stamped regardless of the ``prioritize_unseen`` flag.
    """

    def test_seen_true_for_attempted_false_for_unattempted(self):
        exercises = [make_mcq(f"dbx-de-{i:04d}") for i in range(4)]
        store.record_attempt("dbx-de-0001", answered_at="2026-01-01T00:00:00+00:00")
        store.record_attempt("dbx-de-0003", answered_at="2026-01-01T00:00:00+00:00")

        session = build_session(exercises)
        seen_by_id = {e["exerciseId"]: e["seen"] for e in session}

        assert seen_by_id["dbx-de-0001"] is True
        assert seen_by_id["dbx-de-0003"] is True
        assert seen_by_id["dbx-de-0000"] is False
        assert seen_by_id["dbx-de-0002"] is False

    def test_seen_false_when_no_history(self):
        exercises = [make_mcq(f"dbx-de-{i:04d}") for i in range(3)]
        session = build_session(exercises)
        assert all(e["seen"] is False for e in session)
        # Every entry carries the key (never absent).
        assert all("seen" in e for e in session)

    def test_seen_stamped_when_prioritize_unseen_false(self):
        """The replay path (POST /api/sessions) also carries correct seen flags."""
        exercises = [make_mcq(f"dbx-de-{i:04d}") for i in range(3)]
        store.record_attempt("dbx-de-0002", answered_at="2026-01-01T00:00:00+00:00")

        session = build_session(exercises, prioritize_unseen=False)
        seen_by_id = {e["exerciseId"]: e["seen"] for e in session}

        assert seen_by_id["dbx-de-0002"] is True
        assert seen_by_id["dbx-de-0000"] is False
        assert seen_by_id["dbx-de-0001"] is False
