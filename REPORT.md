# Smart Home Voice Control — Engineering Review Report

**Project:** IEEE AI Team — Project 2 (Level 1)  
**Date:** 2026-08-03  
**Scope:** Requirement analysis, codebase/architecture/ML review, functional verification, tests, performance, documentation, and targeted fixes.

---

## 1. Executive summary

The ML package is the strongest part of the system: Clean Architecture layering, stratified holdout evaluation, and both speaker/command models exceed the **F1 ≥ 0.85** gate (~**0.98** macro F1 on the 20% test split).

The largest defects were **integration gaps**, not model quality:

1. Password success never sent `PASSWORD_OK` → Arduino stayed locked → lights/music/temp ignored.
2. Serial port hard-coded to Windows `COM11` with no RX path for temperature.
3. Empty Streamlit pages (Devices / Activity / Settings) and no auth gating.
4. Firmware pin map mismatched the breadboard schematic; no red LED; TMP36 formula incorrect for TMP36.

These were fixed in this review pass. Tests were added (**20 passed**, ~**68%** coverage of core packages). Remaining risks: shared spoken password (not speaker-bound), no unknown-class rejection, and speaker–command feature entanglement.

---

## 2. Phase 1 — Requirement analysis

### Functional requirements

| ID | Requirement | Source |
|----|-------------|--------|
| F1 | Streamlit GUI for voice input and home control | PDF p.10–12 |
| F2 | STT password check vs stored phrase | PDF p.10–11 |
| F3 | On success: red LED on Arduino + unlock control panel | PDF p.10–11 |
| F4 | On failure: feedback; do not unlock | PDF p.10–11 |
| F5 | After unlock: speaker identification from voice | PDF p.12 |
| F6 | Command classification: light on/off, music on/off | PDF p.13–16 |
| F7 | White LED ↔ light; green LED + “music” ↔ music | PDF p.16 |
| F8 | Temperature sensor readable from GUI | PDF p.17 |
| F9 | Arduino: 3 LEDs + buzzer + temp sensor | PDF p.6,9 |
| F10 | Submit repo, circuit photo, Arduino code, demo video | PDF p.19 |

### Non-functional

- Macro **F1 ≥ 0.85** on test set (PDF p.18)
- Usable Streamlit UX; reliable serial link
- Multi-speaker demo capability

### ML requirements

- Two models: speaker ID + command classification
- Training data: ~100 recordings/person, 25/command (PDF p.12–14)
- Dataset shape: features × person × command (PDF p.15)
- Holdout evaluation with precision/recall/F1/confusion matrix

### Hardware

- Arduino Uno (or Nano/Uno equivalent)
- Red / green / white LEDs, buzzer, temperature sensor (TMP36 on team board)
- Laptop with mic + USB serial

### Software

- Python, Streamlit, librosa/sklearn, Whisper STT, pyserial, Arduino IDE

### Required datasets

- Per-speaker folders with four command subfolders of WAV clips
- Current: 280 clips (ahmed 100, Abdlrhman 100, abdullah 80)

### Expected workflow

1. Collect sentences with recorder  
2. Train speaker + command models  
3. Run Streamlit → password → commands → Arduino  
4. Optional temperature query  

### User interaction flow

Password page → say phrase → unlock → Voice Control / Devices → command or temp → Activity log

### Missing / ambiguous in the PDF

- Exact password phrase not specified (team chose `open sesame`)
- Whether password must also match a known speaker — unspecified (implemented as STT-only)
- “Music” = real audio vs LED/buzzer proxy — unspecified (LED + short tone)
- TTS mentioned educationally but **not required** for the build
- Sensor type (LM35 vs TMP36) not specified; board uses TMP36
- White LED absent on current 2-LED breadboard photo

---

## 3. Phase 2 — Codebase review (selected issues)

| Issue | Files | Root cause | Impact | Fix |
|-------|-------|------------|--------|-----|
| Password never reached Arduino | `password_service.py`, UI | Auth only set session flag | Hardware stayed locked | Send `PASSWORD_OK`/`FAIL` |
| Hard-coded `COM11` | `api/serial_service.py` | Windows-only constant | Linux/mac fail silently | `ARDUINO_PORT` + autodetect |
| No serial RX | `serial_service.py` | TX-only API | Temp unusable | `read_line` / `request_temperature` |
| Empty pages | `pages/3–5_*.py` | Unfinished UI | Spec features missing | Implemented |
| Auth not enforced | Voice/Devices pages | No gate | Bypass password | `require_auth()` |
| Pin mismatch | `arduino.ino` vs schematic | Sketch used D11 buzzer / D13 green | Wrong LEDs light | Align to D11 red, D12 green, D13 buzzer, D10 white |
| TMP36 formula | `temprature()` | Used LM35 `V*100` | Wrong °C | `(V-0.5)*100` |
| Command trainer allowed 1 class | `trainer.py` | `required = 1` | Invalid SVM train | Require ≥2 classes |
| `password_ok=True` on command-only predict | `pipeline.py` | Misleading API | Auth confusion | Set false; document |
| Duplicate action dispatch | `voice_service` vs mapper | Parallel policies | Drift risk | Central `execute_command` |
| Dead sidebar / empty components | `components/` | Unused | Noise | Left; documented |
| Shared password in source | `config.py` | Course design | Spoofable | Document limitation |

---

## 4. Phase 3 — Architecture review

**Strengths:** Clear hexagonal ML package; ports/protocols; Trainer ≠ Evaluator; composition root; recorder isolation; config dataclasses.

