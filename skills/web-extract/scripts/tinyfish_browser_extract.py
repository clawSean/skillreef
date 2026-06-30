#!/usr/bin/env python3
"""Compatibility wrapper for the moved web-use TinyFish helper."""

from __future__ import annotations

import runpy
from pathlib import Path


TARGET = Path(__file__).resolve().parents[2] / "web-use" / "scripts" / "tinyfish_browser_extract.py"
runpy.run_path(str(TARGET), run_name="__main__")
