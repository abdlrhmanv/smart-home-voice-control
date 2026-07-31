# Project 2 — Smart Home (Level 1)

Voice-controlled smart home with a Clean Architecture ML package.

## Architecture

```
ml/src/
├── domain/            # labels, dataclasses, paths
├── ports/             # Classifier, FeatureExtractor, ArtifactStore, …
├── application/       # SmartHomePipeline, ClassifierTrainer, Evaluator
├── infrastructure/    # librosa, sklearn, whisper, filesystem, persistence
├── actions/           # Arduino / UI action mapping
└── config.py          # AudioConfig, TrainingConfig, InferenceConfig

ml/recorder/           # isolated Tkinter app (no src imports)
```

**Key rules**

- Pipeline depends on ports only (never sklearn)
- Trainer fits; Evaluator scores (SRP)
- `ArtifactStore.save(task, model)` — task owns `speaker.pkl` / `command.pkl`
- `ModelLoader` reconstructs classifiers for the pipeline
- `AudioPreprocessor` → `FeatureExtractor` (MFCC)

## Public API

```python
from src.application import SmartHomePipeline

pipe = SmartHomePipeline.create_default()
gate = pipe.verify_password("password.wav")
result = pipe.predict_voice_command("command.wav")
```

## Train

```bash
cd Project2/ml
python train_speaker.py --tune
python train_command.py --tune
python inventory.py
```

## Recorder

```bash
python recorder_app.py
```

## Dataset

| Speaker | Notes |
| ------- | ----- |
| ahmed | 100 clips |
| Abdlrhman | 100 clips |
| abdullah | partial (light_on/off) |

## Team repository

Canonical team repo: https://github.com/abdlrhmanv/smart-home-voice-control
