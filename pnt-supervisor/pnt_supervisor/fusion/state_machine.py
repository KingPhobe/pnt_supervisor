"""Supervisor decision state machine with dwell and recovery logic."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from pnt_supervisor.core.enums import NavState


@dataclass(slots=True)
class StateSnapshot:
    """State-machine status at the latest processed epoch."""

    state: NavState
    time_in_state_s: float
    last_transition_reason: str


class SupervisorStateMachine:
    """Manage stable nav state transitions from fused trust evidence."""

    def __init__(self, config: Any | None = None) -> None:
        fusion_cfg = getattr(config, "fusion", config)
        self.warmup_s = self._read(fusion_cfg, "warmup_s", 3.0)
        self.good_threshold = self._read(fusion_cfg, "good_threshold", 0.85)
        self.degrade_threshold = self._read(fusion_cfg, "degrade_threshold", 0.65)
        self.invalid_threshold = self._read(fusion_cfg, "invalid_threshold", 0.35)
        self.recovering_threshold = self._read(fusion_cfg, "recovering_threshold", 0.6)
        self.good_entry_dwell_s = self._read(fusion_cfg, "good_entry_dwell_s", 2.0)
        self.recover_entry_dwell_s = self._read(fusion_cfg, "recover_entry_dwell_s", 3.0)
        self.hard_fail_hold_s = self._read(fusion_cfg, "hard_fail_hold_s", 3.0)

        self.current_state = NavState.UNKNOWN
        self._state_entered_t_sec = 0.0
        self._last_t_sec = 0.0
        self.last_transition_reason = "initial_state"

        self._good_candidate_since: float | None = None
        self._recover_candidate_since: float | None = None
        self._hard_fail_cleared_since: float | None = None

    @staticmethod
    def _read(config: Any, key: str, default: float) -> float:
        if config is None:
            return default
        if hasattr(config, key):
            return float(getattr(config, key))
        return default

    def _transition(self, new_state: NavState, t_sec: float, reason: str) -> None:
        if self.current_state == new_state:
            return
        self.current_state = new_state
        self._state_entered_t_sec = t_sec
        self.last_transition_reason = reason

    def _start_or_keep_timer(self, timer_value: float | None, t_sec: float) -> float:
        return t_sec if timer_value is None else timer_value

    def update(self, t_sec: float, nav_score: float, hard_fail_active: bool) -> StateSnapshot:
        """Advance state machine by one epoch and return current state snapshot."""

        self._last_t_sec = t_sec
        nav_score = min(1.0, max(0.0, nav_score))

        if hard_fail_active:
            self._good_candidate_since = None
            self._recover_candidate_since = None
            self._hard_fail_cleared_since = None
            self._transition(NavState.INVALID, t_sec, "hard_fail_active")
            return self.snapshot()

        severe_drop = nav_score < self.invalid_threshold
        if severe_drop and self.current_state in {NavState.GOOD, NavState.DEGRADED, NavState.RECOVERING}:
            self._good_candidate_since = None
            self._recover_candidate_since = None
            self._hard_fail_cleared_since = None
            self._transition(NavState.INVALID, t_sec, "severe_score_drop")
            return self.snapshot()

        if self.current_state == NavState.INVALID:
            self._hard_fail_cleared_since = self._start_or_keep_timer(self._hard_fail_cleared_since, t_sec)
            clear_elapsed = t_sec - self._hard_fail_cleared_since
            if clear_elapsed >= self.hard_fail_hold_s and nav_score >= self.recovering_threshold:
                self._transition(NavState.RECOVERING, t_sec, "hard_fail_cleared_stable")
                self._recover_candidate_since = None
            return self.snapshot()

        if self.current_state == NavState.UNKNOWN:
            if t_sec >= self.warmup_s and nav_score >= self.good_threshold:
                self._good_candidate_since = self._start_or_keep_timer(self._good_candidate_since, t_sec)
                if (t_sec - self._good_candidate_since) >= self.good_entry_dwell_s:
                    self._transition(NavState.GOOD, t_sec, "warmup_complete_and_stable")
            else:
                self._good_candidate_since = None
            return self.snapshot()

        if self.current_state == NavState.GOOD:
            if nav_score < self.degrade_threshold:
                self._transition(NavState.DEGRADED, t_sec, "below_degrade_threshold")
                self._good_candidate_since = None
            return self.snapshot()

        if self.current_state == NavState.DEGRADED:
            if nav_score >= self.good_threshold:
                self._good_candidate_since = self._start_or_keep_timer(self._good_candidate_since, t_sec)
                if (t_sec - self._good_candidate_since) >= self.good_entry_dwell_s:
                    self._transition(NavState.GOOD, t_sec, "degraded_recovered_stable")
            else:
                self._good_candidate_since = None
            return self.snapshot()

        if self.current_state == NavState.RECOVERING:
            if nav_score < self.recovering_threshold:
                self._transition(NavState.DEGRADED, t_sec, "recovery_not_stable")
                self._recover_candidate_since = None
                return self.snapshot()

            if nav_score >= self.good_threshold:
                self._recover_candidate_since = self._start_or_keep_timer(self._recover_candidate_since, t_sec)
                if (t_sec - self._recover_candidate_since) >= self.recover_entry_dwell_s:
                    self._transition(NavState.GOOD, t_sec, "recovery_complete")
            else:
                self._recover_candidate_since = None
            return self.snapshot()

        return self.snapshot()

    def snapshot(self) -> StateSnapshot:
        return StateSnapshot(
            state=self.current_state,
            time_in_state_s=max(0.0, self._last_t_sec - self._state_entered_t_sec),
            last_transition_reason=self.last_transition_reason,
        )
