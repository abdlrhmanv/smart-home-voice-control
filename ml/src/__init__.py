"""Smart Home ML — Clean Architecture package."""

from .application import (
    COMMAND_TASK,
    SPEAKER_TASK,
    ClassificationEvaluator,
    ClassifierTrainer,
    SmartHomePipeline,
)
from .domain import (
    COMMAND_LABELS,
    DEFAULT_PASSWORD,
    SPEAKER_LABELS,
    InferenceResult,
    ProjectPaths,
)

__version__ = "0.3.0"

__all__ = [
    "COMMAND_LABELS",
    "COMMAND_TASK",
    "DEFAULT_PASSWORD",
    "SPEAKER_LABELS",
    "SPEAKER_TASK",
    "ClassificationEvaluator",
    "ClassifierTrainer",
    "InferenceResult",
    "ProjectPaths",
    "SmartHomePipeline",
    "__version__",
]
