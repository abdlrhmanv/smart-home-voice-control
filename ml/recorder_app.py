#!/usr/bin/env python3
"""Launcher for the voice dataset recorder (Abdlrhman by default)."""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure Project2/ml is on sys.path when launched as a script
sys.path.insert(0, str(Path(__file__).resolve().parent))

from recorder.app import main

if __name__ == "__main__":
    main()
