#!/usr/bin/env python3
"""Run reference-audio transcription without importing an optional CUDA torch build."""

from __future__ import annotations

import importlib.abc
import runpy
import sys
from pathlib import Path


class _BlockTorchImport(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname: str, path=None, target=None):
        if fullname == "torch" or fullname.startswith("torch."):
            raise ImportError("torch is intentionally disabled for CPU transcription")
        return None


sys.meta_path.insert(0, _BlockTorchImport())
runpy.run_path(
    str(Path(__file__).with_name("transcribe_reference_audio.py")),
    run_name="__main__",
)
