"""Features describing recovery after invalid states."""

from __future__ import annotations

from collections import deque

from pnt_supervisor.core import EpochObservation, FeatureFlag, FeatureValue, FeatureVector

from .base import FeatureExtractor


class RecoveryFeatureExtractor(FeatureExtractor):
    def __init__(self, *, unstable_window_s: float = 5.0, flap_window: int = 20) -> None:
        super().__init__(window_size=max(flap_window, 20))
        self.unstable_window_s = unstable_window_s
        self.last_invalid_t: float | None = None
        self.state_history: deque[bool] = deque(maxlen=flap_window)

    def extract(self, obs: EpochObservation, out: FeatureVector) -> FeatureVector:
        out = self._prepare_output(obs, out)
        if not obs.fix_valid:
            self.last_invalid_t = obs.t_sec

        if self.last_invalid_t is None:
            time_since_last_invalid = float("inf")
            reacq_unstable = False
        else:
            time_since_last_invalid = max(0.0, obs.t_sec - self.last_invalid_t)
            reacq_unstable = obs.fix_valid and time_since_last_invalid <= self.unstable_window_s

        self.state_history.append(obs.fix_valid)
        state_flap_count = 0
        if len(self.state_history) > 1:
            prev = self.state_history[0]
            for current in list(self.state_history)[1:]:
                if current != prev:
                    state_flap_count += 1
                prev = current

        out.values.update(
            {
                FeatureValue.TIME_SINCE_LAST_INVALID: time_since_last_invalid,
                FeatureValue.STATE_FLAP_COUNT: float(state_flap_count),
            }
        )
        out.flags[FeatureFlag.REACQ_UNSTABLE] = reacq_unstable

        self.context.append(obs)
        return out
