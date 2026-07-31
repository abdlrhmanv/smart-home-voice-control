# Voice Dataset Recorder

Tkinter app for capturing the Smart Home command dataset.

```
UI (RecorderApp)
  → RecordingSession
  → RecordingDatasetRepository + AudioCaptureService / QualityGate / WavWriter
```

No imports from `src` (ML package) — recorder stays isolated.

```bash
cd Project2/ml
python recorder_app.py
python -m recorder --speaker abdullah
```
