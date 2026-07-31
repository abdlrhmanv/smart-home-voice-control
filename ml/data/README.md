# Dataset layout

Team voice recordings only:

```
dataset/
├── ahmed/{light_on,light_off,music_on,music_off}/
├── abdullah/…
└── Abdlrhman/…
```

Target: **25+ clips** per command per person.

Naming (Tkinter recorder):

```
light_on_001.wav …
```

```bash
cd Project2/ml
python recorder_app.py
python inventory.py
```
