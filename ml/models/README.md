# Model artifacts

| File | Task | Algorithm |
|------|------|-----------|
| `speaker.pkl` | Speaker ID | `StandardScaler` + RBF SVM |
| `command.pkl` | Command class | `StandardScaler` + RBF SVM |

Serialized with **joblib** as a sklearn `Pipeline`. Retrain:

```bash
python train_speaker.py --tune
python train_command.py --tune
```

Do not commit large experimental checkpoints; keep only the evaluation-passing pair used by the app.
