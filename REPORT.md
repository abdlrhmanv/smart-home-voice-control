# Smart Home Voice Control — Engineering Review Report

**Project:** IEEE AI Team — Project 2 (Level 1)  
**Date:** 2026-08-04  
**Spec:** `Project 2.pdf`  
**Scope:** Requirement analysis, codebase/architecture/ML review, functional verification, tests, performance, documentation, and defect fixes.

Evidence sources: PDF text extraction, source inspection, `pytest` (56 passed / 4 skipped UI), inventory (280 WAVs), LOSO (~0.11 command F1), nested CV (~0.95 random-split F1), latency/memory microbenchmarks.

---

## 1. Executive summary

The system is **spec-capable for a same-speaker course demo**: Whisper password gate, dual SVMs, Streamlit multipage UI, Arduino protocol, temperature RX, and laptop music playback are wired end-to-end.

The ML package is the strongest subsystem (ports + composition root, stratified holdout, calibrated RBF SVM). The weakest scientific claim is treating **~0.98 random-split macro F1** as generalization — leave-one-speaker-out command F1 is **~0.11** (near chance).

This pass fixed concrete defects:

| Defect | Fix |
|--------|-----|
| `run_full()` dropped `password_ok=True` | Preserve gate fields after command predict |
| Low speaker confidence left executable `action` | Clear `action` whenever rejected |
| Device UI updated before serial success | Update session state only on send OK / offline mode |
| Stale temperature shown as fresh read | `get_temperature()` returns `None` on failure |
| Serial guessed `ports[0]` | Fail closed unless Arduino-like or `ARDUINO_PORT` |
| Spec music-on-laptop missing | `services/music_player.py` looping synth |
| Upload overwrite / no validation | Unique paths + RIFF/size checks |
| Nested CV inner folds used class count | Use min per-class count |

**Overall score: 7.7 / 10**

---

## 2. Phase 1 — Requirement analysis

### Functional requirements

| ID | Requirement | Spec source |
|----|-------------|-------------|
| F1 | Streamlit GUI for voice input and home control | PDF (Streamlit control panel) |
| F2 | STT password vs stored phrase | PDF (password page) |
| F3 | On success: red LED + unlock control panel | PDF |
| F4 | On failure: Streamlit error; no unlock | PDF |
| F5 | After unlock: identify who is speaking + show name/photo | PDF |
| F6 | Command classification: light/music on/off | PDF |
| F7 | White LED ↔ light; green LED + laptop music ↔ music | PDF |
| F8 | Temperature readable from GUI via Arduino | PDF |
| F9 | Hardware: 3 LEDs + buzzer + temp sensor + Arduino | PDF |
| F10 | Deliverables: GitHub, Arduino code, circuit photo, English demo video, Markdown | PDF |
| F11 | Macro F1 ≥ 0.85 on test set | PDF |

### Non-functional

- Usable Streamlit UX; reliable USB serial
- Multi-speaker demo capability
- Training data from team voices only (no synthetic AI voices)

### ML requirements

- Two models: speaker ID + command classification
- ~100 clips/person, 25/command (or 120)
- Feature × person × command dataset shape
- Holdout evaluation with P/R/F1 + confusion matrix

### Hardware

- Arduino Uno/Nano, red/green/white LEDs, buzzer, temperature sensor (team board: TMP36), laptop + mic + USB

### Software

- Python, Streamlit, librosa/sklearn, Whisper STT, pyserial, Arduino IDE

### Required datasets

```
ml/data/dataset/<speaker>/{light_on,light_off,music_on,music_off}/*.wav
```

Current inventory: **280** clips — ahmed 100, Abdlrhman 100, abdullah 80; condition=`close` only; 33 low-RMS clips flagged.

### Expected workflow

1. Record team utterances → 2. Train speaker + command → 3. Streamlit password → commands → Arduino → 4. Optional temperature

### User interaction flow

Password (say phrase) → unlock (red LED) → Voice Control / Devices → command or temp → Activity log

### Missing / ambiguous in the PDF

- Exact password phrase (team chose `open sesame`)
- Whether password must also match enrolled speaker (implemented as STT ∧ speaker)
- Sensor type LM35 vs TMP36 (board uses TMP36)
- TTS educational only — **not required** for the build
- White LED may be unwired on 2-LED breadboards

---

## 3. Phase 2 — Codebase review (issues)

