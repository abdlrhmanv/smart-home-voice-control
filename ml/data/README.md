# Dataset

```
dataset/<speaker>/<command>/*.wav
dataset/<speaker>/<command>/<condition>/*.wav   # optional multi-condition
```

Speakers must match `src/domain/labels.py` (`ahmed`, `abdullah`, `Abdlrhman`).  
Commands: `light_on`, `light_off`, `music_on`, `music_off`.  
Conditions: `close`, `distance`, `noise`, `rate` (optional third folder level).

**Target:** ≥25 WAV files per command per speaker (100 total / person).

| Speaker   | Status |
|-----------|--------|
| ahmed     | 100 clips |
| Abdlrhman | 100 clips |
| abdullah  | 80 clips (20 per command) |

```bash
python inventory.py
python validate_dataset.py --min-per-pair 20 --min-conditions 1
python scaffold_conditions.py          # create condition folders
```

## Multi-condition recording (improves LOSO)

1. `python scaffold_conditions.py`
2. Edit `ml/recorder/config.py`:
   - `SPEAKER_NAME = "..."`
   - `RECORDING_CONDITION = "close"` then `"distance"` / `"noise"` / `"rate"`
3. `python recorder_app.py` for each condition
4. Retrain:

```bash
python train_command.py --augment
python eval_loso.py
python validate_dataset.py --min-conditions 2
```

Flat legacy folders (no condition subdir) still load and count as `close`.
