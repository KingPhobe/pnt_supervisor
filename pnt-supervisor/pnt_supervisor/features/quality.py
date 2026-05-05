"""Fix quality and geometry features."""

from __future__ import annotations

from collections import deque

from pnt_supervisor.core.feature_keys import FeatureFlag, FeatureValue
from pnt_supervisor.core.models import EpochObservation, FeatureVector

from .base import FeatureExtractor


class QualityFeatureExtractor(FeatureExtractor):
    def __init__(
        self,
        *,
        hdop_bad_threshold: float = 6.0,
        sats_min_threshold: int = 4,
        transition_window: int = 10,
    ) -> None:
        super().__init__(window_size=max(transition_window, 10))
        self.hdop_bad_threshold = hdop_bad_threshold
        self.sats_min_threshold = sats_min_threshold
        self.fix_history: deque[bool] = deque(maxlen=transition_window)

    def extract(self, obs: EpochObservation, out: FeatureVector) -> FeatureVector:
        out = self._prepare_output(obs, out)
        fix_valid_numeric = 1.0 if obs.fix_valid else 0.0
        self.fix_history.append(obs.fix_valid)

        transition_count = 0
        if len(self.fix_history) > 1:
            prior = self.fix_history[0]
            for curr in list(self.fix_history)[1:]:
                if curr != prior:
                    transition_count += 1
                prior = curr

        hdop_bad = obs.hdop >= self.hdop_bad_threshold
        geometry_bad = hdop_bad or obs.num_sats < self.sats_min_threshold

        out.values.update(
            {
                FeatureValue.FIX_VALID_NUMERIC: fix_valid_numeric,
                FeatureValue.NUM_SATS: float(obs.num_sats),
                FeatureValue.HDOP: float(obs.hdop),
                FeatureValue.FIX_TRANSITION_COUNT_SHORT_WINDOW: float(transition_count),
            }
        )
        out.flags.update(
            {
                FeatureFlag.HDOP_BAD: hdop_bad,
                FeatureFlag.GEOMETRY_BAD: geometry_bad,
            }
        )

        self.context.append(obs)
        return out