| Issue | File(s) | Root cause | Impact | Status |
|-------|---------|------------|--------|--------|
| `run_full` lost password success | `ml/src/application/pipeline.py` | Returned command result as-is | Misleading API | **Fixed** |
| Rejected speaker kept action | `pipeline.py` | Only command gate cleared action | Could actuate when rejected | **Fixed** |
| Optimistic device state | `services/device_service.py` | State before serial ack | UI/hardware desync | **Fixed** |
| Stale temperature as success | `device_service.py` | Returned cache on failure | False readings | **Fixed** |
| Serial `ports[0]` fallback | `api/serial_service.py` | Convenience guess | Wrong device risk | **Fixed** |
| Shared `temp/input.wav` | `audio/recorder.py` | Fixed path | Cross-session overwrite | **Fixed** |
| Unvalidated uploads | `utils/uploads.py` | Trust client | Crash/abuse | **Fixed** |
| No laptop music | app layer | Arduino-only proxy | Spec F7 incomplete | **Fixed** |
| Nested CV fold guard wrong | `ml/eval_nested_cv.py` | Used `#classes` | Fragile CV | **Fixed** |
| Calibration on trained artifact | `ml/report_calibration.py` | Random “holdout” after full train | Misleading cal curves | Open |
| Command train/test share speakers | `trainer.py` | Utterance stratified split | Inflated F1 | Documented; LOSO exists |
| Dead `components/sidebar.py` | components | Unused stale links | Noise | Open (low) |
| Auth only in UI pages | `pages/*` | No service-level check | Bypass if API reused | Open (low) |
| Closed-set “unknown” | pipeline thresholds | No open-set verifier | Spoof risk | Accepted for course |

---

## 4. Phase 3 — Architecture review

**Strengths**

- Hexagonal ML package: domain / ports / application / infrastructure
- `SmartHomePipeline.create_default()` composition root
- Task objects (`SPEAKER_TASK` / `COMMAND_TASK`) centralize labels + artifacts
- Recorder isolated under `ml/recorder/`
- App services separate password / voice / device concerns (partially)

**Weaknesses**

- App layer mixes Streamlit session state with use-cases (`device_service`)
- Module-global serial singleton
- Application trainers still import concrete adapters directly
- Duplicate command→action mapping (ML mapper vs `execute_command`)

**Architecture score: 8.5 / 10** (after `core/` + `adapters/` split; pages → façades → use-cases → ports)

---

## 5. Phase 4 — Machine Learning review

| Topic | Assessment |
|-------|------------|
| Dataset structure | Correct speaker/command tree; conditions scaffolded but unused |
| Features | Speaker 122-D; command 282-D (MFCC+Δ/ΔΔ + spectral) |
| Preprocess | 16 kHz mono, peak norm |
| Normalization | `StandardScaler` in sklearn Pipeline (fit train); command CMVN on summary vector |
| Split | Stratified 80/20 seed 42 — **not speaker-grouped** |
| CV / tune | Optional GridSearch on train; nested CV script; LOSO script |
| Metrics | Acc, P/R/F1 macro+weighted, confusion matrix |
| Serialization | joblib `CalibratedClassifierCV(Pipeline(Scaler, RBF SVC))` |
| Classic leakage | Scaler/CV on train only — OK |
| Entanglement | Same clips train speaker & command; command random-split F1 optimistic |
| Unseen test (random) | Yes — held-out utterances |
| Unseen speaker | LOSO command F1 **~0.11** |
| F1 gate (random) | Speaker/command ~**0.98** ≥ 0.85 |

**ML pipeline score: 7.8 / 10** (methodology honesty reduced by random-split optimism)

---

## 6. Phase 5 — Functional verification

| Feature | Result | Evidence |
|---------|--------|----------|
| Voice password auth | **PASS** | Whisper normalize + phrase match + enrolled speaker gate |
| STT transcription | **PASS** | `FasterWhisperTranscriber` |
| Speaker identification | **PASS** | `speaker.pkl` + UI metrics |
| Speaker photo | **PARTIAL** | Placeholder avatars in `assets/speakers/`; replace with real photos |
| Command classification | **PASS** | `command.pkl`, 4 classes + reject |
| Streamlit interface | **PASS** | Multipage app + auth gate |
| Arduino communication | **PASS** | Configurable serial + protocol (needs hardware to confirm live) |
| LED control | **PARTIAL** | Firmware mapped; white LED may be unwired |
| Music control | **PASS** | Green LED + laptop loop (`music_player`) |
| Temperature display | **PASS** | Devices page + `SEND_TEMP` (fresh-read semantics fixed) |
| Auth gate before control | **PASS** | `require_auth()` on Voice/Devices/Activity |
| F1 ≥ 0.85 (random holdout) | **PASS** | ~0.98 both models |
| Cross-speaker robustness | **FAIL** | LOSO command F1 ~0.11 |

---

## 7. Phase 6 — Testing

```
56 passed, 4 skipped (Playwright UI unless RUN_UI_E2E=1)
Coverage ~71% (ml/src, api, services, ai, utils, audio)
```

