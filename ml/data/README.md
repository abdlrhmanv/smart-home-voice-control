# Dataset

```
dataset/<speaker>/<command>/*.wav
```

Speakers must match `src/domain/labels.py` (`ahmed`, `abdullah`, `Abdlrhman`).  
Commands: `light_on`, `light_off`, `music_on`, `music_off`.

**Target:** ≥25 WAV files per command per speaker (100 total / person).

| Speaker   | Status |
|-----------|--------|
| ahmed     | 100 clips |
| Abdlrhman | 100 clips |
| abdullah  | 80 clips (20 per command) |

Use `python inventory.py` for live counts. Record with `python recorder_app.py`.
