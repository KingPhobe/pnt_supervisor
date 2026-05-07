"""High-level supervisor pipeline API."""

from dataclasses import dataclass

from pnt_supervisor.core.models import EpochObservation, FeatureVector, SupervisorDecision
from pnt_supervisor.features.pipeline import FeaturePipeline

from .decision_engine import DecisionEngine


@dataclass(slots=True)
class SupervisorStepResult:
    observation: EpochObservation
    features: FeatureVector
    decision: SupervisorDecision


class SupervisorPipeline:
    def __init__(
        self,
        feature_pipeline: FeaturePipeline | None = None,
        decision_engine: DecisionEngine | None = None,
    ) -> None:
        self.feature_pipeline = feature_pipeline or FeaturePipeline.default()
        self.decision_engine = decision_engine or DecisionEngine()

    def step(self, obs: EpochObservation) -> SupervisorStepResult:
        features = self.feature_pipeline.extract(obs)
        decision = self.decision_engine.decide(features)
        return SupervisorStepResult(
            observation=obs,
            features=features,
            decision=decision,
        )