Includes unit (labels, features, password normalize, actions, serial, uploads, trainer validation, confidence reject, device service), integration (real model inference on fixtures/dataset), service e2e with mocked mic/serial, edge cases (noise, silence, wrong password, unknown/rejected command).

Gaps: real Whisper password E2E, live Arduino, stateful UI flows.

**Testing score: 7.2 / 10**

---

## 8. Phase 7 — Performance (measured 2026-08-04)

| Metric | Value |
|--------|-------|
| Joblib model load | ~1.5–2.1 ms / artifact |
| `create_default()` (models, no Whisper warm) | ~4 ms |
| Feature extract (warm) | ~9 ms mean |
| `predict_voice_command` (20 runs) | **~28 ms** mean (p95 ~28.5 ms) |
| RSS after SVM models | ~175 MB |
| Whisper `tiny` first call | ~27 s (cold/HF download in this run) |
| Whisper second call | ~0.35 s |
| RSS after Whisper | ~917 MB |

**Optimizations:** keep `WHISPER_SIZE=tiny` for demos; cache pipeline (`st.cache_resource` already used in `ai/predict.py`); avoid reloading Whisper per rerun; collect multi-condition data before chasing exotic models.

**Performance score: 7.6 / 10**

---

## 9. Phase 8 — Documentation

Updated: `README.md`, `REPORT.md`, `assets/speakers/README.md`, `.env.example`, Arduino header protocol docs (pre-existing), ML data/models READMEs (pre-existing).

---

## 10. Phase 9 — Improvements applied (this pass)

1. Pipeline reject clears action; `run_full` preserves password success  
2. Device/serial sync + offline mode flag  
3. Fresh temperature semantics  
4. Serial fail-closed autodetection  
5. Laptop music player  
6. Upload validation + unique temp recordings  
7. Speaker avatar placeholders + Voice UI hook  
8. Nested CV fold guard fix  
9. Regression tests (`test_device_service`, confidence/run_full, serial resolve, uploads)

---

## 11. Scores

| Area | Score (/10) | Notes |
|------|-------------|-------|
| Architecture | 8.5 | `core/` use-cases + `adapters/`; Streamlit out of business logic |
| Code Quality | 7.6 | Dead stubs removed; sidebar fixed |
| Machine Learning | 8.0 | Honest calibration + group-holdout option |
| Testing | 7.5 | ~73% cov, auth/serial/group tests; Whisper E2E optional |
| Documentation | 8.2 | README + REPORT + env + avatars |
| Performance | 7.6 | Fast SVM path; Whisper dominates RAM/startup |
| Maintainability | 8.0 | Bridge injection + env config |
| Security | 7.2 | Service-level auth; speaker-bound password |
| **Overall** | **7.9** | Spec demo-ready; cross-speaker needs data |

---

## 12. Remaining issues & roadmap

**Done in fix pass (2026-08-04)**

- Calibration report trains fresh on train split only (`report_calibration.py`)  
- `SerialBridge` injectable via `set_bridge()` / `device_service.set_serial_bridge()`  
- Service-level auth (`services/auth.py`) on voice + device actuation  
- `--group-holdout` on command trainer (speaker-disjoint test)  
- CI `--cov-fail-under=65`; Whisper normalize unit tests (+ optional `RUN_WHISPER_E2E=1`)  
- Dead empty modules removed; sidebar links fixed  

**P0 — submission polish (needs humans / hardware)**

1. Replace avatar placeholders with real team photos  
2. Record English ~2 min LinkedIn demo (multi-speaker)  
3. Upload circuit photo; confirm white LED wiring or document 2-LED fallback  
4. Re-record low-RMS `abdullah` clips (`filter_quiet_clips.py --move`)

**P1 — still open**

5. Collect `distance` / `noise` / `rate` conditions; retrain; re-run `eval_loso.py`  
6. Optional: open-set speaker verification (embedding + threshold)  
7. Prefer LOSO / `--group-holdout` numbers in any public claims (tooling ready)

---

## Scorecard table

| Area | Score (/10) | Notes |
|------|-------------|-------|
| Architecture | 8.0 | Injectable serial + service auth |
| Code Quality | 7.6 | Dead stubs removed |
| Machine Learning | 8.0 | Honest calibration + group-holdout |
| Testing | 7.5 | ~73% cov; optional Whisper E2E |
| Documentation | 8.2 | Spec-aligned README + this report |
| Performance | 7.6 | ~28 ms command path; Whisper ~0.9 GB |
| Maintainability | 8.0 | Bridge injection + env config |
| Overall | 7.9 | Course-demo ready; data work left for cross-speaker |
