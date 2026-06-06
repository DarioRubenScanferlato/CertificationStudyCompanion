"""Tests for the server-side session randomizer (Story 5.3)."""

from app.models import MCQ, Difficulty, Domain, ExamType, ExerciseType, Option
from app.session import (
    build_displayed_options,
    build_session,
    build_session_entry,
)


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
        domain=Domain.LAKEHOUSE_PLATFORM,
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
        assert entry["domain"] == Domain.LAKEHOUSE_PLATFORM.value
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
