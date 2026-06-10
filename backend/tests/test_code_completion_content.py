"""Content-validation tests for the Code-Completion bank (Story 4.6).

Loads the REAL exercise corpus and asserts the authored code-completion content
satisfies the CodeCompletion model invariants, mirroring the MCQ content checks.
"""

import re

from app.content import load_exercises_from_directory
from app.models import CodeCompletion, Domain

VALID_LANGUAGES = {"sql", "pyspark", "python"}


def _load():
    return load_exercises_from_directory()


class TestCodeCompletionContent:
    def test_corpus_loads_without_errors(self):
        _exercises, error_count, error_log = _load()
        assert error_count == 0, f"content load errors: {[str(e) for e in error_log]}"

    def test_no_duplicate_ids_across_corpus(self):
        exercises, _, _ = _load()
        ids = [e.id for e in exercises]
        dups = sorted({i for i in ids if ids.count(i) > 1})
        assert dups == [], f"duplicate exercise ids: {dups}"

    def test_starter_bank_exists_and_spans_both_languages(self):
        exercises, _, _ = _load()
        ccs = [e for e in exercises if isinstance(e, CodeCompletion)]
        # Story 4.6 targets a real starter bank (~10-15+); we have 3 seed + batch-02.
        assert len(ccs) >= 10, f"expected a real code-completion bank, got {len(ccs)}"
        langs = {e.language for e in ccs}
        assert {"sql", "pyspark"} <= langs, f"bank should span SQL + PySpark, got {langs}"

    def test_every_code_completion_satisfies_model_invariants(self):
        exercises, _, _ = _load()
        valid_domains = {d.value for d in Domain}
        for e in (x for x in exercises if isinstance(x, CodeCompletion)):
            assert e.template.count("___") == 1, f"{e.id}: needs exactly one ___ blank"
            assert e.answer.strip(), f"{e.id}: empty answer"
            # The answer must tokenize to a real token, not pure punctuation —
            # otherwise the green/yellow/grey feedback is meaningless/unsolvable.
            assert re.search(r"\w", e.answer), f"{e.id}: answer has no word token: {e.answer!r}"
            assert e.language in VALID_LANGUAGES, f"{e.id}: bad language {e.language!r}"
            assert isinstance(e.accepted, list), f"{e.id}: accepted must be a list"
            # Every accepted alternative must be a non-empty string.
            for alt in e.accepted:
                assert isinstance(alt, str) and alt.strip(), (
                    f"{e.id}: accepted has an empty/non-string entry: {alt!r}"
                )
            assert e.domain.value in valid_domains, f"{e.id}: bad domain {e.domain!r}"

    def test_at_least_one_accepted_alternative_exercises_fr16(self):
        # FR-16: a learner typing a valid alternative phrasing isn't penalized.
        exercises, _, _ = _load()
        ccs = [e for e in exercises if isinstance(e, CodeCompletion)]
        with_alts = [e for e in ccs if len(e.accepted) > 1]
        assert with_alts, "expected at least one item with >1 accepted alternative (FR-16)"