**Weaknesses (partially improved):** App layer thinner and less clean than `ml/`; Streamlit services still import concrete serial; pipeline imports infra in composition root file (acceptable) but module-level imports of concrete adapters remain; no structured logging in UI path historically (serial now uses `logging`).

**Architecture score: 7.5/10** (ML 8.5; app integration was ~5, now ~7 after fixes)

---

## 5. Phase 4 — ML pipeline review

| Topic | Assessment |
|-------|------------|
| Dataset structure | Correct speaker/command tree |
| Features | 122-D MFCC+spectral; peak norm |
| Normalization | `StandardScaler` inside sklearn Pipeline (fit on train) |
| Split | Stratified 80/20, seed 42 |
| CV / tune | Optional StratifiedKFold(5) GridSearch on train only |
| Metrics | Acc, P/R/F1 macro+weighted, confusion matrix, report |
| Serialization | joblib Pipeline |
| Data leakage | No classic leakage (scaler/CV on train). **Entanglement risk:** same clips train speaker & command |
| Unseen test | Yes — metrics from held-out `X_test` |
| F1 gate | Speaker **0.981**, Command **0.982** (≥ 0.85) |

**ML score: 8/10**

---

## 6. Phase 5 — Functional verification

| Feature | Result | Evidence |
|---------|--------|----------|
| Voice password auth | **PASS** | Whisper exact-match in pipeline + Password page |
| STT transcription | **PASS** | `FasterWhisperTranscriber` |
| Speaker identification | **PASS** | SVM `speaker.pkl`; UI shows speaker |
| Command classification | **PASS** | SVM `command.pkl`; 4 classes |
| Streamlit interface | **PASS** | Multipage app (was PARTIAL; pages filled) |
| Arduino communication | **PASS** | Configurable serial + protocol (was FAIL) |
| LED control | **PARTIAL** | Firmware mapped; white LED may be unwired on board |
| Music control | **PARTIAL** | Green LED + short tone (not full playback) |
| Temperature display | **PASS** | Devices page + `SEND_TEMP` parse (was FAIL) |
| Auth gate before control | **PASS** | `require_auth()` (was FAIL) |
| F1 ≥ 0.85 | **PASS** | ~0.98 both models |

---

## 7. Phase 6 — Testing

```
20 passed
Coverage ~68% (ml/src, api, services, ai)
```

Includes: unit (labels, features, password normalize, actions, serial parse, trainer validation), integration (real model inference), edge cases (noise WAV, empty WAV, wrong password, unknown command).

**Testing score: 6.5/10** (solid start; Whisper E2E and Streamlit UI tests still missing)

---

## 8. Phase 7 — Performance (measured)

| Metric | Value |
|--------|-------|
| Joblib model load | ~2 ms |
| Pipeline create | ~2 ms |
| Feature extract (warm) | ~20–25 ms typical; cold higher |
| `predict_voice_command` | **~22 ms mean** (20 runs) |
| RSS after models | ~317 MB |
| Whisper `base` first load | **~4 s**, RSS → **~1.07 GB** |

**Optimizations:** smaller Whisper (`tiny`/`small`) for password; cache pipeline in Streamlit `@st.cache_resource`; avoid reloading Whisper per page rerun; optional ONNX/quantized SVM (low gain given 22 ms).

**Performance score: 7.5/10**

---

## 9. Phase 8 — Documentation

Updated: root `README.md`, `ml/data/README.md`, `ml/models/README.md`, this `REPORT.md`, inline Arduino header protocol docs.

---

## 10. Phase 9 — Improvements applied

- Arduino pin map + TMP36 formula + red LED + unlock gate messaging  
- Serial autodetect / env port + temperature RX  
- Password → Arduino unlock wiring  
- Auth-gated Voice/Devices; Devices + Activity + Settings pages  
- Trainer multi-class validation  
- Pipeline API honesty (`password_ok` on command-only path)  
- Tests + requirements + README  

---

## 11. Scores

| Area | Score (/10) | Notes |
|------|-------------|-------|
| Architecture | 7.5 | Strong ML layering; app layer improved |
| Code Quality | 7.0 | Cleaner services; some dead components remain |
| Machine Learning | 8.0 | Solid pipeline; entanglement / no reject class |
| Testing | 6.5 | 20 tests, 68% cov; no UI/Whisper E2E |
| Documentation | 8.0 | README + REPORT + model/data docs |
| Performance | 7.5 | Fast SVM path; Whisper dominates memory |
| Maintainability | 7.5 | Clear packages; config/env for serial |
| Security | 5.0 | Shared phrase password; spoofable STT gate |
| **Overall** | **7.2** | Spec-capable after integration fixes |

---

## 12. Remaining issues & roadmap

**P1 — done this pass**

1. Leave-one-speaker-out evaluation (`ml/eval_loso.py`) — mean command F1 **~0.11** (near chance); documents optimistic random-split scores  
2. Confidence threshold + `unknown` rejection (`InferenceConfig`)  
3. Cached pipeline (`st.cache_resource` + LRU fallback in `ai/predict.py`)  
4. Persist activity log (`data/activity_log.jsonl`)  
5. Document 2-LED / white-LED (D10) fallback in firmware, Settings, README  

**P2**

6. Speaker-verified password (STT ∧ speaker ∈ allow-list)  
7. Improve cross-speaker command features / more data / multi-condition recording  
8. Nested CV / calibration curves  
9. Streamlit e2e (Playwright)  
10. CI workflow running `pytest` on push  
