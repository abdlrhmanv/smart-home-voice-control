# Model artifacts

| File | Task | Algorithm | Features |
|------|------|-----------|----------|
| `speaker.pkl` | Speaker ID | Scaler + RBF SVM + CalibratedClassifierCV | 122-D (no CMVN) |
| `command.pkl` | Command class | Scaler + RBF SVM + CalibratedClassifierCV | 282-D + CMVN (train may include `--augment`) |

Serialized with **joblib**. Retrain:

```bash
python train_speaker.py
python train_command.py --augment
python eval_loso.py
python eval_nested_cv.py --task command --no-tune
```

Use `--no-calibrate` only for ablation. Do not commit large experimental checkpoints.
