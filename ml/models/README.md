# Saved models

| File | Task |
| ---- | ---- |
| `speaker.pkl` | speaker recognition |
| `command.pkl` | command recognition |

These files are committed so Streamlit can load them after `git pull`.

```python
# from Project2/ml (or repo root/ml)
from src.application import SmartHomePipeline

pipe = SmartHomePipeline.create_default()
# loads ml/models/speaker.pkl and ml/models/command.pkl automatically
```

Retrain locally if needed:

```bash
python train_speaker.py --tune
python train_command.py --tune
```
