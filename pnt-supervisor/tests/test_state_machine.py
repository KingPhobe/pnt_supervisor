from types import SimpleNamespace

from pnt_supervisor.core.enums import NavState
from pnt_supervisor.fusion.state_machine import SupervisorStateMachine


def _machine() -> SupervisorStateMachine:
    cfg = SimpleNamespace(
        fusion=SimpleNamespace(
            warmup_s=2.0,
            good_threshold=0.85,
            degrade_threshold=0.65,
            invalid_threshold=0.30,
            recovering_threshold=0.60,
            good_entry_dwell_s=2.0,
            recover_entry_dwell_s=2.0,
            hard_fail_hold_s=1.0,
        )
    )
    return SupervisorStateMachine(cfg)


def test_sustained_healthy_reaches_good_after_warmup() -> None:
    sm = _machine()
    for t in [0.0, 1.0, 2.0, 3.0, 4.0]:
        snap = sm.update(t_sec=t, nav_score=0.95, hard_fail_active=False)

    assert snap.state == NavState.GOOD
    assert snap.last_transition_reason == "warmup_complete_and_stable"


def test_hard_fail_sends_invalid_immediately() -> None:
    sm = _machine()
    sm.update(t_sec=0.0, nav_score=0.95, hard_fail_active=False)
    snap = sm.update(t_sec=1.0, nav_score=0.95, hard_fail_active=True)

    assert snap.state == NavState.INVALID
    assert snap.last_transition_reason == "hard_fail_active"


def test_clearing_hard_fail_enters_recovering_not_good() -> None:
    sm = _machine()
    sm.update(t_sec=0.0, nav_score=0.95, hard_fail_active=True)

    sm.update(t_sec=0.5, nav_score=0.95, hard_fail_active=False)
    snap = sm.update(t_sec=1.6, nav_score=0.95, hard_fail_active=False)

    assert snap.state == NavState.RECOVERING


def test_stable_after_recovery_returns_to_good() -> None:
    sm = _machine()
    sm.update(t_sec=0.0, nav_score=0.95, hard_fail_active=True)
    sm.update(t_sec=0.5, nav_score=0.95, hard_fail_active=False)
    sm.update(t_sec=1.6, nav_score=0.95, hard_fail_active=False)

    sm.update(t_sec=2.0, nav_score=0.95, hard_fail_active=False)
    snap = sm.update(t_sec=4.1, nav_score=0.95, hard_fail_active=False)

    assert snap.state == NavState.GOOD
    assert snap.last_transition_reason == "recovery_complete"


def test_chattering_inputs_do_not_rapidly_oscillate_due_to_dwell() -> None:
    sm = _machine()
    sm.update(t_sec=0.0, nav_score=0.95, hard_fail_active=False)
    sm.update(t_sec=1.0, nav_score=0.95, hard_fail_active=False)
    sm.update(t_sec=2.0, nav_score=0.90, hard_fail_active=False)
    sm.update(t_sec=2.5, nav_score=0.60, hard_fail_active=False)
    sm.update(t_sec=3.0, nav_score=0.90, hard_fail_active=False)
    sm.update(t_sec=3.5, nav_score=0.60, hard_fail_active=False)
    snap = sm.update(t_sec=4.0, nav_score=0.90, hard_fail_active=False)

    # Never reached sustained dwell for GOOD entry.
    assert snap.state == NavState.UNKNOWN
