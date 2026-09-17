#!/usr/bin/env python3
"""``SL-V2-EFF-RESET-01`` — the PILOT-SCOPED turn budget, and nothing wider.

What this freezes
-----------------
Three numbers, for the ``AFCI_EFFICIENCY_PILOT`` run purpose only:

===========================  =====  ====================================
``PRE_RESET_MAX_TURNS``         32  phase A of a ``RESET`` run
``POST_RESET_MAX_TURNS``        32  phase B of a ``RESET`` run
``NON_RESET_MAX_TURNS``         64  the single process of a ``NON_RESET`` run
===========================  =====  ====================================

``32 + 32 == 64``, so a reset run and a non-reset run of the same cell receive
the SAME total allowance. That equality is the whole point: if a reset run had
more room, any "robustness" difference could be a budget artifact rather than a
context-mechanism one (``RESET_PROTOCOL.md`` §3).

What this does NOT do
---------------------
It does **not** resolve ``TD-B01`` (the pre-reset allowance) or ``TD-B11`` (the
total budget), and it does not pass ``G2``. Those decide the allowances of the
CONFIRMATORY study, across every task, condition and model, and they stay OPEN
and unchanged. These three numbers are chosen so one non-confirmatory pilot can
execute at all; they are bounded to that purpose, they expire with it, and they
create no precedent for the confirmatory reset protocol. A later reader who
finds them must not read a resolved decision out of an executed pilot.

Why turns, and why these turns
------------------------------
The allowance is expressed in **agentic turns** because that is the only ceiling
Claude Code 2.1.229 enforces deterministically in headless mode, and it enforces
it by construction rather than by observation. The runtime's own agent loop
(``--max-turns N``, ``--print`` only) runs turn ``1..N``, checks
``turn_just_completed > N`` *after* the turn's tools have executed and their
results have been collected, and returns before issuing request ``N+1``. So the
ceiling is exactly N model requests, the tool effects of turn N are already on
disk when it fires, and the run ends with a terminal ``result`` event whose
``subtype`` is ``error_max_turns``. Nothing about it is probabilistic and
nothing about it depends on the model's cooperation.

The VALUES are a judgement, and are recorded as one. 32 is large enough that a
phase-A run reaches the checkpoint predicate — one ``npm run ci:agent`` after at
least one edit — with room to spare in every shape of run the PT08/PT09/PT10
diagnostics actually produced, and small enough that a run which never reaches
it terminates rather than burning a budget on a loop. No efficiency observation
informed the choice, because none exists.

Unused allowance never transfers
--------------------------------
``POST_RESET_MAX_TURNS`` is 32 whatever phase A consumed. A phase A that stops
at turn 3 does not hand 29 turns to phase B, and a phase A that exhausts all 32
does not shrink it. The allowance is frozen; consumption is observational
(``RESET_PROTOCOL.md`` §3).

No model is invoked by this module.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional, Tuple

import run_governance as gov

#: The authority. Recorded, not assumed: every value below is re-derived from
#: the record named here and a drift between the two is a refusal.
SL_V2_EFF_RESET_01 = "SL-V2-EFF-RESET-01"

#: The record carrying the frozen budget table, repository-relative.
RESET_BUDGET_RECORD = "docs/v2/AFCI_EFFICIENCY_PILOT_RESET_BUDGET_DECISION.md"

#: The section the budget table lives in.
RESET_BUDGET_HEADING = "### 4.1 The frozen turn-budget table"

#: The ONE run purpose these values are scoped to. A budget request for any
#: other purpose is refused rather than defaulted.
RESET_BUDGET_PURPOSE = "AFCI_EFFICIENCY_PILOT"

PRE_RESET_MAX_TURNS = 32
POST_RESET_MAX_TURNS = 32
NON_RESET_MAX_TURNS = 64

#: The two reset states. There is no third, and no "partial" or "recovered" one:
#: a reset either happened exactly as the protocol describes or the observation
#: is refused.
NON_RESET = "NON_RESET"
RESET = "RESET"
RESET_STATES: Tuple[str, str] = (NON_RESET, RESET)

#: The two phases of a RESET run, in order.
PHASE_A = "A"
PHASE_B = "B"
PHASES: Tuple[str, str] = (PHASE_A, PHASE_B)

#: What the record must say, as data. A relaxation in the record is then a
#: mechanical failure rather than a wording nobody re-read.
RESET_BUDGET_PINS: Tuple[Tuple[str, object], ...] = (
    ("decision_id", SL_V2_EFF_RESET_01),
    ("run_purpose", RESET_BUDGET_PURPOSE),
    ("scope", "AFCI_EFFICIENCY_PILOT ONLY"),
    ("pre_reset_max_turns", PRE_RESET_MAX_TURNS),
    ("post_reset_max_turns", POST_RESET_MAX_TURNS),
    ("non_reset_max_turns", NON_RESET_MAX_TURNS),
    ("total_allowance_reset", NON_RESET_MAX_TURNS),
    ("total_allowance_non_reset", NON_RESET_MAX_TURNS),
    ("allowances_identical_across_conditions", True),
    ("unused_pre_reset_transfers", False),
    ("post_reset_depends_on_phase_a_consumption", False),
    ("td_b01_resolved_globally", False),
    ("td_b11_resolved_globally", False),
    ("g2_passed", False),
    ("confirmatory_precedent_created", False),
    ("decided_before_any_efficiency_observation", True),
)


#: ``SL-V2-LOWER-MODEL-01`` — the lower-capability-model pilot's allowance.
#:
#: It is a SECOND authority rather than an extension of the first, because the
#: two pilots freeze genuinely different things: that one authorises both arms
#: and splits 32/32 against 64; this one authorises ``NON_RESET`` ONLY and
#: freezes the single number 64. Folding them together would have meant either
#: teaching the efficiency pilot's record about a reset arm it does not run, or
#: letting a lower-model row draw a reset allowance nothing froze for it.
#:
#: The NUMBER is deliberately identical. A cheaper model is not given a smaller
#: ceiling: needing more turns to reach the same place is the phenomenon under
#: study, and capping it lower would turn that phenomenon into a truncation.
LOWER_MODEL_BUDGET_PURPOSE = "AFCI_LOWER_MODEL_PILOT"
SL_V2_LOWER_MODEL_01 = "SL-V2-LOWER-MODEL-01"
LOWER_MODEL_BUDGET_RECORD = "docs/v2/AFCI_LOWER_MODEL_PILOT_DECISION.md"
LOWER_MODEL_BUDGET_HEADING = "### 8.1 The frozen turn-budget table"

LOWER_MODEL_BUDGET_PINS: Tuple[Tuple[str, object], ...] = (
    ("decision_id", SL_V2_LOWER_MODEL_01),
    ("run_purpose", LOWER_MODEL_BUDGET_PURPOSE),
    ("scope", "AFCI_LOWER_MODEL_PILOT ONLY"),
    ("reset_states_authorised", NON_RESET),
    ("reset_arm_authorised", False),
    ("non_reset_max_turns", NON_RESET_MAX_TURNS),
    ("total_allowance_non_reset", NON_RESET_MAX_TURNS),
    # Stated as absent rather than as a number. A record that carried 32/32 here
    # would be freezing an allowance for an arm this purpose cannot run.
    ("pre_reset_max_turns", "not applicable"),
    ("post_reset_max_turns", "not applicable"),
    ("allowances_identical_across_conditions", True),
    ("budget_lowered_because_the_model_is_cheaper", False),
    ("td_b01_resolved_globally", False),
    ("td_b11_resolved_globally", False),
    ("g2_passed", False),
    ("confirmatory_precedent_created", False),
    ("decided_before_any_lower_model_observation", True),
)


@dataclass(frozen=True)
class BudgetAuthority:
    """One Study-Lead decision's frozen allowance, and the arms it covers.

    Carried as data so a second pilot cannot acquire the first's allowance by
    resembling it. A purpose absent from :data:`BUDGET_AUTHORITIES` has no
    frozen budget at all and is refused — which is the state every purpose but
    these two is in, and must stay in.
    """

    run_purpose: str
    decision_id: str
    record: str
    heading: str
    reset_states: Tuple[str, ...]
    pins: Tuple[Tuple[str, object], ...]
    non_reset_max_turns: int
    pre_reset_max_turns: Optional[int] = None
    post_reset_max_turns: Optional[int] = None

    @property
    def splits_a_reset(self) -> bool:
        return RESET in self.reset_states

    def record_path(self, repo: Path) -> Path:
        return Path(repo) / self.record


BUDGET_AUTHORITIES: Dict[str, BudgetAuthority] = {
    RESET_BUDGET_PURPOSE: BudgetAuthority(
        run_purpose=RESET_BUDGET_PURPOSE,
        decision_id=SL_V2_EFF_RESET_01,
        record=RESET_BUDGET_RECORD,
        heading=RESET_BUDGET_HEADING,
        reset_states=RESET_STATES,
        pins=RESET_BUDGET_PINS,
        non_reset_max_turns=NON_RESET_MAX_TURNS,
        pre_reset_max_turns=PRE_RESET_MAX_TURNS,
        post_reset_max_turns=POST_RESET_MAX_TURNS,
    ),
    LOWER_MODEL_BUDGET_PURPOSE: BudgetAuthority(
        run_purpose=LOWER_MODEL_BUDGET_PURPOSE,
        decision_id=SL_V2_LOWER_MODEL_01,
        record=LOWER_MODEL_BUDGET_RECORD,
        heading=LOWER_MODEL_BUDGET_HEADING,
        reset_states=(NON_RESET,),
        pins=LOWER_MODEL_BUDGET_PINS,
        non_reset_max_turns=NON_RESET_MAX_TURNS,
    ),
}


def budget_authority(run_purpose: str) -> BudgetAuthority:
    """The frozen allowance authority for one purpose, or a refusal."""
    authority = BUDGET_AUTHORITIES.get(run_purpose)
    if authority is None:
        raise gov.RunnerRefusal(
            gov.RESET_NOT_AUTHORISED_FOR_PURPOSE,
            f"no Study-Lead decision freezes a turn budget for {run_purpose!r}; "
            f"the purposes that carry one are {sorted(BUDGET_AUTHORITIES)} and "
            "the runner never invents an allowance",
        )
    return authority


class ResetBudgetError(gov.RunnerRefusal):
    """A budget that cannot be re-derived is not a frozen budget."""


@dataclass(frozen=True)
class TurnBudget:
    """The allowance ONE process of one run receives.

    ``phase`` is ``None`` for a non-reset run, which has no phases — it is one
    process, not a phase-A that happens to be alone.
    """

    run_purpose: str
    reset_state: str
    phase: Optional[str]
    max_turns: int
    total_allowance: int
    authority: str = SL_V2_EFF_RESET_01

    def to_dict(self) -> Dict[str, object]:
        return {
            "authority": self.authority,
            "run_purpose": self.run_purpose,
            "reset_state": self.reset_state,
            "phase": self.phase,
            "max_turns": self.max_turns,
            "total_allowance": self.total_allowance,
        }


def assert_reset_state(reset_state: str) -> str:
    if reset_state not in RESET_STATES:
        raise gov.RunnerRefusal(
            gov.RESET_STATE_INVALID,
            f"{reset_state!r} is not a governed reset state; the only two are "
            f"{list(RESET_STATES)} and neither is defaulted",
        )
    return reset_state


def governed_budget_table(
    repo: Path = gov.REPO,
    record: Optional[Path] = None,
    heading: Optional[str] = None,
    *,
    run_purpose: str = RESET_BUDGET_PURPOSE,
) -> Dict[str, object]:
    """Re-derive one purpose's frozen budget table from its own record.

    ``run_purpose`` defaults to the efficiency pilot, so every call site that
    predates a second authority reads exactly the table it always read.
    """
    authority = budget_authority(run_purpose)
    path = Path(record) if record else authority.record_path(repo)
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise gov.RunnerRefusal(
            gov.GOVERNANCE_RECORD_UNREADABLE, f"cannot read {path}: {exc}"
        ) from exc
    return gov._table_values(
        gov._section(text, heading if heading is not None else authority.heading)
    )


def budget_problems(
    repo: Path = gov.REPO,
    record: Optional[Path] = None,
    heading: Optional[str] = None,
    *,
    run_purpose: str = RESET_BUDGET_PURPOSE,
) -> list:
    """Every reason the frozen budget cannot be re-derived. Empty means frozen."""
    authority = budget_authority(run_purpose)
    section = heading if heading is not None else authority.heading
    governed = governed_budget_table(
        repo, record, section, run_purpose=run_purpose
    )
    if not governed:
        return [(
            gov.RESET_BUDGET_NOT_FROZEN,
            f"{authority.decision_id}'s budget table ({section!r} in "
            f"{authority.record}) is absent or unparseable; a frozen budget "
            "is never assumed",
        )]
    problems = []
    for key, expected in authority.pins:
        if governed.get(key) != expected:
            problems.append((
                gov.RESET_BUDGET_NOT_FROZEN,
                f"the record's {key} is {governed.get(key)!r}, not {expected!r}",
            ))
    # The arithmetic the protocol depends on, checked against the record rather
    # than against the constants: a record whose own numbers do not add up has
    # not frozen an equal-total split however plausible each number looks.
    #
    # Only for an authority that actually SPLITS a reset. A NON_RESET-only
    # authority has no split to check, and its record states the two reset
    # allowances as absent rather than as numbers, which the pins already
    # require — so there is nothing here that a missing check could let through.
    pre = governed.get("pre_reset_max_turns")
    post = governed.get("post_reset_max_turns")
    non = governed.get("non_reset_max_turns")
    if authority.splits_a_reset and (
        isinstance(pre, int)
        and isinstance(post, int)
        and isinstance(non, int)
        and pre + post != non
    ):
        problems.append((
            gov.RESET_BUDGET_NOT_FROZEN,
            f"the record splits {pre} + {post} = {pre + post} against a non-reset "
            f"allowance of {non}; a reset must never receive a different total "
            "from a non-reset run of the same cell (RESET_PROTOCOL.md section 3)",
        ))
    return problems


def turn_budget(
    *,
    run_purpose: str,
    reset_state: str,
    phase: Optional[str] = None,
    repo: Path = gov.REPO,
    record: Optional[Path] = None,
) -> TurnBudget:
    """The frozen allowance for one process, or a refusal.

    Fails closed on every axis: an unauthorised purpose, an unknown reset state,
    a missing phase for a reset run, a phase supplied for a non-reset run, and a
    record whose table does not re-derive are all refusals rather than defaults.
    """
    authority = budget_authority(run_purpose)
    assert_reset_state(reset_state)
    if reset_state not in authority.reset_states:
        raise gov.RunnerRefusal(
            gov.RESET_NOT_AUTHORISED_FOR_PURPOSE,
            f"{authority.decision_id} authorises "
            f"{list(authority.reset_states)} for {run_purpose}; {reset_state!r} "
            "has no frozen allowance under it and the runner never invents one",
        )

    problems = budget_problems(repo, record, run_purpose=run_purpose)
    if problems:
        code, detail = problems[0]
        raise gov.RunnerRefusal(
            code,
            detail
            + (
                f" (and {len(problems) - 1} further problem(s))"
                if len(problems) > 1
                else ""
            ),
        )

    if reset_state == NON_RESET:
        if phase is not None:
            raise gov.RunnerRefusal(
                gov.RESET_STATE_INVALID,
                "a NON_RESET run has no phases; it is one process, and asking "
                f"for phase {phase!r} of it describes a run that does not exist",
            )
        return TurnBudget(
            run_purpose=run_purpose,
            reset_state=NON_RESET,
            phase=None,
            max_turns=authority.non_reset_max_turns,
            total_allowance=authority.non_reset_max_turns,
            authority=authority.decision_id,
        )

    if phase not in PHASES:
        raise gov.RunnerRefusal(
            gov.RESET_STATE_INVALID,
            f"a RESET run has exactly two phases {list(PHASES)}; got {phase!r}",
        )
    return TurnBudget(
        run_purpose=run_purpose,
        reset_state=RESET,
        phase=phase,
        max_turns=(
            authority.pre_reset_max_turns
            if phase == PHASE_A
            else authority.post_reset_max_turns
        ),
        total_allowance=(
            authority.pre_reset_max_turns + authority.post_reset_max_turns
        ),
        authority=authority.decision_id,
    )


def budget_block(
    *, run_purpose: str, reset_state: str, repo: Path = gov.REPO,
    record: Optional[Path] = None,
) -> Dict[str, object]:
    """The record's view of a run's allowances, for the run record.

    Both reset allowances are reported for a reset run even before phase B
    exists, because the post-reset allowance is frozen IN ADVANCE and reporting
    it only once phase B had started would make it look derived from phase A.
    """
    authority = budget_authority(run_purpose)
    assert_reset_state(reset_state)
    if reset_state == NON_RESET:
        budget = turn_budget(
            run_purpose=run_purpose, reset_state=NON_RESET, repo=repo, record=record
        )
        return {
            "authority": authority.decision_id,
            "reset_state": NON_RESET,
            "max_turns": budget.max_turns,
            "total_allowance": budget.total_allowance,
            "single_process": True,
            "pre_reset_turn_limit": None,
            "post_reset_turn_limit": None,
            "unused_pre_reset_transfers": False,
        }
    a = turn_budget(
        run_purpose=run_purpose, reset_state=RESET, phase=PHASE_A,
        repo=repo, record=record,
    )
    b = turn_budget(
        run_purpose=run_purpose, reset_state=RESET, phase=PHASE_B,
        repo=repo, record=record,
    )
    return {
        "authority": authority.decision_id,
        "reset_state": RESET,
        "max_turns": None,
        "total_allowance": a.total_allowance,
        "single_process": False,
        "pre_reset_turn_limit": a.max_turns,
        "post_reset_turn_limit": b.max_turns,
        "unused_pre_reset_transfers": False,
    }


def max_turns_flag(budget: TurnBudget) -> Tuple[str, ...]:
    """The launch tokens that impose this allowance.

    Kebab-case, verified against the installed runtime rather than assumed:
    Claude Code 2.1.229 registers ``--max-turns <turns>`` and documents it as
    "Maximum number of agentic turns in non-interactive mode ... (only works
    with --print)". Every launch this harness builds carries ``-p``.
    """
    return ("--max-turns", str(budget.max_turns))
