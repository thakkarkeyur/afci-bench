"""The terminal sentence must describe the run that actually happened.

`run_v2.main` printed one hard-coded line on every successful run:

    => dry run complete; no model was invoked and nothing was scored

It printed it after a successful ``--real-run`` too, so a run in which a model
process really was started and a paid turn really was spent announced on the
terminal that no model was invoked. The run record was correct throughout; only
the sentence lied. That is the dangerous shape of the defect, because the
terminal is what an operator reads and repeats: the evidence would have been
described to a reviewer exactly backwards.

These tests pin the sentence to the RECORDED observation (``invocation.invoked``
and ``outcome.scored``) rather than to the requested mode, so the report cannot
drift from the artifact again.
"""
import run_v2


def _result(*, invoked, scored=False, record=True):
    """A RunResult carrying only the fields the terminal line reads."""
    machine = run_v2.StateMachine()
    payload = None
    if record:
        payload = {
            "invocation": {"invoked": invoked},
            "outcome": {"scored": scored},
        }
    return run_v2.RunResult(machine=machine, record=payload)


# --------------------------------------------------------------------------- #
# The defect itself
# --------------------------------------------------------------------------- #
def test_real_run_that_invoked_a_model_does_not_say_dry_run():
    """The regression. A real invocation must never be called a dry run."""
    line = run_v2.completion_line(_result(invoked=True), "real")
    assert "dry run" not in line
    assert "no model was invoked" not in line


def test_real_run_that_invoked_a_model_says_so():
    line = run_v2.completion_line(_result(invoked=True), "real")
    assert "real run complete" in line
    assert "a model process was invoked" in line


def test_dry_run_keeps_its_accurate_sentence():
    line = run_v2.completion_line(_result(invoked=False), "dry-run")
    assert line == "dry run complete; no model was invoked and nothing was scored"


# --------------------------------------------------------------------------- #
# The sentence follows the record, not the requested mode
# --------------------------------------------------------------------------- #
def test_real_mode_without_an_invocation_is_not_reported_as_one():
    """Mode alone never promotes a run to "a model ran"."""
    line = run_v2.completion_line(_result(invoked=False), "real")
    assert "NO model process was started" in line
    assert "a model process was invoked" not in line


def test_scoring_clause_follows_the_record():
    assert "nothing was scored" in run_v2.completion_line(
        _result(invoked=True, scored=False), "real"
    )
    assert "something was scored" in run_v2.completion_line(
        _result(invoked=True, scored=True), "real"
    )


def test_a_missing_record_never_claims_an_invocation():
    """Fail closed: no record is not evidence that a model ran."""
    for mode in ("dry-run", "real"):
        line = run_v2.completion_line(_result(invoked=True, record=False), mode)
        assert "a model process was invoked" not in line


# --------------------------------------------------------------------------- #
# The source no longer carries an unconditional dry-run sentence
# --------------------------------------------------------------------------- #
def test_main_has_no_hardcoded_dry_run_completion_line():
    source = run_v2.__file__
    with open(source, "r", encoding="utf-8") as fh:
        text = fh.read()
    # The only remaining occurrences are inside completion_line() and this
    # module's docstring reference -- never as a print in main().
    assert 'print("  => dry run complete' not in text
